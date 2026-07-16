#!/usr/bin/env python3
"""
woz_node.py — Wizard-of-Oz web interface with multi-robot support.

Each connected robot gets its own WOZ session at /r/<rid>/.
The /robots page lets the operator add and disconnect robots.
Commands execute directly on the robot via qi (NAO/Pepper).
"""
import math
import os
import re
import socket
import tempfile
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String as _RosString

try:
    from ros2_robot_bridge.msg import RobotConfig
    _HAS_MSG = True
except ImportError:
    _HAS_MSG = False

try:
    from flask import Flask, jsonify, render_template, request, redirect, session
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False

import ros2_robot_bridge.woz_states as _s  # noqa: E402
from ros2_robot_bridge.robot_discovery import RobotDiscovery  # noqa: E402
from ros2_robot_bridge.nao_behavior_tables import (  # noqa: E402
    BEHAVIORS as _NAO_BEHAVIORS,
    QT_TO_NAO_BEHAVIOR as _QT_TO_NAO_BEHAVIOR,
    QT_TO_NAO_MOTION as _QT_TO_NAO_MOTION,
    GESTURES as _NAO_GESTURES,
)

# ── Whisper (lazy) ────────────────────────────────────────────────────────────

_whisper_model = None
_whisper_lock  = threading.Lock()

def _get_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
        except ImportError:
            pass
    return _whisper_model

try:
    from ament_index_python.packages import get_package_share_directory as _gpsd
    _share = _gpsd('ros2_robot_bridge')
    _TEMPLATE_DIR = os.path.join(_share, 'woz_templates')
    _STATIC_DIR   = os.path.join(_share, 'woz_static')
except Exception:
    _TEMPLATE_DIR = None
    _STATIC_DIR   = None

# ── Per-robot slot constants ──────────────────────────────────────────────────

_SLOT_POSTURES = {
    'stand': 'Stand', 'standinit': 'StandInit', 'standzero': 'StandZero',
    'sit': 'Sit', 'sitrelax': 'SitRelax', 'crouch': 'Crouch',
    'lyingback': 'LyingBack', 'lyingbelly': 'LyingBelly',
}

_SLOT_WALK = {
    'walk_forward':  (0.35,  0.0,  0.0),
    'walk_backward': (-0.35, 0.0,  0.0),
    'walk_left':     (0.0,   0.2,  0.0),
    'walk_right':    (0.0,  -0.2,  0.0),
    'turn_left':     (0.0,   0.0,  0.5),
    'turn_right':    (0.0,   0.0, -0.5),
    'stop':          (0.0,   0.0,  0.0),
}

_SLOT_EMOTIONS = {
    'happy':     (1.0, 1.0, 0.0),
    'sad':       (0.0, 0.0, 1.0),
    'angry':     (1.0, 0.0, 0.0),
    'neutral':   (1.0, 1.0, 1.0),
    'surprised': (0.0, 1.0, 1.0),
    'scared':    (0.5, 0.0, 0.5),
    'excited':   (1.0, 0.5, 0.0),
}

_SLOT_LANG = {
    'fr': 'French', 'fr-FR': 'French',
    'en': 'English', 'en-US': 'English', 'en-GB': 'English',
    'de': 'German',  'de-DE': 'German',
    'es': 'Spanish', 'es-ES': 'Spanish',
    'it': 'Italian', 'it-IT': 'Italian',
    'ja': 'Japanese','ja-JP': 'Japanese',
    'zh': 'Chinese', 'zh-CN': 'Chinese',
}

_SLOT_LED_GROUPS = {
    'eyes': 'FaceLeds', 'left_eye': 'LeftFaceLeds', 'right_eye': 'RightFaceLeds',
    'ears': 'EarLeds', 'left_ear': 'LeftEarLeds', 'right_ear': 'RightEarLeds',
    'chest': 'ChestLeds', 'feet': 'FeetLeds', 'head': 'BrainLeds',
    'shoulder': 'ShoulderLeds', 'left_shoulder': 'LeftShoulderLeds',
    'right_shoulder': 'RightShoulderLeds', 'all': 'AllLeds',
}

_SLOT_NAMED_COLORS = {
    'red': 0xFF0000, 'green': 0x00FF00, 'blue': 0x0000FF,
    'white': 0xFFFFFF, 'yellow': 0xFFFF00, 'cyan': 0x00FFFF,
    'magenta': 0xFF00FF, 'orange': 0xFF8000, 'purple': 0x800080,
    'pink': 0xFF69B4, 'off': 0x000000,
}

_STRIP_RE = re.compile(r'#[A-Z0-9]+#|\\sel=[^\\]+\\')

# Joystick walk/head maps (used in route handler)
_WALK_MAP = {
    'walk_fwd':    'walk_forward',
    'walk_back':   'walk_backward',
    'strife_left': 'walk_left',
    'strife_right':'walk_right',
    'rotate_left': 'turn_left',
    'rotate_right':'turn_right',
    'stop':        'stop',
}

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


# ── Robot slot ────────────────────────────────────────────────────────────────

class _RobotSlot:
    """Holds a qi connection and per-robot WOZ state for one robot."""

    def __init__(self, rid: int, host: str, robot_type: str, robot_version: str,
                 language: str, logger):
        self.rid          = rid
        self.host         = host
        self.robot_type   = robot_type
        self.robot_version = robot_version
        self.language     = language
        self._log         = logger

        self.child_name   = ''
        self.adult_name   = ''
        self.state        = 'begin'
        self.auto_timer   = None
        self._sm_lock     = threading.Lock()

        self._qi          = None
        self._posture     = None
        self._motion      = None
        self._tts         = None
        self._leds        = None
        self._behavior    = None
        self._audio       = None
        self.connected    = False
        self.connecting   = True
        self.error        = ''

    def start_connect(self):
        threading.Thread(target=self._connect, daemon=True).start()

    def _connect(self):
        try:
            import qi  # noqa: F401
            s = qi.Session()
            s.connect(f'tcp://{self.host}:9559')
            self._qi       = s
            self._posture  = s.service('ALRobotPosture')
            self._motion   = s.service('ALMotion')
            self._tts      = s.service('ALTextToSpeech')
            self._leds     = s.service('ALLeds')
            self._behavior = s.service('ALBehaviorManager')
            self._audio    = s.service('ALAudioDevice')
            try:
                life = s.service('ALAutonomousLife')
                life.setState('disabled')
            except Exception:
                pass
            try:
                self._motion.setStiffnesses('Body', 1.0)
            except Exception:
                pass
            self.connected  = True
            self.connecting = False
            self._log.info(f'[WOZ] Slot {self.rid} connected: {self.host}')
        except Exception as exc:
            self.connecting = False
            self.error      = str(exc)
            self._log.error(f'[WOZ] Slot {self.rid} connect failed: {exc}')

    def disconnect(self):
        if self.auto_timer:
            self.auto_timer.cancel()
            self.auto_timer = None
        try:
            if self._qi:
                self._qi.close()
        except Exception:
            pass
        self._qi       = None
        self.connected  = False
        self.connecting = False

    # ── Command execution ─────────────────────────────────────────────────────

    def exec_cmd(self, action: str, **kwargs):
        if not self.connected:
            return
        threading.Thread(target=self._do_exec, args=(action,), kwargs=kwargs, daemon=True).start()

    def _do_exec(self, action: str, **kwargs):
        try:
            if action == 'speak':
                self._do_speak(kwargs.get('text', ''), kwargs.get('language', self.language))
            elif action == 'move':
                self._do_move(kwargs.get('motion_name', ''), float(kwargs.get('speed', 0.5)))
            elif action == 'display':
                self._do_display(
                    kwargs.get('emotion', ''),
                    kwargs.get('led_name', ''),
                    kwargs.get('color', 'white'),
                )
            elif action == 'relax':
                if self._tts:
                    try:
                        self._tts.stopAll()
                    except Exception:
                        pass
                part = kwargs.get('motion_name', 'body')
                if self._motion:
                    if part == 'body':
                        self._motion.rest()
                    else:
                        self._motion.setStiffnesses(part, 0.0)
            elif action == 'stiffen':
                if self._motion:
                    self._motion.wakeUp()
            elif action == 'volume':
                level = int(float(kwargs.get('speed', 0.5)) * 100)
                if self._audio:
                    self._audio.setOutputVolume(level)
        except Exception as exc:
            self._log.warning(f'[WOZ] Slot {self.rid} exec error ({action}): {exc}')

    def _do_speak(self, text: str, language: str):
        if not self._tts or not text:
            return
        nao_lang = _SLOT_LANG.get(language, 'French')
        self._tts.setLanguage(nao_lang)
        self._tts.say(text)

    def _do_move(self, motion_name: str, speed: float):
        if not motion_name:
            return
        mn_lower = motion_name.lower()

        # Posture
        posture = _SLOT_POSTURES.get(mn_lower)
        if posture and self._posture:
            self._posture.goToPosture(posture, max(0.1, min(1.0, speed)))
            return

        # Walk
        walk = _SLOT_WALK.get(motion_name)
        if walk is not None and self._motion:
            x, y, theta = walk
            if motion_name == 'stop':
                self._motion.stopMove()
            else:
                try:
                    self._motion.setStiffnesses('Body', 1.0)
                except Exception:
                    pass
                self._motion.moveToward(x * speed, y * speed, theta * speed)
            return

        # Raw joint control: Joint:angle[,Joint:angle,...]
        if ':' in motion_name and self._motion:
            pairs = [p.split(':') for p in motion_name.split(',') if ':' in p]
            joints = [p[0] for p in pairs]
            angles = [float(p[1]) for p in pairs]
            self._motion.setAngles(joints, angles, max(0.05, speed))
            return

        # Named gesture / behavior — resolve via nao_behavior_tables
        if self._behavior:
            try:
                if mn_lower in _NAO_BEHAVIORS:
                    self._behavior.runBehavior(_NAO_BEHAVIORS[mn_lower])
                    return
                if mn_lower in _QT_TO_NAO_BEHAVIOR:
                    nao_name = _QT_TO_NAO_BEHAVIOR[mn_lower]
                    if nao_name and nao_name in _NAO_BEHAVIORS:
                        self._behavior.runBehavior(_NAO_BEHAVIORS[nao_name])
                        return
                if mn_lower in _QT_TO_NAO_MOTION:
                    nao_name = _QT_TO_NAO_MOTION[mn_lower]
                    if nao_name and nao_name in _NAO_BEHAVIORS:
                        self._behavior.runBehavior(_NAO_BEHAVIORS[nao_name])
                        return
            except Exception as exc:
                self._log.warning(f'[WOZ] Slot {self.rid} runBehavior error ({motion_name}): {exc}')
            # Last resort: try running as a raw behavior path
            try:
                if self._behavior.isBehaviorInstalled(motion_name):
                    self._behavior.runBehavior(motion_name)
                    return
            except Exception as exc:
                self._log.warning(f'[WOZ] Slot {self.rid} raw behavior error ({motion_name}): {exc}')

        # Joint-angle gesture sequences (wave, nod, shake_head, arms_open, peekaboo, …)
        if mn_lower in _NAO_GESTURES and self._motion:
            gesture = _NAO_GESTURES[mn_lower]
            steps = gesture if isinstance(gesture, list) else (
                gesture.get('init', []) + gesture.get('loop', []) + gesture.get('cleanup', [])
            )
            try:
                for joint_names, joint_angles, step_speed, pause in steps:
                    self._motion.angleInterpolationWithSpeed(
                        list(joint_names), [float(a) for a in joint_angles], float(step_speed))
                    if pause > 0:
                        time.sleep(pause)
            except Exception as exc:
                self._log.warning(f'[WOZ] Slot {self.rid} gesture error ({motion_name}): {exc}')

    def _do_display(self, emotion: str, led_name: str, color: str):
        if not self._leds:
            return
        if emotion:
            r, g, b = _SLOT_EMOTIONS.get(emotion.lower(), (1.0, 1.0, 1.0))
            rgb_int = int(r * 255) << 16 | int(g * 255) << 8 | int(b * 255)
            try:
                self._leds.fadeRGB('FaceLeds',  rgb_int, 0.3)
                self._leds.fadeRGB('ChestLeds', rgb_int, 0.3)
            except Exception:
                pass
            return
        if led_name:
            rgb_int = _SLOT_NAMED_COLORS.get(color, 0xFFFFFF)
            if color.startswith('#') and len(color) == 7:
                try:
                    rgb_int = int(color[1:], 16)
                except ValueError:
                    pass
            group = _SLOT_LED_GROUPS.get(led_name, led_name)
            try:
                self._leds.fadeRGB(group, rgb_int, 0.3)
            except Exception:
                pass

    # ── State machine ─────────────────────────────────────────────────────────

    def on_button(self, button_name: str):
        if self.auto_timer:
            self.auto_timer.cancel()
        self.enter_state(button_name)

    def enter_state(self, state_name: str):
        with self._sm_lock:
            self.state = state_name

        if state_name == 'end':
            return
        if state_name not in _s.states:
            self._log.warning(f'[WOZ] Slot {self.rid} unknown state: {state_name}')
            return

        behavior, triggers = _s.states[state_name]
        self._log.info(f'[WOZ] Slot {self.rid} → {state_name}')

        if behavior:
            self._execute_behavior(behavior)

        for trig in triggers:
            if trig[0] == 'time':
                if self.auto_timer:
                    self.auto_timer.cancel()
                self.auto_timer = threading.Timer(
                    float(trig[1]), self.enter_state, args=(trig[2],)
                )
                self.auto_timer.daemon = True
                self.auto_timer.start()
                break

    def _execute_behavior(self, beh: dict):
        has_joints = 'h' in beh or 'la' in beh or 'ra' in beh

        txt = beh.get('s', '')
        if txt:
            txt = txt.replace('child_name', self.child_name)
            txt = txt.replace('adult_name', self.adult_name)
            txt = txt.replace('robot_name', self.robot_type or 'le robot')
            if txt.startswith('~'):
                txt = txt[1:]
            txt = _STRIP_RE.sub('', txt).strip()
            self.exec_cmd(action='speak', text=txt, language=self.language)

        emotion = beh.get('e', '')
        if emotion:
            self.exec_cmd(action='display', emotion=emotion)

        gesture = beh.get('g', '')
        if gesture and not has_joints:
            spd = beh.get('spd', 0.0)
            self.exec_cmd(action='move', motion_name=gesture, speed=spd)

        if 'h' in beh:
            yaw, pitch = beh['h']
            self.exec_cmd(
                action='move',
                motion_name=f'HeadYaw:{math.radians(yaw):.4f},HeadPitch:{math.radians(pitch):.4f}',
            )
        if 'la' in beh:
            p, r, e = beh['la']
            self.exec_cmd(
                action='move',
                motion_name=(f'LShoulderPitch:{math.radians(p):.4f},'
                             f'LShoulderRoll:{math.radians(r):.4f},'
                             f'LElbowRoll:{math.radians(e):.4f}'),
            )
        if 'ra' in beh:
            p, r, e = beh['ra']
            self.exec_cmd(
                action='move',
                motion_name=(f'RShoulderPitch:{math.radians(p):.4f},'
                             f'RShoulderRoll:{math.radians(r):.4f},'
                             f'RElbowRoll:{math.radians(e):.4f}'),
            )

    def as_dict(self) -> dict:
        return {
            'rid':          self.rid,
            'host':         self.host,
            'robot_type':   self.robot_type,
            'robot_version': self.robot_version,
            'connected':    self.connected,
            'connecting':   self.connecting,
            'error':        self.error,
        }


# ── WOZ node ──────────────────────────────────────────────────────────────────

class WozNode(Node):

    def __init__(self):
        super().__init__('woz_node')

        self.declare_parameter('woz_host', '0.0.0.0')
        self.declare_parameter('woz_port', 5555)
        self.declare_parameter('language', 'fr-FR')

        self._lang         = self.get_parameter('language').value
        self._robots: dict[int, _RobotSlot] = {}
        self._next_rid     = 0
        self._robots_lock  = threading.Lock()

        self._discovery = RobotDiscovery()
        self._discovery.start()

        if not _HAS_FLASK:
            self.get_logger().error('[WOZ] flask not installed — pip install flask')
            return

        host = self.get_parameter('woz_host').value
        port = self.get_parameter('woz_port').value

        threading.Thread(target=self._run_flask, args=(host, port), daemon=True).start()
        threading.Thread(target=_get_whisper, daemon=True).start()

        display_host = host if host != '0.0.0.0' else socket.gethostbyname(socket.gethostname())
        self.get_logger().info(f'[WOZ] Web interface → https://{display_host}:{port}')

    # ── Robot management ──────────────────────────────────────────────────────

    def add_robot(self, host: str, robot_type: str, robot_version: str) -> int:
        with self._robots_lock:
            rid = self._next_rid
            self._next_rid += 1
        slot = _RobotSlot(rid, host, robot_type, robot_version, self._lang, self.get_logger())
        slot.start_connect()
        with self._robots_lock:
            self._robots[rid] = slot
        return rid

    def remove_robot(self, rid: int):
        with self._robots_lock:
            slot = self._robots.pop(rid, None)
        if slot:
            slot.disconnect()

    def get_robot(self, rid: int) -> '_RobotSlot | None':
        return self._robots.get(rid)

    def all_robots(self) -> list:
        with self._robots_lock:
            return [s.as_dict() for s in self._robots.values()]

    # ── Flask ─────────────────────────────────────────────────────────────────

    def _run_flask(self, host, port):
        kwargs = {}
        if _TEMPLATE_DIR and os.path.isdir(_TEMPLATE_DIR):
            kwargs['template_folder'] = _TEMPLATE_DIR
        if _STATIC_DIR and os.path.isdir(_STATIC_DIR):
            kwargs['static_folder']   = _STATIC_DIR
            kwargs['static_url_path'] = '/static'
        app = Flask(__name__, **kwargs)
        app.secret_key = 'woz'
        _register_routes(app, self)
        try:
            import OpenSSL  # noqa: F401
            ssl_ctx = 'adhoc'
        except ImportError:
            self.get_logger().warning(
                '[WOZ] pyopenssl not installed — serving HTTP (mic blocked on LAN). pip install pyopenssl'
            )
            ssl_ctx = None
        app.run(host=host, port=port, debug=False, use_reloader=False, ssl_context=ssl_ctx)


# ── Flask routes ──────────────────────────────────────────────────────────────

def _register_routes(app: 'Flask', node: WozNode):

    # ── Robot list / management ───────────────────────────────────────────────

    @app.route('/')
    def index():
        return redirect('/robots')

    # Legacy redirect so old bookmarks still work
    @app.route('/connect', methods=['GET'])
    def connect_legacy():
        return redirect('/robots')

    @app.route('/login', methods=['GET'])
    def login_legacy():
        return redirect('/robots')

    @app.route('/scenarios')
    @app.route('/reactions')
    @app.route('/maison')
    @app.route('/macros')
    @app.route('/vocal')
    def tab_legacy():
        return redirect('/robots')

    @app.route('/robots', methods=['GET', 'POST'])
    def robots_page():
        error = ''
        if request.method == 'POST':
            robot_type    = request.form.get('robot_type', 'nao')
            robot_version = request.form.get('robot_version', '')
            robot_ip      = request.form.get('robot_ip', '').strip()
            if not robot_ip:
                error = "Veuillez entrer l'adresse IP du robot."
            else:
                port = 9090 if robot_type == 'qtrobot' else 9559
                try:
                    with socket.create_connection((robot_ip, port), timeout=4):
                        pass
                    rid = node.add_robot(robot_ip, robot_type, robot_version)
                    return redirect(f'/r/{rid}/login')
                except OSError as exc:
                    error = f"Robot non joignable à {robot_ip}:{port} — {exc}"
        return render_template('robots.html', robots=node.all_robots(), error=error)

    @app.route('/robots/<int:rid>/disconnect', methods=['POST'])
    def disconnect_robot(rid):
        node.remove_robot(rid)
        session.pop(f'rid_{rid}_ok', None)
        return redirect('/robots')

    @app.route('/robots/status')
    def robots_status():
        return jsonify(node.all_robots())

    @app.route('/robots/scan')
    def robots_scan():
        return jsonify({
            'scanning': node._discovery.scanning,
            'robots':   node._discovery.robots,
        })

    @app.route('/robots/scan/refresh', methods=['POST'])
    def robots_scan_refresh():
        node._discovery.refresh()
        return jsonify({'ok': True})

    # ── Per-robot pages ───────────────────────────────────────────────────────

    def _slot_ok(rid: int) -> bool:
        return node.get_robot(rid) is not None and bool(session.get(f'rid_{rid}_ok'))

    @app.route('/r/<int:rid>/login', methods=['GET', 'POST'])
    def robot_login(rid):
        slot = node.get_robot(rid)
        if slot is None:
            return redirect('/robots')
        if request.method == 'POST':
            if not slot.connected:
                return render_template('login.html', rid=rid, robot_ip=slot.host,
                                       robot_type=slot.robot_type,
                                       connecting=slot.connecting,
                                       conn_error=slot.error or 'Robot non connecté')
            fname  = request.form.get('fname', '').strip() or 'Enfant'
            lname  = request.form.get('lname', '').strip()
            fname2 = request.form.get('fname2', '').strip() or 'Accompagnant'
            slot.child_name = f'{fname} {lname}'.strip()
            slot.adult_name = fname2
            session[f'rid_{rid}_ok'] = True
            slot.enter_state('begin')
            return redirect(f'/r/{rid}/scenarios')
        return render_template('login.html', rid=rid, robot_ip=slot.host,
                               robot_type=slot.robot_type,
                               connecting=slot.connecting,
                               conn_error=slot.error)

    @app.route('/r/<int:rid>/')
    def robot_root(rid):
        return redirect(f'/r/{rid}/scenarios')

    def _render_tab(template: str, rid: int):
        if not _slot_ok(rid):
            return redirect('/robots')
        slot = node.get_robot(rid)
        child = slot.child_name if slot else ''
        return render_template(template, rid=rid, child_name=child)

    @app.route('/r/<int:rid>/scenarios')
    def robot_scenarios(rid):
        return _render_tab('scenarios.html', rid)

    @app.route('/r/<int:rid>/reactions')
    def robot_reactions(rid):
        return _render_tab('reactions.html', rid)

    @app.route('/r/<int:rid>/maison')
    def robot_maison(rid):
        return _render_tab('maison.html', rid)

    @app.route('/r/<int:rid>/macros')
    def robot_macros(rid):
        return _render_tab('macros.html', rid)

    @app.route('/r/<int:rid>/vocal')
    def robot_vocal(rid):
        return _render_tab('vocal.html', rid)

    # ── Per-robot command endpoint ────────────────────────────────────────────

    @app.route('/r/<int:rid>/woz', methods=['POST'])
    def robot_woz(rid):
        slot = node.get_robot(rid)
        if slot is None:
            return jsonify({'error': 'robot not connected'}), 404

        payload = request.get_json(silent=True) or {}

        if 'motion' in payload:
            spd = max(0.1, min(1.0, float(payload.get('speed', 0.5))))
            slot.exec_cmd(action='move', motion_name=str(payload['motion']), speed=spd)
            return jsonify({})

        if 'speak_text' in payload:
            slot.exec_cmd(action='speak', text=str(payload['speak_text']), language=slot.language)
            return jsonify({})

        if 'emotion' in payload and 'command' not in payload and 'walk' not in payload:
            slot.exec_cmd(action='display', emotion=str(payload['emotion']))
            return jsonify({})

        if 'led_name' in payload:
            slot.exec_cmd(action='display',
                          led_name=str(payload['led_name']),
                          color=str(payload.get('led_color', 'white')))
            return jsonify({})

        if payload.get('relax'):
            slot.exec_cmd(action='relax', motion_name='body')
            return jsonify({})

        if payload.get('stiffen'):
            slot.exec_cmd(action='stiffen')
            return jsonify({})

        if 'volume' in payload:
            try:
                level = max(0.0, min(1.0, float(payload['volume']) / 100.0))
                slot.exec_cmd(action='volume', speed=level)
            except (ValueError, TypeError):
                pass
            return jsonify({})

        button = (payload.get('command') or
                  payload.get('direction') or
                  payload.get('walk') or '')
        if not button:
            return jsonify({})

        if button in _WALK_MAP:
            slot.exec_cmd(action='move', motion_name=_WALK_MAP[button])
            return jsonify({})

        if button in _HEAD_MAP:
            yaw, pitch = _HEAD_MAP[button]
            slot.exec_cmd(
                action='move',
                motion_name=f'HeadYaw:{math.radians(yaw):.4f},HeadPitch:{math.radians(pitch):.4f}',
                speed=0.15,
            )
            return jsonify({})

        slot.on_button(button)
        return jsonify({})

    # ── Per-robot transcription ───────────────────────────────────────────────

    @app.route('/r/<int:rid>/woz_transcribe', methods=['POST'])
    def robot_transcribe(rid):
        slot = node.get_robot(rid)
        if slot is None:
            return jsonify({'error': 'robot not connected'}), 404

        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({'error': 'no audio'}), 400

        model = _get_whisper()
        if model is None:
            return jsonify({'error': 'faster-whisper non installé — pip install faster-whisper'}), 503

        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            audio_file.save(tmp)
            tmp_path = tmp.name

        mode = request.form.get('mode', 'repeat')
        prompt = None
        temperature = 0.0 if mode == 'command' else 0.2
        if mode == 'command':
            prompt = (
                'debout, assis, salue, bonjour, applaudis, oui, non, arc, bras ouverts, '
                'donne, pointe, muscles, câlin, content, heureux, triste, rire, peur, '
                'confus, timide, excité, colère, réfléchis, danse, guitare, zombie, '
                'kung fu, avance, recule, gauche, droite, tourne, stop, arrête, '
                'relax, détends-toi, stiffen, raidis-toi'
            )

        try:
            segments, _ = model.transcribe(
                tmp_path, language='fr', initial_prompt=prompt,
                beam_size=5, temperature=temperature,
                condition_on_previous_text=False,
                vad_filter=True, vad_parameters={'min_silence_duration_ms': 300},
            )
            text = ' '.join(s.text.strip() for s in segments)
            node.get_logger().info(f'[WOZ] Slot {rid} Whisper heard: {text!r}')
            return jsonify({'text': text})
        except Exception as exc:
            node.get_logger().warning(f'[WOZ] Slot {rid} Whisper error: {exc}')
            return jsonify({'error': str(exc)}), 500
        finally:
            os.unlink(tmp_path)


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
