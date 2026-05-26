#!/usr/bin/env python3
"""
woz_node.py — Wizard-of-Oz web interface bridged to the ROS2 robot bridge.

Runs a Flask web server on port 5555 (configurable). The operator opens the
interface in a browser, selects a scenario, and clicks reaction/scenario buttons.
Each button maps to a state in woz_states.py that carries a behavior dict:
  's' → speech text     → RobotCmd(action='speak')
  'e' → emotion path    → RobotCmd(action='display', emotion=...)
  'g' → gesture path    → RobotCmd(action='move', motion_name=...)
  'h' → [yaw, pitch]   → RobotCmd(action='move', motion_name='HeadYaw:x,HeadPitch:y')
  'la'→ [p, r, e]      → RobotCmd(action='move', motion_name='LeftShoulderPitch:...')
  'ra'→ [p, r, e]      → RobotCmd(action='move', motion_name='RightShoulderPitch:...')

The joystick panels (reactions page) also send walk commands mapped to standard
motion_names: walk_forward, walk_backward, walk_left, walk_right, turn_left,
turn_right, stop.

All messages are published to /robot_cmd and routed by the bridge to the active
robot (NAO, Pepper, or QTrobot).

Parameters:
  woz_host    string  "0.0.0.0"   — Flask bind address
  woz_port    int     5555        — Flask port
  language    string  "fr-FR"     — TTS language code for speak commands
"""
import os
import threading

import rclpy
from rclpy.node import Node
from ros2_robot_bridge.msg import RobotCmd

try:
    from flask import Flask, jsonify, render_template, request, redirect, session
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False

try:
    from ament_index_python.packages import get_package_share_directory as _gpsd
    _share = _gpsd('ros2_robot_bridge')
    _TEMPLATE_DIR = os.path.join(_share, 'woz_templates')
    _STATIC_DIR   = os.path.join(_share, 'woz_static')
except Exception:
    _TEMPLATE_DIR = None
    _STATIC_DIR   = None

import ros2_robot_bridge.woz_states as _s  # noqa: E402

# Joystick walk commands → universal motion_name
_WALK_MAP = {
    'walk_fwd':    'walk_forward',
    'walk_back':   'walk_backward',
    'strife_left': 'walk_left',
    'strife_right':'walk_right',
    'rotate_left': 'turn_left',
    'rotate_right':'turn_right',
    'stop':        'stop',
}

# Head-look joystick directions → HeadYaw/HeadPitch (degrees)
_HEAD_MAP = {
    'up':        ( 0.0, -20.0),
    'down':      ( 0.0,  10.0),
    'left':      (+20.0,  0.0),
    'right':     (-20.0,  0.0),
    'upleft':    (+20.0, -20.0),
    'upright':   (-20.0, -20.0),
    'downleft':  (+10.0, +10.0),
    'downright': (-10.0, +10.0),
    'center':    ( 0.0,   0.0),
}


class WozNode(Node):
    """ROS2 node that hosts the WOZ Flask interface and publishes RobotCmd messages."""

    def __init__(self):
        super().__init__('woz_node')

        self.declare_parameter('woz_host', '0.0.0.0')
        self.declare_parameter('woz_port', 5555)
        self.declare_parameter('language', 'fr-FR')

        self._pub  = self.create_publisher(RobotCmd, '/robot_cmd', 10)
        self._lang = self.get_parameter('language').value

        self._child_name  = ''
        self._adult_name  = ''
        self._state       = 'begin'
        self._auto_timer  = None
        self._lock        = threading.Lock()

        if not _HAS_FLASK:
            self.get_logger().error('[WOZ] flask not installed — node inactive (pip install flask)')
            return

        host = self.get_parameter('woz_host').value
        port = self.get_parameter('woz_port').value

        flask_thread = threading.Thread(
            target=self._run_flask, args=(host, port), daemon=True
        )
        flask_thread.start()
        self.get_logger().info(f'[WOZ] Web interface → http://{host}:{port}')

        # kick off the initial state
        self._enter_state('begin')

    # ── Flask server ──────────────────────────────────────────────────────────

    def _run_flask(self, host, port):
        kwargs = {}
        if _TEMPLATE_DIR and os.path.isdir(_TEMPLATE_DIR):
            kwargs['template_folder'] = _TEMPLATE_DIR
        if _STATIC_DIR and os.path.isdir(_STATIC_DIR):
            kwargs['static_folder'] = _STATIC_DIR
        app = Flask(__name__, **kwargs)
        app.secret_key = 'woz'
        _register_routes(app, self)
        app.run(host=host, port=port, debug=False, use_reloader=False)

    # ── State machine ─────────────────────────────────────────────────────────

    def _enter_state(self, state_name):
        """Enter a state: cancel any pending timer, execute behavior, arm next timer."""
        with self._lock:
            self._state = state_name

        if state_name == 'end':
            self.get_logger().info('[WOZ] Reached end state.')
            return

        if state_name not in _s.states:
            self.get_logger().warning(f'[WOZ] Unknown state: {state_name}')
            return

        behavior, triggers = _s.states[state_name]
        self.get_logger().info(f'[WOZ] → {state_name}')

        if behavior:
            self._execute_behavior(behavior)

        # Arm the time-based auto-transition (first 'time' trigger wins)
        for trig in triggers:
            if trig[0] == 'time':
                if self._auto_timer:
                    self._auto_timer.cancel()
                self._auto_timer = threading.Timer(
                    float(trig[1]), self._enter_state, args=(trig[2],)
                )
                self._auto_timer.daemon = True
                self._auto_timer.start()
                break

    def on_button(self, button_name):
        """Operator pressed a WOZ button — jump to that state."""
        if self._auto_timer:
            self._auto_timer.cancel()
        self._enter_state(button_name)

    # ── Behavior → RobotCmd translation ──────────────────────────────────────

    def _execute_behavior(self, beh: dict):
        has_joints = 'h' in beh or 'la' in beh or 'ra' in beh

        # Speech
        txt = beh.get('s', '')
        if txt:
            txt = txt.replace('child_name', self._child_name)
            txt = txt.replace('adult_name', self._adult_name)
            if txt.startswith('~'):
                txt = txt[1:]
            self._pub_cmd(action='speak', text=txt, language=self._lang)

        # Emotion (facial expression on QTrobot, LEDs on NAO/Pepper)
        emotion = beh.get('e', '')
        if emotion:
            self._pub_cmd(action='display', emotion=emotion)

        # Gesture — only when no joint-level control in this state
        gesture = beh.get('g', '')
        if gesture and not has_joints:
            self._pub_cmd(action='move', motion_name=gesture)

        # Head: [yaw_deg, pitch_deg]
        if 'h' in beh:
            yaw, pitch = beh['h']
            self._pub_cmd(action='move',
                          motion_name=f'HeadYaw:{yaw},HeadPitch:{pitch}')

        # Left arm: [ShoulderPitch, ShoulderRoll, ElbowRoll] degrees
        if 'la' in beh:
            p, r, e = beh['la']
            self._pub_cmd(action='move',
                          motion_name=f'LeftShoulderPitch:{p},LeftShoulderRoll:{r},LeftElbowRoll:{e}')

        # Right arm: [ShoulderPitch, ShoulderRoll, ElbowRoll] degrees
        if 'ra' in beh:
            p, r, e = beh['ra']
            self._pub_cmd(action='move',
                          motion_name=f'RightShoulderPitch:{p},RightShoulderRoll:{r},RightElbowRoll:{e}')

    def _pub_cmd(self, **kwargs):
        msg = RobotCmd()
        for k, v in kwargs.items():
            setattr(msg, k, v)
        self._pub.publish(msg)


# ── Flask routes ──────────────────────────────────────────────────────────────

def _register_routes(app: 'Flask', node: WozNode):

    def _session_ok():
        return (session.get('user_name') and session.get('user_surname'))

    @app.route('/')
    def index():
        return redirect('/login')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            session['user_name']    = request.form.get('fname', '')
            session['user_surname'] = request.form.get('lname', '')
            session['teacher_name'] = request.form.get('fname2', '')
            node._child_name = session['user_name']
            node._adult_name = session['teacher_name']
            node._enter_state('begin')
            return render_template('scenarios.html')
        return render_template('login.html')

    @app.route('/reactions')
    def reactions():
        if not _session_ok():
            return redirect('/')
        return render_template('reactions.html')

    @app.route('/scenarios')
    def scenarios():
        if not _session_ok():
            return redirect('/')
        return render_template('scenarios.html')

    @app.route('/theatre')
    def theatre():
        if not _session_ok():
            return redirect('/')
        return render_template('theatre.html')

    @app.route('/maison')
    def maison():
        if not _session_ok():
            return redirect('/')
        return render_template('maison.html')

    @app.route('/woz', methods=['POST'])
    def woz():
        payload = request.get_json(silent=True) or {}
        button  = (payload.get('command') or
                   payload.get('direction') or
                   payload.get('walk') or '')
        if not button:
            return jsonify({})

        # Walk joystick
        if button in _WALK_MAP:
            node._pub_cmd(action='move', motion_name=_WALK_MAP[button])
            return jsonify({})

        # Head-look joystick (direction strings from woz.js)
        if button in _HEAD_MAP:
            yaw, pitch = _HEAD_MAP[button]
            node._pub_cmd(action='move',
                          motion_name=f'HeadYaw:{yaw},HeadPitch:{pitch}')
            return jsonify({})

        # WOZ reaction/scenario button
        node.on_button(button)
        return jsonify({})


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = WozNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
