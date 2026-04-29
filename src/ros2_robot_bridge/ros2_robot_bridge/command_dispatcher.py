#!/usr/bin/env python3
# Validates and forwards /robot_cmd messages to robot_cmd_validated after dedup checks.
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from ros2_robot_bridge.msg import RobotCmd, RobotConfig
import time

# Dedup window: identical command arriving within this many seconds is dropped.
# 5 s is long enough to cover any typical speak duration while still allowing
# a user to intentionally re-send the same command after a pause.
# 1 s was too short — it matched ros2 topic pub's default 1 Hz rate exactly,
# so the second published message would slip through every time.
_DEDUP_WINDOW = 5.0

class CommandDispatcher(Node):
    """Validates /robot_cmd messages and republishes them on robot_cmd_validated."""

    def __init__(self):
        super().__init__("command_dispatcher")
        self._robot_config = None
        self._recent: dict[str, float] = {}  # cmd_key → last forward time
        latched_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE)
        # VOLATILE: commands must not be replayed to late-joining subscribers.
        volatile_qos = QoSProfile(depth=10, durability=DurabilityPolicy.VOLATILE, reliability=ReliabilityPolicy.RELIABLE)
        self._validated_pub = self.create_publisher(RobotCmd, "robot_cmd_validated", volatile_qos)
        self.create_subscription(RobotConfig, "robot_config", self._on_config, latched_qos)
        self.create_subscription(RobotCmd, "/robot_cmd", self._on_cmd, volatile_qos)  # absolute: shared entry point
        self.get_logger().info("[Dispatcher] Ready.  Waiting for /robot_config ...")

    def _on_config(self, msg):
        """Cache the latest robot config to check readiness before forwarding commands."""
        self._robot_config = msg
        status = "READY" if msg.is_ready else "NOT READY"
        self.get_logger().info(f"[Dispatcher] Robot: {msg.robot_type} {msg.robot_version} - {status}")

    def _cmd_key(self, msg):
        """Build a string key that uniquely identifies the logical content of a command."""
        return f"{msg.action}|{msg.text}|{msg.motion_name}|{msg.emotion}|{msg.led_name}|{msg.color}|{msg.image_path}"

    def _on_cmd(self, msg):
        """Validate and dedup an incoming command, then forward it to robot_cmd_validated."""
        if self._robot_config is None:
            self.get_logger().warning("[Dispatcher] No robot config yet - command dropped.")
            return
        if not self._robot_config.is_ready:
            self.get_logger().warning("[Dispatcher] Robot not ready - command dropped.")
            return
        action = msg.action.lower().strip()
        if action not in ("speak", "move", "display", "relax", "stiffen"):
            self.get_logger().error(f"[Dispatcher] Unknown action '{msg.action}' - dropped.")
            return
        # Dedup: drop if identical command already forwarded within the window
        key = self._cmd_key(msg)
        now = time.monotonic()
        if key in self._recent and now - self._recent[key] < _DEDUP_WINDOW:
            return
        self._recent[key] = now
        # Prune old entries to avoid unbounded growth
        self._recent = {k: t for k, t in self._recent.items() if now - t < _DEDUP_WINDOW * 2}
        self.get_logger().info(f"[Dispatcher] Forwarding '{action}' to {self._robot_config.robot_type} {self._robot_config.robot_version}")
        self._validated_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CommandDispatcher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()
