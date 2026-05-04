#!/usr/bin/env python3
"""
Template for a new robot sensor node.

To add sensor support for a new robot, follow these steps:

  1. Copy this file and rename it, e.g. my_robot_sensor.py
  2. Fill in every TODO below — choose the polling OR event-driven model
  3. Add the sensor node to robot_bridge.launch.py (_make_nodes function)
  4. Add the file to the install(PROGRAMS ...) list in CMakeLists.txt

Two data models — choose the one that matches your robot SDK:

  A — POLLING  (e.g. NAO/Pepper via ALMemory, HTTP REST, serial port)
        connect()  →  open connection, acquire proxies
                   →  call self._start_polling(hz)   ← base class handles the timer
        _poll()    →  batch-read all sensors → publish
        disconnect() →  release proxies / close connection

  B — EVENT-DRIVEN  (e.g. WebSocket subscriptions, SDK callbacks, ROS1 via roslibpy)
        connect()      →  open connection
                       →  register callbacks OR call sdk.run() (blocking — must be last)
        callbacks      →  publish on every incoming message
        disconnect()   →  unsubscribe, terminate connection

Key constraint shared by both models:
  _start_connect() must be the LAST call in __init__() — it spawns the connect()
  thread. Everything before it (declare_parameter, create_publisher) must be done
  first, otherwise connect() may read parameters that haven't been declared yet.

Reference implementations:
  nao_sensors.py  — Pattern A: qi SDK, ALMemory.getListData() batch poll
  qt_sensor.py    — Pattern B: roslibpy WebSocket subscriptions
"""

import rclpy
from std_msgs.msg import Bool, Float32
from sensor_msgs.msg import JointState
from ros2_robot_bridge.base_sensor import SensorBase

# TODO: import your robot SDK here
# try:
#     import my_robot_sdk
#     _HAS_SDK = True
# except ImportError:
#     _HAS_SDK = False

# ---------------------------------------------------------------------------
# Constants — robot-side data source names.
#
# For polling robots: ALMemory keys, register addresses, REST endpoints …
# For event-driven robots: topic/channel names, event IDs …
#
# Document what each constant refers to so the mapping is unambiguous.
# ---------------------------------------------------------------------------
# Pattern A examples (ALMemory keys):
#   _KEY_TOUCH_CHEST  = "Device/SubDeviceList/ChestBoard/Button/Sensor/Value"
#   _KEY_BATTERY      = "Device/SubDeviceList/Battery/Charge/Sensor/Value"
#   _KEY_SONAR_LEFT   = "Device/SubDeviceList/US/Left/Sensor/Value"
#
# Pattern B examples (topic names):
#   _TOPIC_JOINTS     = "/my_robot/joints/state"
#   _TOPIC_BATTERY    = "/my_robot/battery_state"


class MyRobotSensor(SensorBase):
    """Sensor publisher for MyRobot.

    Reads sensor data from the physical robot and publishes it as ROS2
    topics in the node namespace (set by the launch file).

    Topics published (relative to the node namespace, e.g. /myrobot_42/...):
      sensor/touch      std_msgs/Bool    — True while a touch sensor is pressed
      battery           std_msgs/Float32 — charge level 0.0 (empty) to 1.0 (full)
      sonar/front       std_msgs/Float32 — distance in metres (0 = no echo)
      joint_states      sensor_msgs/JointState — joint positions (radians)

    Parameters:
      my_robot_host  string  "192.168.1.200"  — robot IP
      my_robot_port  int     1234             — SDK/WebSocket port
      poll_hz        float   20.0             — poll rate (Pattern A only)
    """

    def __init__(self):
        super().__init__("my_robot_sensor")  # TODO: rename node

        # Declare all ROS2 parameters before _start_connect() is called.
        self.declare_parameter("my_robot_host", "192.168.1.200")  # TODO: rename
        self.declare_parameter("my_robot_port", 1234)             # TODO: set default
        self.declare_parameter("poll_hz",       20.0)             # Pattern A only

        self._host    = self.get_parameter("my_robot_host").value
        self._port    = self.get_parameter("my_robot_port").value
        self._poll_hz = self.get_parameter("poll_hz").value

        # ── ROS2 publishers ──────────────────────────────────────────────────
        # QoS depth=1: only the latest reading matters; stale sensor data is useless.
        qos = 1

        # TODO: keep only the publishers that match your robot's actual sensors.
        self._pub_touch  = self.create_publisher(Bool,       "sensor/touch",  qos)
        self._pub_battery= self.create_publisher(Float32,    "battery",       qos)
        self._pub_sonar  = self.create_publisher(Float32,    "sonar/front",   qos)
        self._pub_joints = self.create_publisher(JointState, "joint_states",  qos)

        # ── SDK handles — set in connect(), cleared in disconnect() ──────────
        self._client = None  # TODO: replace with the correct type for your SDK

        self.get_logger().info(
            f"[MyRobotSensor] Connecting to {self._host}:{self._port} ..."
        )
        # Spawn the connect() thread. Must be the last line of __init__.
        self._start_connect()

    # ------------------------------------------------------------------
    # connect() — runs in a daemon thread, blocking calls are safe here
    # ------------------------------------------------------------------

    def connect(self):
        """Open the connection to the robot and start the data flow.

        Pattern A — polling:
            1. Open connection, acquire SDK proxy/session
            2. Call self._start_polling(self._poll_hz) — base class takes over
            The base class will call _poll() at the requested rate.

        Pattern B — event-driven:
            1. Open connection
            2. Register callbacks (each callback publishes to a self._pub_* topic)
            3. Call sdk.run() or equivalent as the very last statement — it blocks
               until disconnect() calls sdk.terminate(). Never put code after it.
        """

        # ── PATTERN A (polling) ──────────────────────────────────────────────
        # try:
        #     self._client = my_robot_sdk.Session()
        #     self._client.connect(f"tcp://{self._host}:{self._port}")
        #     self._memory = self._client.service("ALMemory")
        #     self.get_logger().info("[MyRobotSensor] Connected.")
        # except Exception as exc:
        #     self.get_logger().error(f"[MyRobotSensor] Connection failed: {exc}")
        #     return
        # self._start_polling(self._poll_hz)   # ← triggers _poll() at poll_hz

        # ── PATTERN B (event-driven / WebSocket) ─────────────────────────────
        # try:
        #     self._client = roslibpy.Ros(host=self._host, port=self._port)
        #     self._client.on_ready(self._on_connected)
        #     self._client.run()   # ← blocks; must be the last statement
        # except Exception as exc:
        #     self.get_logger().error(f"[MyRobotSensor] Connection failed: {exc}")
        #     self._client = None

        self.get_logger().warning("[MyRobotSensor] connect() not implemented yet.")

    def disconnect(self):
        """Close the connection and release all SDK resources.

        Called automatically by the base class at node shutdown.
        Safe to call more than once.

        Pattern A:  self._client.close() or self._session.close()
        Pattern B:  self._client.terminate()
        """
        if self._client is not None:
            try:
                pass  # TODO: self._client.close() or self._client.terminate()
            except Exception:
                pass
            self._client = None

    # ------------------------------------------------------------------
    # Pattern A — _poll()
    # Delete this method entirely if using Pattern B.
    # ------------------------------------------------------------------

    def _poll(self):
        """Read all sensors in one batch and publish.

        Called by the base class at poll_hz via a ROS timer.
        Keep this fast — it runs in the ROS2 spin thread.

        Prefer a single batch RPC call (e.g. ALMemory.getListData) over
        individual per-sensor calls to minimize Wi-Fi round-trip latency.
        """
        if self._client is None:
            return

        # TODO: read sensor values and publish.
        #
        # Batch example (ALMemory):
        #   keys = [_KEY_TOUCH_CHEST, _KEY_BATTERY, _KEY_SONAR_LEFT]
        #   try:
        #       vals = self._memory.getListData(keys)
        #   except Exception:
        #       return
        #   self._pub_touch.publish(Bool(data=bool(vals[0])))
        #   self._pub_battery.publish(Float32(data=float(vals[1])))
        #   self._pub_sonar.publish(Float32(data=float(vals[2])))
        #
        # Individual example (REST / serial):
        #   try:
        #       status = self._client.get_status()
        #   except Exception:
        #       return
        #   self._pub_battery.publish(Float32(data=status["battery"] / 100.0))
        #   self._pub_touch.publish(Bool(data=status["button_pressed"]))

    # ------------------------------------------------------------------
    # Pattern B — _on_connected() + per-sensor callbacks
    # Delete this method and all callbacks if using Pattern A.
    # ------------------------------------------------------------------

    def _on_connected(self):
        """Called once when the SDK/WebSocket connection is ready (Pattern B).

        Register one subscription or callback per sensor here.
        Each callback receives a message dict and publishes to self._pub_*.
        """
        self.get_logger().info("[MyRobotSensor] Connected — registering subscriptions.")

        # TODO: add one block per sensor.
        #
        # roslibpy example:
        #   def _on_battery(msg):
        #       level = float(msg.get("percentage", 0))
        #       if level > 1.0:
        #           level /= 100.0
        #       self._pub_battery.publish(Float32(data=max(0.0, min(1.0, level))))
        #
        #   sub = roslibpy.Topic(self._client, _TOPIC_BATTERY, "sensor_msgs/BatteryState")
        #   sub.subscribe(_on_battery)
        #
        # SDK callback example:
        #   self._client.on_sensor("touch", lambda v: self._pub_touch.publish(Bool(data=bool(v))))


def main(args=None):
    rclpy.init(args=args)
    node = MyRobotSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()


# =============================================================================
# PROMPT FOR AI ASSISTANTS
# Copy everything between the === lines into your AI assistant, fill in the
# fields marked [FILL IN], and it will produce a complete sensor node file.
# =============================================================================
#
# You are implementing a ROS2 robot sensor node for the `ros2_robot_bridge`
# package. Read this entire template file carefully before writing any code —
# the architecture, constraints, and examples are all embedded in it.
#
# ## What this node does
#
# It reads sensor data from a physical robot and re-publishes it as standard
# ROS2 topics under the node namespace (set at launch time). Other nodes — a
# dashboard, a behaviour tree, a monitoring script — subscribe to those topics
# without knowing anything about the robot SDK.
#
# ## Base class: SensorBase (ros2_robot_bridge/base_sensor.py)
#
# Your class inherits SensorBase, which handles:
#   - Spawning the connect() thread when _start_connect() is called
#   - Calling disconnect() automatically at node shutdown
#   - The _start_polling(hz) helper that drives the _poll() timer (Pattern A)
#
# CRITICAL constraint: _start_connect() must be the LAST statement in __init__.
# All declare_parameter() and create_publisher() calls must come before it,
# because connect() runs in a thread that may start before __init__ finishes.
#
# ## Reference implementations (study these before writing code)
#
#   nao_sensors.py — Pattern A: qi SDK session, ALMemory.getListData() batch poll,
#                    20 Hz timer, touch buttons + sonar + battery + audio.
#   qt_sensor.py   — Pattern B: roslibpy WebSocket, topic subscriptions,
#                    joint states + motor states forwarded as ROS2 topics.
#
# ## The new robot
#
# Robot name        : [FILL IN — e.g. "Furhat", "Misty II", "Pepper v3", "TIAGo"]
# SDK / library     : [FILL IN — e.g. "furhat-python-api 1.0", "roslibpy 1.3", "requests"]
# Connection method : [FILL IN — e.g. "WebSocket ws://host:9090", "REST http://host/api/v1",
#                                     "qi TCP tcp://host:9559", "serial /dev/ttyUSB0"]
# Data model        : [FILL IN — "polling" (Pattern A) or "event-driven" (Pattern B)]
#                     Use polling when the SDK has no push/callback support, or when
#                     sensors must be read on demand (e.g. ALMemory, REST endpoints).
#                     Use event-driven when the SDK provides topic subscriptions,
#                     WebSocket streams, or native callbacks.
#
# ## Sensors to bridge
#
# List every sensor the robot exposes that is worth publishing as a ROS2 topic.
# For each, provide: the sensor name, the SDK call or topic name used to read it,
# and the ROS2 message type to publish.
#
# Common sensors and their standard ROS2 mappings:
#   Touch buttons / bumpers  → std_msgs/Bool       topic: sensor/<name>
#   Battery charge           → std_msgs/Float32    topic: battery          (0.0–1.0)
#   Sonar / distance         → std_msgs/Float32    topic: sonar/<name>     (metres)
#   Sound detected (bool)    → std_msgs/Bool       topic: audio/sound_detected
#   Sound direction azimuth  → std_msgs/Float32    topic: audio/localization/azimuth  (radians)
#   Sound direction elevation→ std_msgs/Float32    topic: audio/localization/elevation(radians)
#   Sound confidence         → std_msgs/Float32    topic: audio/localization/confidence
#   Joint positions          → sensor_msgs/JointState  topic: joint_states (radians, ROS standard)
#   Camera image             → sensor_msgs/Image   topic: camera/<name>/image_raw
#   Laser scan               → sensor_msgs/LaserScan  topic: scan
#   IMU                      → sensor_msgs/Imu     topic: imu
#
# Sensor list (repeat for each sensor):
#   Sensor name      : [FILL IN — e.g. "chest button", "left sonar", "battery"]
#   SDK source       : [FILL IN — ALMemory key / topic name / API call]
#   ROS2 topic       : [FILL IN — e.g. "sensor/chest", "sonar/left", "battery"]
#   ROS2 message type: [FILL IN — e.g. "std_msgs/Bool", "std_msgs/Float32"]
#   Notes            : [FILL IN — units, value range, any conversion needed]
#
# ## What to produce
#
# A single complete Python file based on this template. Do not produce partial
# snippets — the file must be runnable as-is after filling in the SDK calls.
#
# Step-by-step:
#
#   1. Rename the class MyRobotSensor → <RobotName>Sensor and the node name
#      "my_robot_sensor" → "<robot_name>_sensor" throughout.
#
#   2. Replace the TODO parameter declarations with the real connection
#      parameters (host, port, or whatever the SDK needs). Keep poll_hz only
#      if using Pattern A.
#
#   3. Replace the TODO publishers with exactly one publisher per sensor
#      listed above. Use the standard topic names and message types from the
#      table above. Import any additional message types at the top of the file.
#
#   4. Choose ONE pattern and delete ALL code for the other:
#
#      Pattern A — polling:
#        - Implement connect(): open the SDK connection, acquire all proxies/
#          sessions needed by _poll(), then call self._start_polling(self._poll_hz).
#          If connection fails, log the error and return without calling _start_polling.
#        - Implement _poll(): read ALL sensors in a single batch RPC call where
#          possible (reduces Wi-Fi latency). Publish each value. Guard with
#          `if self._client is None: return`. Wrap reads in try/except and return
#          on failure so a transient error does not crash the poll loop.
#        - Implement disconnect(): release all proxies, close session, set
#          self._client = None.
#        - Delete _on_connected() entirely.
#
#      Pattern B — event-driven:
#        - Implement connect(): open the WebSocket or SDK session, register
#          _on_connected as the ready callback, then call sdk.run() or equivalent
#          as the VERY LAST statement (it blocks until disconnect() terminates it).
#        - Implement _on_connected(): register one subscription/callback per sensor.
#          Each callback receives raw SDK data, converts it to the ROS message type,
#          and calls self._pub_<sensor>.publish(...). Inline small conversions
#          (unit scaling, clamping); extract helpers only for complex transforms.
#        - Implement disconnect(): call sdk.terminate() or sdk.close(), set
#          self._client = None.
#        - Delete _poll() entirely.
#
#   5. For Pattern A — if the SDK requires an explicit "activate" call to start
#      a sensor (e.g. ALSonar.subscribe, ALSoundDetection.subscribe), do that
#      in connect() before calling _start_polling(). Mirror those calls with
#      the corresponding "deactivate" calls in disconnect().
#
#   6. For Pattern B — if a subscription may silently produce no data when the
#      robot-side topic does not exist (e.g. roslibpy), add a comment noting
#      that the user should verify the topic with `rostopic list` on the robot.
#
#   7. Battery values: if the SDK returns 0–100 (percentage), divide by 100
#      before publishing. If it returns Wh or V, document the conversion.
#      Always clamp to [0.0, 1.0] before publishing.
#
#   8. Do NOT add any sensor that was not listed above. Do NOT add error handling
#      for cases that cannot happen (e.g. None checks on values the SDK guarantees
#      are non-None). Keep the file concise — one method per concern.
#
# ## Integration checklist (provide alongside the file)
#
#   A. The Node(...) block to insert in robot_bridge.launch.py (_make_nodes).
#      Match the is_<robot> branch pattern already used for nao_sensors / qt_sensor.
#
#   B. The install(PROGRAMS ...) entry to add to CMakeLists.txt.
#
#   C. Any new DeclareLaunchArgument entries needed in generate_launch_description().
#
# =============================================================================
