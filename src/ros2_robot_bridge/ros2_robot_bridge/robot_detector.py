#!/usr/bin/env python3
# Publishes RobotConfig based on launch parameters; re-publishes every 2 s as a heartbeat.
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from ros2_robot_bridge.msg import RobotConfig

VALID_VERSIONS = {
    "nao":     ["v5", "v6"],
    "pepper":  ["v1", "v1.8", "v2"],
    "qtrobot": ["qt1", "qt2"],
}

class RobotDetector(Node):
    """Reads robot_type / robot_version params and publishes a latched RobotConfig."""

    def __init__(self):
        super().__init__("robot_detector")
        self.declare_parameter("robot_type",    "nao")
        self.declare_parameter("robot_version", "v6")
        latched_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._pub = self.create_publisher(RobotConfig, "robot_config", latched_qos)
        self._last = None
        self._publish_config()
        self.create_timer(2.0, self._publish_config)
        self.get_logger().info("RobotDetector started.")

    def _publish_config(self):
        """Validate params and publish RobotConfig; only republishes when something changes."""
        robot_type    = self.get_parameter("robot_type").get_parameter_value().string_value.lower().strip()
        robot_version = self.get_parameter("robot_version").get_parameter_value().string_value.lower().strip()
        msg = RobotConfig()
        msg.robot_type    = robot_type
        msg.robot_version = robot_version
        if robot_type not in VALID_VERSIONS:
            msg.is_ready   = False
            msg.status_msg = f"Unknown robot_type '{robot_type}'. Valid: {list(VALID_VERSIONS)}"
            self.get_logger().error(msg.status_msg)
            self._pub.publish(msg)
            return
        if robot_version and robot_version not in VALID_VERSIONS[robot_type]:
            msg.is_ready   = False
            msg.status_msg = f"Unknown robot_version '{robot_version}' for '{robot_type}'. Valid: {VALID_VERSIONS[robot_type]}"
            self.get_logger().error(msg.status_msg)
            self._pub.publish(msg)
            return
        msg.is_ready   = True
        msg.status_msg = f"Configured as {robot_type.upper()}" + (f" {robot_version}" if robot_version else "")
        if self._last is None or self._last.robot_type != msg.robot_type or self._last.robot_version != msg.robot_version:
            self._last = msg
            self._pub.publish(msg)
            self.get_logger().info(msg.status_msg)

def main(args=None):
    rclpy.init(args=args)
    node = RobotDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()
