#!/usr/bin/env python3
"""
nao_sensors.py — Publishes NAO / Pepper sensor data as ROS2 topics.

Connects to the robot via the qi SDK (same library as nao_bridge.py) and reads:
  - Touch sensors     (chest button, 3 head zones, 2 foot bumpers)
  - Sonar distances   (left and right ultrasonic sensors)
  - Battery level
  - Sound detection   (is there a sound above the threshold?)
  - Sound localization (horizontal/vertical angle of the dominant sound source)

WHY polling instead of NAOqi event callbacks?
  ALMemory.subscribeToEvent() requires registering a Python object as a *qi
  module* on the robot's message bus. That works only when the Python process is
  itself launched as a NAOqi application, which conflicts with running inside a
  normal ROS2 node process. Polling via ALMemory.getData() on a ROS timer is
  simpler, fully compatible, and at 20 Hz gives ≤ 50 ms latency — fast enough
  for any button or touch interaction.

Topics published (all relative to the node namespace set by the launch file):
  sensor/chest              std_msgs/Bool    — 1 when pressed, 0 when released
  sensor/head_front         std_msgs/Bool
  sensor/head_middle        std_msgs/Bool
  sensor/head_rear          std_msgs/Bool
  sensor/bumper_left        std_msgs/Bool    — left foot bumper
  sensor/bumper_right       std_msgs/Bool    — right foot bumper
  battery                   std_msgs/Float32 — 0.0 (empty) to 1.0 (full)
  sonar/left                std_msgs/Float32 — distance in metres, 0 = no echo
  sonar/right               std_msgs/Float32
  audio/sound_detected      std_msgs/Bool    — True while a sound is being detected
  audio/localization/azimuth    std_msgs/Float32 — horizontal angle (rad), 0 = front
  audio/localization/elevation  std_msgs/Float32 — vertical angle (rad), 0 = horizontal
  audio/localization/confidence std_msgs/Float32 — 0.0 (no confidence) to 1.0

Parameters (all optional):
  naoqi_host          string  "192.168.1.100"  — robot IP (same as nao_bridge.py)
  naoqi_port          int     9559
  poll_hz             float   20.0             — sensor poll frequency
  sound_sensitivity   float   0.5              — ALSoundDetection sensitivity (0.0–1.0)
"""
import rclpy
from ros2_robot_bridge.base_sensor import SensorBase
from std_msgs.msg import Bool, Float32

try:
    import qi
    _HAS_QI = True
except ImportError:
    _HAS_QI = False


# ── ALMemory key paths ─────────────────────────────────────────────────────────
#
# ALMemory is NAOqi's global key-value store. The robot's DCM updates every
# sensor here at 10 ms intervals. We batch-fetch with getListData() to
# minimize network round-trips over Wi-Fi.

BUTTON_KEYS_NAO = {
    "chest":        "Device/SubDeviceList/ChestBoard/Button/Sensor/Value",
    "head_front":   "Device/SubDeviceList/Head/Touch/Front/Sensor/Value",
    "head_middle":  "Device/SubDeviceList/Head/Touch/Middle/Sensor/Value",
    "head_rear":    "Device/SubDeviceList/Head/Touch/Rear/Sensor/Value",
    "bumper_left":  "Device/SubDeviceList/LFoot/Bumper/Left/Sensor/Value",
    "bumper_right": "Device/SubDeviceList/RFoot/Bumper/Right/Sensor/Value",
}

# Pepper has base bumpers (3 × wheel-guard contacts) rather than foot bumpers.
# Keys verified on NAOqi 2.5 / Pepper 1.8.
BUTTON_KEYS_PEPPER = {
    "chest":          "Device/SubDeviceList/ChestBoard/Button/Sensor/Value",
    "head_front":     "Device/SubDeviceList/Head/Touch/Front/Sensor/Value",
    "head_middle":    "Device/SubDeviceList/Head/Touch/Middle/Sensor/Value",
    "head_rear":      "Device/SubDeviceList/Head/Touch/Rear/Sensor/Value",
    "bumper_left":    "Device/SubDeviceList/Platform/FrontLeft/Bumper/Sensor/Value",
    "bumper_right":   "Device/SubDeviceList/Platform/FrontRight/Bumper/Sensor/Value",
    "bumper_back":    "Device/SubDeviceList/Platform/Back/Bumper/Sensor/Value",
}

BUTTON_KEYS = BUTTON_KEYS_NAO  # overridden at connect time on Pepper

SONAR_KEYS = {
    "left":  "Device/SubDeviceList/US/Left/Sensor/Value",   # metres
    "right": "Device/SubDeviceList/US/Right/Sensor/Value",  # metres
}

BATTERY_KEY = "Device/SubDeviceList/Battery/Charge/Sensor/Value"  # 0.0–1.0

# ── Audio ALMemory keys ────────────────────────────────────────────────────────
#
# ALSoundDetection writes to SoundDetected when it detects audio energy above
# its sensitivity threshold. The value is a list when sound is present and
# None (or empty) when silence is detected.
#
# ALSoundLocalization writes to ALSoundLocalization/AnyDirection after each
# analysis frame. The structure is:
#   [timestamp_s, timestamp_us,
#    [azimuth_rad, elevation_rad, confidence, energy_lf, energy_rf, energy_lb, energy_rb]]
# azimuth  0 = directly in front, positive = left (robot frame)
# elevation 0 = horizontal, positive = above

SOUND_DETECTED_KEY  = "SoundDetected"
# Confirmed key name for NAOqi 2.1.x (discovered via getDataList at startup).
# Older docs say "AnyDirection"; the robot actually writes to "SoundLocated".
SOUND_LOCATION_KEY  = "ALSoundLocalization/SoundLocated"


class NaoSensors(SensorBase):
    """Polls NAO / Pepper sensors and publishes them as ROS2 topics."""

    def __init__(self):
        super().__init__("nao_sensors")

        # ── Parameters ──────────────────────────────────────────────────────
        self.declare_parameter("robot_type",        "nao")
        self.declare_parameter("naoqi_host",        "192.168.1.100")
        self.declare_parameter("naoqi_port",        9559)
        # poll_hz: 20 Hz → 50 ms worst-case latency. The robot's DCM runs at
        # 100 Hz so there is no benefit going above that.
        self.declare_parameter("poll_hz",           20.0)
        # sound_sensitivity: 0.0 = almost nothing triggers detection,
        # 1.0 = very sensitive. 0.5 is a reasonable default for a quiet room.
        self.declare_parameter("sound_sensitivity", 0.5)

        # ── Publishers ──────────────────────────────────────────────────────
        # depth=1: only the latest reading matters; stale sensor values are useless.
        qos = 1

        # Button/bumper publishers are created after connect() so we know the
        # robot model (NAO uses foot keys; Pepper uses platform/base keys).
        self._btn_pubs   = {}
        self._btn_keys   = BUTTON_KEYS_NAO   # updated on Pepper after connect

        self._sonar_pubs = {
            side: self.create_publisher(Float32, f"sonar/{side}", qos)
            for side in SONAR_KEYS
        }
        self._battery_pub       = self.create_publisher(Float32, "battery",                       qos)
        self._sound_det_pub     = self.create_publisher(Bool,    "audio/sound_detected",          qos)
        self._sound_az_pub      = self.create_publisher(Float32, "audio/localization/azimuth",    qos)
        self._sound_el_pub      = self.create_publisher(Float32, "audio/localization/elevation",  qos)
        self._sound_conf_pub    = self.create_publisher(Float32, "audio/localization/confidence", qos)

        # ── Internal state ───────────────────────────────────────────────────
        self._session             = None
        self._memory              = None   # ALMemory — sensor key-value store
        self._sonar               = None   # ALSonar  — ultrasonic emitter control
        self._sound_detection     = None   # ALSoundDetection  — sound presence
        self._sound_localization  = None   # ALSoundLocalization — sound direction
        # Timestamp of the last SoundDetected event we processed.
        # ALMemory never clears SoundDetected — we detect new sounds by
        # comparing the event timestamp to what we saw in the previous poll.
        self._last_sound_ts       = None
        # Set to True once, to log the raw localization structure for diagnostics.
        self._loc_logged          = False

        self.get_logger().info("[Sensors] Node started — connecting to robot ...")
        self._start_connect()

    # ── Connection ───────────────────────────────────────────────────────────

    def connect(self):
        """Open a qi session and acquire service proxies. Runs in a background thread."""
        if not _HAS_QI:
            self.get_logger().error("[Sensors] qi SDK not installed — node inactive.")
            return

        host = self.get_parameter("naoqi_host").value
        port = self.get_parameter("naoqi_port").value

        try:
            self._session = qi.Session()
            self._session.connect(f"tcp://{host}:{port}")
        except Exception as exc:
            self.get_logger().error(f"[Sensors] Connection to {host}:{port} failed — {exc}")
            return

        # ALMemory: the central sensor/actuator key-value store.
        self._memory = self._session.service("ALMemory")

        # ── Robot type detection ─────────────────────────────────────────────
        # Primary: use the robot_type launch parameter (passed from the launch file).
        # Fallback: query ALSystem.robotName() in case the node is started standalone.
        robot_type_param = self.get_parameter("robot_type").value.lower()
        is_pepper = "pepper" in robot_type_param
        if not is_pepper:
            try:
                al_system = self._session.service("ALSystem")
                is_pepper = "pepper" in al_system.robotName().lower()
            except Exception:
                pass

        if is_pepper:
            self._btn_keys = BUTTON_KEYS_PEPPER
            self.get_logger().info("[Sensors] Pepper detected — using platform bumper keys.")
        else:
            self._btn_keys = BUTTON_KEYS_NAO
            self.get_logger().info("[Sensors] NAO detected — using foot bumper keys.")

        # Create button/bumper publishers now that we know which keys to use.
        qos = 1
        self._btn_pubs = {
            name: self.create_publisher(Bool, f"sensor/{name}", qos)
            for name in self._btn_keys
        }

        # ALSonar: the ultrasonic emitter is OFF by default.
        # subscribe() activates it and registers us as a consumer.
        self._sonar = self._session.service("ALSonar")
        self._sonar.subscribe("ros2_sensors")

        # ── Audio services ───────────────────────────────────────────────────
        # ALSoundDetection analyses microphone energy and writes to
        # ALMemory/"SoundDetected" when it exceeds the threshold.
        # setParameter must be called BEFORE subscribe() to take effect.
        try:
            self._sound_detection = self._session.service("ALSoundDetection")
            sensitivity = self.get_parameter("sound_sensitivity").value
            self._sound_detection.setParameter("Sensitivity", float(sensitivity))
            self._sound_detection.subscribe("ros2_sensors")
            self.get_logger().info(
                f"[Sensors] ALSoundDetection active (sensitivity={sensitivity:.2f})"
            )
        except Exception as exc:
            self.get_logger().warning(f"[Sensors] ALSoundDetection unavailable: {exc}")

        # ALSoundLocalization analyses the four microphones to estimate the 3-D
        # direction of the loudest sound source (azimuth + elevation in radians).
        # It writes to ALMemory after every analysis frame (roughly 170 ms).
        try:
            self._sound_localization = self._session.service("ALSoundLocalization")
            self._sound_localization.subscribe("ros2_sensors")
            self.get_logger().info("[Sensors] ALSoundLocalization active.")
            # Discover the real ALMemory key name for this NAOqi version.
            # The key only appears after the first sound triggers localization,
            # so we do a speculative query and log whatever is already there.
            try:
                loc_keys = self._memory.getDataList("ALSoundLocalization")
                self.get_logger().info(f"[Sensors] ALSoundLocalization ALMemory keys: {loc_keys}")
            except Exception:
                pass
        except Exception as exc:
            self.get_logger().warning(f"[Sensors] ALSoundLocalization unavailable: {exc}")

        self.get_logger().info(f"[Sensors] Connected to {host}:{port} — sensors active.")

        self._start_polling(self.get_parameter("poll_hz").value)

    # ── Polling callback ─────────────────────────────────────────────────────

    def _poll(self):
        """Read all sensors from ALMemory and publish. Called at poll_hz by the ROS timer."""
        if self._memory is None:
            return

        # ── Touch buttons — one batch RPC for all keys ──────────────────────
        try:
            btn_vals = self._memory.getListData(list(self._btn_keys.values()))
        except Exception:
            return
        for (name, _key), raw in zip(self._btn_keys.items(), btn_vals):
            if raw is not None:
                self._btn_pubs[name].publish(Bool(data=bool(raw)))

        # ── Sonar ────────────────────────────────────────────────────────────
        try:
            sonar_vals = self._memory.getListData(list(SONAR_KEYS.values()))
        except Exception:
            return
        for (side, _key), metres in zip(SONAR_KEYS.items(), sonar_vals):
            if metres is not None:
                self._sonar_pubs[side].publish(Float32(data=float(metres)))

        # ── Battery ──────────────────────────────────────────────────────────
        try:
            charge = self._memory.getData(BATTERY_KEY)
            if charge is not None:
                self._battery_pub.publish(Float32(data=float(charge)))
        except Exception:
            pass

        # ── Sound detection ──────────────────────────────────────────────────
        # ALMemory NEVER clears SoundDetected after a sound event — the last
        # detected event stays in memory until NAOqi restarts. Naively reading
        # bool(value) therefore gives permanent True after the first sound.
        #
        # Fix: each SoundDetected event carries a [time_s, time_us] timestamp
        # at index 0. We compare it to the timestamp we saw last poll; if it
        # changed, a NEW sound was detected this cycle. If it's the same old
        # timestamp, we're looking at a stale event → report silence.
        try:
            sound_data = self._memory.getData(SOUND_DETECTED_KEY)
            if sound_data and len(sound_data) >= 1 and sound_data[0]:
                ts = (int(sound_data[0][0]), int(sound_data[0][1]))
                is_new = (ts != self._last_sound_ts)
                self._last_sound_ts = ts
                self._sound_det_pub.publish(Bool(data=is_new))
            else:
                # None or empty list → confirmed silence
                self._last_sound_ts = None
                self._sound_det_pub.publish(Bool(data=False))
        except Exception:
            pass

        # ── Sound localization ───────────────────────────────────────────────
        # ALSoundLocalization/SoundLocated structure observed on NAOqi 2.1.x:
        #   [ [timestamp_s, timestamp_us],
        #     [azimuth_rad, elevation_rad, confidence, energy],
        #     [mic_left, mic_right, mic_back, ...],   ← 6 microphone signals
        #     [ ... ] ]
        # azimuth   0 = front, positive = robot's left
        # elevation 0 = horizontal, positive = above
        # confidence 0.0–1.0
        # Note: older docs described index 2 for the angles; the actual key on
        # NAOqi 2.1 places them at index 1. Confirmed from getDataList output.
        try:
            loc = self._memory.getData(SOUND_LOCATION_KEY)
            if not self._loc_logged and loc is not None:
                self.get_logger().info(f"[Sensors] Raw localization value: {loc}")
                self._loc_logged = True
            if loc and len(loc) >= 2 and loc[1] and len(loc[1]) >= 3:
                az   = float(loc[1][0])
                el   = float(loc[1][1])
                conf = float(loc[1][2])
                self._sound_az_pub.publish(Float32(data=az))
                self._sound_el_pub.publish(Float32(data=el))
                self._sound_conf_pub.publish(Float32(data=conf))
        except Exception:
            pass

    # ── Shutdown ─────────────────────────────────────────────────────────────

    def disconnect(self):
        """Unsubscribe from all NAOqi services."""
        for proxy in [self._sonar, self._sound_detection, self._sound_localization]:
            if proxy:
                try:
                    proxy.unsubscribe("ros2_sensors")
                except Exception:
                    pass
        self._session = None
        self._memory  = None


def main(args=None):
    rclpy.init(args=args)
    node = NaoSensors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
