#!/usr/bin/env python3
"""
qt_sensor.py — Bridges QTrobot ROS1 sensor topics into ROS2 via roslibpy.

QTrobot runs ROS1 internally; its data is accessible through the rosbridge
WebSocket server. This node subscribes to available topics via roslibpy and
re-publishes them as standard ROS2 topics in the node namespace.

Available topics on this robot (from `rostopic list`):
  /qt_robot/joints/state        sensor_msgs/JointState — arm/head joint positions
  /qt_robot/motors/states       (motor torque / temperature / error flags)

Topics NOT available on this QTrobot firmware (subscriptions skipped):
  head touch, battery, sonar — these topics do not exist on this robot.

Topics published (all relative to the node namespace, e.g. /qtrobot_1/...):
  joint_states        sensor_msgs/JointState — joint positions (radians, ROS standard)
  motor_states        std_msgs/String        — raw motor state JSON for diagnostics

Parameters:
  qt_host     string  "192.168.100.1"  — robot IP (same as qt_bridge.py)
  qt_port     int     9090             — rosbridge WebSocket port
  sensor_hz   float   10.0             — max rate for joint-state re-publish (0 = all)
"""
import time

import rclpy
from ros2_robot_bridge.base_sensor import SensorBase
from sensor_msgs.msg import JointState
from std_msgs.msg import String

try:
    import roslibpy
    _HAS_ROSLIBPY = True
except ImportError:
    _HAS_ROSLIBPY = False

_QT_TOPIC_JOINTS = "/qt_robot/joints/state"
_QT_TOPIC_MOTORS = "/qt_robot/motors/states"


class QTSensor(SensorBase):
    """Re-publishes QTrobot ROS1 sensor topics as ROS2 topics via roslibpy."""

    def __init__(self):
        super().__init__("qt_sensor")

        self.declare_parameter("qt_host",   "192.168.100.1")
        self.declare_parameter("qt_port",   9090)
        # sensor_hz: cap the joint-state re-publish rate. The robot publishes at
        # ~2 Hz so 10 Hz is effectively "forward everything". Set to 0 to disable throttle.
        self.declare_parameter("sensor_hz", 10.0)

        self._host      = self.get_parameter("qt_host").value
        self._port      = self.get_parameter("qt_port").value
        self._sensor_hz = self.get_parameter("sensor_hz").value

        qos = 1  # only the latest value matters

        self._pub_joints = self.create_publisher(JointState, "joint_states", qos)
        self._pub_motors = self.create_publisher(String,     "motor_states", qos)

        self._client        = None
        self._subs: list    = []
        self._last_joint_t  = 0.0

        self.get_logger().info(
            f"[QTSensor] Connecting to rosbridge @ {self._host}:{self._port} ..."
        )
        self._start_connect()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self):
        if not _HAS_ROSLIBPY:
            self.get_logger().error(
                "[QTSensor] roslibpy not installed — no sensor data will be published."
            )
            return
        try:
            self._client = roslibpy.Ros(host=self._host, port=self._port)
            self._client.on_ready(self._on_connected)
            self._client.run()
        except Exception as exc:
            self.get_logger().error(f"[QTSensor] Could not connect: {exc}")
            self._client = None

    def disconnect(self):
        if self._client:
            try:
                self._client.terminate()
            except Exception:
                pass
            self._client = None

    def _on_connected(self):
        self.get_logger().info(
            f"[QTSensor] rosbridge CONNECTED @ {self._host}:{self._port}"
        )
        self._subscribe_joints()
        self._subscribe_motors()

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    def _subscribe_joints(self):
        """Bridge /qt_robot/joints/state → ROS2 joint_states."""
        min_dt = (1.0 / self._sensor_hz) if self._sensor_hz > 0 else 0.0

        def _cb(msg):
            now = time.monotonic()
            if min_dt > 0 and (now - self._last_joint_t) < min_dt:
                return
            self._last_joint_t = now
            js = JointState()
            js.header.stamp = self.get_clock().now().to_msg()
            js.name         = msg.get("name", [])
            js.position     = msg.get("position", [])
            js.velocity     = msg.get("velocity", [])
            js.effort       = msg.get("effort", [])
            self._pub_joints.publish(js)

        try:
            sub = roslibpy.Topic(self._client, _QT_TOPIC_JOINTS, "sensor_msgs/JointState")
            sub.subscribe(_cb)
            self._subs.append(sub)
            self.get_logger().info(f"[QTSensor] subscribed → {_QT_TOPIC_JOINTS}")
        except Exception as exc:
            self.get_logger().warning(f"[QTSensor] joints/state subscribe failed: {exc}")

    def _subscribe_motors(self):
        """Bridge /qt_robot/motors/states → ROS2 motor_states (raw JSON string)."""
        def _cb(msg):
            import json
            self._pub_motors.publish(String(data=json.dumps(msg)))

        try:
            # The message type for motors/states is not standardised across firmware
            # versions — subscribe as a generic type and forward as a JSON string.
            sub = roslibpy.Topic(self._client, _QT_TOPIC_MOTORS, "qt_robot_interface/robot_state")
            sub.subscribe(_cb)
            self._subs.append(sub)
            self.get_logger().info(f"[QTSensor] subscribed → {_QT_TOPIC_MOTORS}")
        except Exception as exc:
            self.get_logger().warning(f"[QTSensor] motors/states subscribe failed: {exc}")


def main(args=None):
    rclpy.init(args=args)
    node = QTSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
