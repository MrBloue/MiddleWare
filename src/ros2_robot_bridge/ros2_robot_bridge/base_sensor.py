#!/usr/bin/env python3
# Abstract base class for all robot sensor nodes.
# Mirrors the lifecycle pattern of base_bridge.py but for publishing sensor data:
#   connect() → _start_polling(hz)  [polling-based, e.g. NAO/ALMemory]
#   connect() → subscribe callbacks  [event-driven, e.g. QT via roslibpy]
# Subclasses choose whichever model suits the robot SDK.
import threading
import rclpy
from rclpy.node import Node


class SensorBase(Node):
    """Base class for robot sensor publisher nodes.

    Each adapter subclass must:
      1. Call super().__init__(node_name) first, then declare all parameters.
      2. Call self._start_connect() as the LAST line of __init__ — this spawns
         the connect() thread. Doing it last ensures all declare_parameter() calls
         finish before connect() tries to read them.
      3. Implement connect()    — open the robot connection (runs in a daemon thread)
      4. Implement disconnect() — close it cleanly (called at node shutdown)
      5. Either:
           a. Call _start_polling(hz) inside connect() once the connection is ready,
              then override _poll() to read sensors and publish; OR
           b. Register roslibpy / SDK callbacks directly inside connect() and publish
              from those callbacks — no _poll() needed in that case.

    The base class handles:
      - Calling disconnect() before the node is destroyed
      - A guarded poll-timer helper so subclasses don't have to handle None checks
    """

    def __init__(self, node_name: str):
        super().__init__(node_name)
        self._sensor_timer = None

    # ------------------------------------------------------------------
    # Internal helpers — do not override
    # ------------------------------------------------------------------

    def _start_connect(self):
        """Spawn the connect() thread. Call this as the LAST line of subclass __init__()."""
        threading.Thread(target=self._connect_safe, daemon=True).start()

    def _connect_safe(self):
        """Wraps connect() so exceptions are logged rather than silently killing the thread."""
        try:
            self.connect()
        except Exception as exc:
            self.get_logger().error(f"[{self.get_name()}] connect() raised: {exc}")

    def _start_polling(self, hz: float):
        """Create a ROS timer that calls _poll() at the given frequency.

        Call this from inside connect() once the connection is ready.
        Safe to call from a non-spin thread — rclpy timers are thread-safe.
        """
        if hz <= 0:
            return
        self._sensor_timer = self.create_timer(1.0 / hz, self._poll_safe)

    def _poll_safe(self):
        """Timer callback that calls _poll() with error isolation."""
        try:
            self._poll()
        except Exception as exc:
            self.get_logger().warning(f"[{self.get_name()}] poll error: {exc}")

    def destroy_node(self):
        """Disconnect cleanly before the node is torn down."""
        try:
            self.disconnect()
        except Exception:
            pass
        super().destroy_node()

    # ------------------------------------------------------------------
    # Public interface — subclasses implement these
    # ------------------------------------------------------------------

    def connect(self):
        """Open the connection to the robot and start sensors.

        Runs in a daemon thread — blocking calls are safe here.
        After a successful connection, either:
          - call self._start_polling(hz)  (polling model), or
          - subscribe to SDK callbacks    (event-driven model).
        On failure, log the error and return — the node stays alive.
        """
        raise NotImplementedError

    def disconnect(self):
        """Close the connection and release all SDK resources.

        Called from destroy_node() — must be safe to call more than once.
        """
        pass

    def _poll(self):
        """Read sensor values and publish them.

        Called at the rate set by _start_polling(). Only needed for the
        polling model; leave unimplemented if using event-driven callbacks.
        """
        pass


def main(args=None):
    """Placeholder — base_sensor.py is not meant to be run directly."""
    raise RuntimeError("base_sensor.py is an abstract base — run a concrete sensor node instead.")


if __name__ == "__main__":
    main()
