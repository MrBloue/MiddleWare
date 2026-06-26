#!/usr/bin/env python3
# Abstract base class for all robot bridges.
# Handles the ROS2 plumbing common to every adapter: robot_config subscription,
# command dispatch, and the connect/disconnect lifecycle.
# To add a new robot adapter, see robot_bridge_template.py.
import threading
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from ros2_robot_bridge.msg import RobotCmd, RobotConfig

# How long (seconds) to suppress a repeated identical command at the bridge level.
# This is a second dedup layer that catches DDS retransmissions of the same
# message (e.g. TRANSIENT_LOCAL replay when a participant joins late).
_BRIDGE_DEDUP_S = 5.0


class RobotBridge(Node):
    """Base class for all robot bridges.

    Each adapter subclass must:
      1. Declare SUPPORTED_TYPES = ("robot_type", ...)
      2. Implement connect(), do_speak(), do_move(), do_display()
      3. Optionally override disconnect(), do_stiffness(),
         _on_activate(), _on_deactivate()

    The base class handles:
      - Subscribing to robot_config and robot_cmd_validated
      - Activating / deactivating on config changes
      - Dispatching commands to the right do_* method
      - Calling disconnect() before node teardown
    """

    # Subclass must override — e.g. ("nao", "pepper") or ("qtrobot",)
    SUPPORTED_TYPES: tuple[str, ...] = ()

    def __init__(self, node_name: str):
        super().__init__(node_name)
        self._active = False
        self._robot_type = ""
        self._robot_version = ""
        self._recent_cmds: dict[str, float] = {}  # key → last-executed monotonic time
        self._recent_lock = threading.Lock()

        latched_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        volatile_qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.create_subscription(RobotConfig, "robot_config", self._on_config, latched_qos)
        self.create_subscription(RobotCmd, "robot_cmd_validated", self._on_cmd, volatile_qos)
        self.get_logger().info(f"[{node_name}] Waiting for /robot_config ...")

    # ------------------------------------------------------------------
    # Lifecycle hooks — override in subclass if needed
    # ------------------------------------------------------------------

    def _on_activate(self, msg: RobotConfig):
        """Called synchronously before connect() on activation.
        Use this to read parameters and initialize robot-specific state."""
        pass

    def _on_deactivate(self):
        """Called synchronously before disconnect() on deactivation.
        Use this to clear proxies, publishers, or cached state."""
        pass

    # ------------------------------------------------------------------
    # Internal config handler — do not override
    # ------------------------------------------------------------------

    def _on_config(self, msg: RobotConfig):
        """Activate or deactivate the bridge based on robot_config transitions."""
        was_active = self._active
        self._active = (msg.robot_type in self.SUPPORTED_TYPES and msg.is_ready)

        if self._active and not was_active:
            self._robot_type = msg.robot_type
            self._robot_version = msg.robot_version
            self.get_logger().info(
                f"[{self.get_name()}] Activated for "
                f"{msg.robot_type.upper()} {msg.robot_version}"
            )
            self._on_activate(msg)
            threading.Thread(target=self.connect, daemon=True).start()

        elif not self._active and was_active:
            self.get_logger().info(f"[{self.get_name()}] Deactivated.")
            self._on_deactivate()
            threading.Thread(target=self.disconnect, daemon=True).start()

    def destroy_node(self):
        """Cleanly disconnect before the node is torn down."""
        try:
            self.disconnect()
        except Exception:
            pass
        super().destroy_node()

    # ------------------------------------------------------------------
    # Internal command dispatcher — do not override
    # ------------------------------------------------------------------

    def _cmd_key(self, msg: RobotCmd) -> str:
        return f"{msg.action}|{msg.text}|{msg.motion_name}|{msg.emotion}|{msg.led_name}|{msg.color}|{msg.image_path}"

    def _on_cmd(self, msg: RobotCmd):
        """Route an incoming validated command to the right do_* handler."""
        if not self._active:
            return
        # Bridge-level dedup: DDS can replay the same message multiple times
        # (e.g. TRANSIENT_LOCAL participants or RELIABLE retransmissions).
        key = self._cmd_key(msg)
        now = time.monotonic()
        with self._recent_lock:
            if key in self._recent_cmds and now - self._recent_cmds[key] < _BRIDGE_DEDUP_S:
                return
            self._recent_cmds[key] = now
            # Prune stale entries to keep the dict bounded.
            self._recent_cmds = {k: t for k, t in self._recent_cmds.items()
                                  if now - t < _BRIDGE_DEDUP_S * 2}
        action = msg.action.lower().strip()
        if action == "speak":
            self.do_speak(msg)
        elif action == "move":
            self.do_move(msg)
        elif action == "display":
            self.do_display(msg)
        elif action in ("relax", "stiffen"):
            self.do_stiffness(msg, stiff=(action == "stiffen"))
        elif action == "volume":
            self.do_volume(msg)
        self._after_cmd(msg)

    # ------------------------------------------------------------------
    # Public interface — subclasses implement these
    # ------------------------------------------------------------------

    def connect(self):
        """Open the connection to the robot.
        Called in a background thread after activation.
        Must be non-blocking (or handle blocking internally with threads)."""
        raise NotImplementedError

    def disconnect(self):
        """Close the connection to the robot gracefully.
        Called in a background thread on deactivation and at node teardown."""
        pass

    def _after_cmd(self, msg: RobotCmd):
        """Called after every command dispatch. Subclasses can override."""
        pass

    def do_speak(self, msg: RobotCmd):
        """Execute a speak command (msg.text, msg.language)."""
        raise NotImplementedError

    def do_move(self, msg: RobotCmd):
        """Execute a move / gesture / walk / posture command (msg.motion_name, msg.speed)."""
        raise NotImplementedError

    def do_display(self, msg: RobotCmd):
        """Execute a display command (msg.emotion, msg.led_name, msg.color,
        msg.image_path, msg.duration_ms)."""
        raise NotImplementedError

    def do_stiffness(self, msg: RobotCmd, stiff: bool):
        """Execute a relax/stiffen command (msg.motion_name = body part).
        Default implementation logs that the action is not supported."""
        label = "stiffen" if stiff else "relax"
        self.get_logger().info(
            f"[{self.get_name()}] '{label}' not supported on this robot — skipped."
        )

    def do_volume(self, msg: RobotCmd):
        """Set audio output volume. msg.speed is the level (0.0–1.0).
        Default implementation logs that the action is not supported."""
        self.get_logger().info(
            f"[{self.get_name()}] 'volume' not supported on this robot — skipped."
        )
