# ros2_robot_bridge

Universal ROS2 command interface for heterogeneous robots. Publish a single `RobotCmd` message — the bridge automatically routes it to the active robot using the correct protocol.

Currently supported: **NAO** (v5/v6, NAOqi ≥ 2.1.4), **Pepper** (v1/v1.8/v2, NAOqi ≥ 2.5), and **QTrobot QT1/QT2** (via rosbridge/roslibpy).

---

## Architecture

```
/robot_cmd  →  command_dispatcher  →  /robot_cmd_validated  →  nao_bridge   →  NAO / Pepper robot
                                                             →  qt_bridge    →  QTrobot

robot_detector  →  /robot_config  (TRANSIENT_LOCAL, describes the active robot)

nao_sensors  →  sensor/*, sonar/*, battery, audio/*   (NAO / Pepper — polls ALMemory via qi)
qt_sensor    →  joint_states, motor_states             (QTrobot — bridges ROS1 topics via roslibpy)
```

The user always publishes to `/robot_cmd`. The dispatcher validates the command against the active robot config and forwards it. Each bridge translates the universal message into robot-specific calls. Sensor nodes run independently and publish live robot data regardless of which commands are being sent.

---

## Prerequisites

### NAO / Pepper

The bridge connects directly via the **qi SDK** — no naoqi_driver2 required.

- `qi` Python SDK must be installed on the bridge machine
- NAOqi must be running on the robot (port 9559)

> **Note:** Always source `/opt/ros/jazzy/setup.bash` before building/launching. Do not source other ROS overlays (e.g. `~/ros2_jazzy`) — this causes a FastCDR ABI mismatch.

### QTrobot

- `rosbridge_server` must be running on the QTrobot (ROS1):
  ```bash
  roslaunch rosbridge_server rosbridge_websocket.launch
  ```
- `roslibpy` must be installed: `pip install roslibpy`

### Python dependencies

```bash
pip install -r src/ros2_robot_bridge/requirements.txt
```

| Package | Purpose |
|---------|---------|
| `flask>=3.0` | WOZ web server |
| `roslibpy>=1.3` | QTrobot rosbridge client |
| `pyopenssl>=23.0` | HTTPS for WOZ (mic access on LAN) |
| `faster-whisper>=1.0` | Server-side speech-to-text for the Vocal tab |

The WOZ interface runs over **HTTPS** (self-signed certificate via pyopenssl). Browsers will show a security warning the first time — accept it once. HTTPS is required for microphone access from any device other than localhost.

---

## Jetson / ROS2 Humble

The package is compatible with both **ROS2 Jazzy** (Ubuntu 24.04) and **ROS2 Humble** (Ubuntu 22.04 / Jetson). No code changes are needed when targeting Humble.

`setup.sh` at the workspace root bootstraps a fresh Ubuntu 22.04 / Jetson system end-to-end: locale, ROS2 Humble apt repository, system packages, rosdep, pip dependencies, and colcon build.

```bash
bash setup.sh
```

---

## Build

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Lutin/mw_ws
colcon build --packages-skip nao_meshes pepper_meshes
source install/setup.bash
```

---

## Launch

### NAO
```bash
ros2 launch ros2_robot_bridge robot_bridge.launch.py \
    robot_type:=nao robot_version:=v5 naoqi_host:=192.168.24.46
```

### Pepper
```bash
ros2 launch ros2_robot_bridge robot_bridge.launch.py \
    robot_type:=pepper robot_version:=v1.8 naoqi_host:=192.168.24.11
```

`robot_version` is optional for NAO and Pepper (used for display only — does not affect behavior).

### QTrobot QT1
```bash
ros2 launch ros2_robot_bridge robot_bridge.launch.py \
    robot_type:=qtrobot robot_version:=qt1 qt_host:=192.168.100.1
```

### QTrobot QT2
```bash
ros2 launch ros2_robot_bridge robot_bridge.launch.py \
    robot_type:=qtrobot robot_version:=qt2 qt_host:=<QT_IP>
```

### Launch arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `robot_type` | `nao` | `nao`, `pepper`, or `qtrobot` |
| `robot_version` | _(empty)_ | `v5`/`v6` (NAO) · `v1`/`v1.8`/`v2` (Pepper) · `qt1`/`qt2` (QTrobot) |
| `naoqi_host` | `192.168.1.100` | NAO/Pepper IP address |
| `naoqi_port` | `9559` | NAOqi port |
| `naoqi_scheme` | `tcp` | Connection scheme: `tcp` or `tcps` (TLS gateway) |
| `naoqi_ssl_cert` | _(empty)_ | CA certificate path for `tcps` connections |
| `qt_host` | `192.168.100.1` | QTrobot rosbridge IP |
| `qt_port` | `9090` | QTrobot rosbridge port |
| `queue_commands` | `false` | Buffer commands for sequential execution |
| `cmd_timeout_s` | `10.0` | Seconds before a queued command expires |
| `sensor_poll_hz` | `20.0` | Sensor polling frequency in Hz (NAO/Pepper only) |
| `sound_sensitivity` | `0.5` | ALSoundDetection sensitivity: `0.0` (deaf) to `1.0` (very sensitive) |
| `woz` | `false` | Enable the Wizard-of-Oz web interface |
| `woz_host` | `0.0.0.0` | WOZ Flask bind address |
| `woz_port` | `5555` | WOZ Flask port |
| `language` | `fr-FR` | TTS language for WOZ speech commands |

---

## Wizard-of-Oz (WOZ) Web Interface

The WOZ interface lets an operator remote-control the robot from a browser during a session with a child. It runs as a Flask web server embedded in a ROS2 node and publishes `RobotCmd` messages to `/robot_cmd`. Commands are routed to whichever robot is currently connected — the interface itself is robot-agnostic.

### Enable

Pass `woz:=true` to any launch command:

```bash
ros2 launch ros2_robot_bridge robot_bridge.launch.py woz:=true
```

Then open `https://<bridge-machine-ip>:5555` in a browser on the same network. Accept the self-signed certificate warning once (required for HTTPS — see the note under Prerequisites).

### Multi-robot support

The WOZ supports **multiple simultaneous robot connections**. Each robot gets its own isolated session at `/r/<rid>/`, with its own qi connection, proxies, and login state.

### Robots page (`/robots`)

The browser always lands on `/robots` first. This page lists all currently connected robots and provides a form to add a new one. Fill in:

- **Type** — `nao`, `pepper`, or `qtrobot`
- **Version** — version choices update automatically based on type
- **IP address** — the robot's IP on your network

On submit the WOZ:
1. Verifies the robot is reachable on its expected port (9559 for NAO/Pepper, 9090 for QTrobot).
2. Opens a dedicated qi session for the new robot in a background thread.
3. Redirects to `/r/<rid>/login` for that robot.

Robots can be disconnected individually from the `/robots` page. The live robot list is also available as JSON at `/robots/status`.

### Login

All fields are optional. Defaults are **Enfant** (child) and **Accompagnant** (therapist) if left blank. Names are substituted into speech templates at runtime (`child_name` and `adult_name` placeholders in `woz_states.py`). The robot greets the child on submission.

### Pages

| Tab | Description |
|-----|-------------|
| **Scénario et Jeux** | Scenario launch and explanation buttons grouped by game type |
| **Réactions** | Quick-reaction buttons (emotions, feedback, questions) for live improvisation |
| **Maison** | Alternate activity set (symbolic play, mime, manual activities, daily life) |
| **Macros** | Custom macro buttons, quick motion presets, relax/stiffen controls, a walk joystick, and a head-look joystick |
| **Vocal** | Browser microphone → server-side Whisper transcription → robot repeats or executes a voice command |

All tabs include a walk joystick (bottom-right) and a head-look joystick (bottom-left). An **⛔ STOP** button is always visible — pressing it stops all motor movement and interrupts any ongoing speech.

All category labels in the UI use the generic term **"Le robot"** and are not tied to any specific robot model.

### Vocal tab

The Vocal tab lets the operator speak into the browser microphone and have the robot react.

**Modes:**
- **Répéter** — the robot repeats the transcribed speech verbatim. Whisper runs with natural speech settings (unbiased, temperature 0.2).
- **Commander** — Whisper runs with deterministic settings (temperature 0, vocabulary-biased prompt) and the transcribed text is matched against 57+ French voice commands. On a match the corresponding motion, emotion, walk, or motor action is dispatched; on no match the text is spoken.

**Speed slider** (0.1 – 1.0, persisted in localStorage): scales the speed of motion commands sent from the Vocal tab, mirroring the volume slider behaviour on RobotAct.

**Setup:** The Vocal tab requires the browser to be on the same HTTPS origin as the WOZ server. Open `https://<bridge-ip>:5555` (note the `https://`), accept the self-signed certificate warning once, then the mic permission prompt will appear normally on any device.

**Server-side transcription:** `faster-whisper` (model: `small`, CPU, int8) is loaded lazily at first use and pre-warmed in a background thread at startup. Audio is recorded in the browser using the `MediaRecorder` API (works in Firefox, Chrome, and Safari) and uploaded as a blob to `/woz_transcribe`.

### State machine

Each button sends a state name to the `/woz` endpoint. The state machine in `woz_states.py` defines behaviors for each state:

| Key | Meaning | Sent as |
|-----|---------|---------|
| `s` | Speech text | `RobotCmd(action='speak')` |
| `e` | Emotion / animation name | `RobotCmd(action='display', emotion=...)` |
| `g` | Gesture name | `RobotCmd(action='move', motion_name=...)` |
| `h` | `[yaw_deg, pitch_deg]` head angles | `RobotCmd(action='move', motion_name='HeadYaw:r,HeadPitch:r')` — degrees stored in state machine, converted to radians before publishing |
| `la` | `[pitch, roll, elbow]` left arm degrees | `RobotCmd(action='move', motion_name='LShoulderPitch:r,...')` |
| `ra` | `[pitch, roll, elbow]` right arm degrees | `RobotCmd(action='move', motion_name='RShoulderPitch:r,...')` |
| `spd` | Posture transition speed 0.0–1.0 | `RobotCmd(speed=...)` — applies to posture changes (`Stand`, `Sit`, …) |

Angles are stored in degrees everywhere (state machine and `_HEAD_MAP`) and converted to radians before publishing. This applies both to scripted behaviors and to the head-look joystick on the RobotAct tab.

States can chain via time-based auto-transitions: `('time', seconds, next_state)`. Pressing any button cancels the pending timer and jumps directly to the chosen state.

### TTS preprocessing

The state machine was originally authored for QTrobot and contains robot-specific TTS markup. `woz_node.py` strips these before publishing so NAO's Nuance TTS does not speak them literally:

- Sound tags `#YAWN01#`, `#LAUGH01#`, etc. — removed
- Prosody tags `\sel=alt=p-70\` etc. — removed

NAO-compatible tags that pass through unchanged: `\pau=N\` (pause ms), `\rspd=N\` (speech rate), `\vct=N\` (voice category).

> **Note:** This stripping is always applied regardless of the connected robot. On a QTrobot session the prosody tags would be meaningful — this is a known limitation.

### Gesture and emotion mapping (NAO / Pepper)

Gesture name lookup is **case-insensitive** — `QT/happy`, `qt/happy`, and `Qt/Happy` all resolve to the same NAO animation. `qt/...` gesture paths from `woz_states.py` are translated to NAO equivalents via two dicts in `nao_behavior_tables.py`:

- **`QT_TO_NAO_BEHAVIOR`** — maps to a `BEHAVIORS` or `GESTURES` key for execution.
- **`QT_TO_NAO_MOTION`** — maps to a `GESTURES` key, or `None` to silently skip (used for QT-specific paths that have no meaningful NAO equivalent).

Unrecognized paths are logged at DEBUG level and silently dropped.

Currently mapped QT gesture paths (all WOZ-relevant entries):

| QT path | NAO equivalent |
|---------|----------------|
| `qt/hi` | `wave` |
| `qt/bye` | `wave` |
| `qt/happy` | `happy_anim` |
| `qt/laugh` | `laugh_anim` |
| `qt/yes` | `yes_anim` |
| `qt/no` | `shake_head` |
| `qt/kiss` | `love_you` |
| `qt/face` | `hide_eyes` |
| `qt/peekaboo` | `hide_eyes` |
| `qt/surprise` | `yay` |
| `qt/touch-head` | `pat_pat` |
| `qt/touch-head-back` | `scratch_head` |
| `qt/head_scratch` | `scratch_head` |
| `qt/emotions/sad` | `sad` |
| `qt/bored` | `bored_anim` |
| `qt/angry` | `angry_anim` |
| `qt/curious` | `puzzled` |
| `qt/handclap` | `applause` |
| `qt/thanks` | `bow` |
| `qt/strong` | `show_muscles` |
| `qt/stretch` | `stretch_wait` |
| `qt/yawn` | `relaxation` |
| `qt/show_tablet` | `give` |
| `qt/imitation/nodding-yes` | `nod` |
| `qt/imitation/head-right-left` | `shake_head` |
| `qt/imitation/hands-on-hip` | `show_muscles` |
| `qt/neutral` | _(skipped — no equivalent on NAO)_ |

### Postures (RobotAct tab)

| Button | State | Action |
|--------|-------|--------|
| Debout | `standup` | `Stand` posture |
| LSD | `LSD` | `Sit` posture |
| LSU | `LSU` | `Stand` posture |

---

## Universal Command Interface

All commands share the same message type regardless of robot:

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd "{...}"
```

### Message fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | `speak`, `move`, `display`, `relax`, `stiffen`, or `volume` |
| `text` | string | Text to say |
| `language` | string | Language code (e.g. `en-US`, `fr-FR`) |
| `motion_name` | string | Motion, posture, gesture, walk command, or behavior name |
| `speed` | float32 | Speed 0.0–1.0 (default 0.5) |
| `emotion` | string | Emotion name for LED display |
| `led_name` | string | LED group name for direct color control |
| `color` | string | LED color (`red`, `blue`, `#RRGGBB`, …) |
| `image_path` | string | Image path (QTrobot only) |
| `duration_ms` | int32 | Duration in milliseconds |

---

## speak

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'speak', text: 'Bonjour', language: 'fr-FR'}"
```

| Language code | Language |
|---------------|----------|
| `en-US`, `en-GB`, `en` | English |
| `fr-FR`, `fr` | French |
| `de-DE`, `de` | German |
| `es-ES`, `es` | Spanish |
| `it-IT`, `it` | Italian |
| `ja-JP` | Japanese |
| `zh-CN` | Chinese |

**NAO/Pepper:** calls `ALTextToSpeech.say()` via qi SDK.  
**QTrobot:** publishes to `/qt_robot/speech/say` via rosbridge. Supports **SSML** markup for prosody control (pitch, rate, emphasis, pauses) when the robot's TTS backend is Azure TTS.

**QTrobot SSML examples:**
```bash
# Pause and emphasis
rostopic pub --once /qt_robot/speech/say std_msgs/String \
    'data: "Attends <break time=\"500ms\"/> maintenant je continue."'

# Slower and higher pitch
rostopic pub --once /qt_robot/speech/say std_msgs/String \
    'data: "<prosody rate=\"slow\" pitch=\"+5st\">Je suis heureux !</prosody>"'

# Emphasis level
rostopic pub --once /qt_robot/speech/say std_msgs/String \
    'data: "<emphasis level=\"strong\">Excellent</emphasis> travail !"'
```

> **Bash tip:** Use single quotes `'...'` for the outer shell quoting — the `!` character is then literal and does not trigger bash history expansion.

---

## move

### Walking (NAO / Pepper)

Walking uses `ALMotion.moveToward()` directly via qi — no naoqi_driver2 required. `ALAutonomousLife` is automatically disabled before walking. The robot must **not** be on its charging dock.

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'walk_forward', speed: 0.8}"
```

| `motion_name` | Description |
|---------------|-------------|
| `walk_forward` | Forward — max 0.35 m/s at speed=1.0 |
| `walk_backward` | Backward — max 0.35 m/s |
| `walk_left` | Sidestep left — max 0.2 m/s |
| `walk_right` | Sidestep right — max 0.2 m/s |
| `turn_left` | Rotate left — max 0.5 rad/s |
| `turn_right` | Rotate right — max 0.5 rad/s |
| `stop` | Stop walking |

The `speed` field scales all velocities linearly (e.g. `speed: 0.5` → 0.175 m/s forward).

### Postures (NAO / Pepper)

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'stand', speed: 0.8}"
```

| `motion_name` | NAOqi posture |
|---------------|---------------|
| `stand` | Stand |
| `standinit` | StandInit |
| `standzero` | StandZero |
| `sit` | Sit |
| `sitrelax` | SitRelax |
| `crouch` | Crouch |
| `lyingback` | LyingBack |
| `lyingbelly` | LyingBelly |

### Custom Gestures (NAO / Pepper)

One-shot gestures run once and return to neutral. **Infinite-loop gestures** (marked ∞) run until interrupted by any other `move` command. Only the joints used by each gesture are stiffened — relaxed body parts remain relaxed.

> **NAO / Pepper:** `ALAutonomousLife` is disabled at connect and re-disabled before every walk command so the life manager cannot block motion. Motor stiffness is set to 1.0 at connect (`setStiffnesses`) without forcing a stand-up posture (`wakeUp` is not called, so the robot stays in whatever posture it is in when the WOZ connects).

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'wave'}"

# Start infinite loop
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'pat_pat'}"

# Stop it (any other move command works)
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'stand'}"
```

| `motion_name` | Description | Loop |
|---------------|-------------|------|
| `look_left` | Turn head left and back | |
| `look_right` | Turn head right and back | |
| `look_up` | Tilt head up and back | |
| `look_down` | Tilt head down and back | |
| `nod` | Nod twice | |
| `shake_head` | Shake head side to side | |
| `arms_open` | Both arms spread wide (welcoming) | |
| `point_forward` | Right arm extended forward | |
| `salute` | Right hand raised to forehead | |
| `think` | Right hand near chin, head tilted | |
| `refuse` | Shake head while crossing arm | |
| `arm_up` | Raise right arm straight up | |
| `wave` | Raise and wave right hand | |
| `yay` | Finger flutter, then both arms raised | |
| `clapping` | Clap hands | |
| `sneezing` | Sneeze gesture | |
| `head_scratch` | Scratch head | |
| `peekaboo` | Cover and reveal face | |
| `ohno` | Both hands on head | |
| `hips` | Hands on hips | |
| `drink` | Drinking gesture | |
| `monkey` | Monkey dance | |
| `ecrit` | Writing gesture | |
| `show_tablet` | Both arms forward, palms up | |
| `breathing_exercise` | Slow arms up/down breathing | |
| `neutral` | Return to neutral pose | |
| `sad` | Head down, shoulders hunched | |
| `touch_head_back` | Right arm reaches behind head | |
| `hands_on_head` | Both hands raised at head level | |
| `hands_on_belly` | Arms bent in front at belly | |
| `personal_distance` | Right arm forward, palm out (stop) | |
| `premiere_rencontre` | Bow then wave greeting | |
| `fera_mieux` | Thumbs-up with encouraging nod | |
| `grandpa` | Slow deliberate head turns | |
| `luxai_en` | Alternating arm raises | |
| `give_hand` | Extend left hand open, wait, close | |
| `give_hand_sitted` | Left hand extended for sitting | |
| `give_hand_right` | Extend right hand open, wait, close | |
| `give_hand_sitted_right` | Right hand for sitting | |
| `close_right_hand` | Rotate wrist, close right hand | |
| `close_left_hand` | Rotate wrist, close left hand | |
| `pat_pat` | Pat with finger flutter | ∞ |
| `six_seven` | Pendulum arm swing left↔right | ∞ |
| `test` | Quick arms-up test | |

### Built-in NAOqi Behaviors (NAO / Pepper)

Runs behaviors installed on the robot via `ALBehaviorManager`. The names below are pre-mapped and confirmed on a NAO H25 v5 with NAOqi 2.1.4. Names not listed can still be run using the `behavior:` escape hatch.

If a behavior is not installed on the target robot, the WOZ falls through to the `GESTURES` table automatically. For example, `applause` maps to `animations/Stand/Gestures/Applause_1`; on NAOs that don't have this behavior pack, it falls back to the `clapping` joint-sequence gesture.

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'funny_dancer'}"

# Run any installed behavior by raw path (bypasses the table)
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'behavior:animations/Stand/Waiting/Zombie_1'}"
```

> To discover all behaviors installed on a robot: `qicli call ALBehaviorManager.getInstalledBehaviors`

**Dance / performance:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `funny_dancer` | `animations/Stand/Waiting/FunnyDancer_1` |
| `air_guitar` | `animations/Stand/Waiting/AirGuitar_1` |
| `air_juggle` | `animations/Stand/Waiting/AirJuggle_1` |
| `bandmaster` | `animations/Stand/Waiting/Bandmaster_1` |
| `drive_car` | `animations/Stand/Waiting/DriveCar_1` |
| `funny_slide` | `animations/Stand/Waiting/FunnySlide_1` |
| `happy_birthday` | `animations/Stand/Waiting/HappyBirthday_1` |
| `headbang` | `animations/Stand/Waiting/Headbang_1` |
| `helicopter` | `animations/Stand/Waiting/Helicopter_1` |
| `knight` | `animations/Stand/Waiting/Knight_1` |
| `kung_fu` | `animations/Stand/Waiting/KungFu_1` |
| `robot_dance` | `animations/Stand/Waiting/Robot_1` |
| `space_shuttle` | `animations/Stand/Waiting/SpaceShuttle_1` |
| `vacuum` | `animations/Stand/Waiting/Vacuum_1` |
| `walk_in_the_shit` | `animations/Stand/Waiting/WalkInTheShit_1` |
| `zombie` | `animations/Stand/Waiting/Zombie_1` |

**Fun / waiting:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `back_rubs` | `animations/Stand/Waiting/BackRubs_1` |
| `binoculars` | `animations/Stand/Waiting/Binoculars_1` |
| `call_someone` | `animations/Stand/Waiting/CallSomeone_1` |
| `drink_wait` | `animations/Stand/Waiting/Drink_1` |
| `fitness` | `animations/Stand/Waiting/Fitness_1` |
| `fitness_2` | `animations/Stand/Waiting/Fitness_2` |
| `fitness_3` | `animations/Stand/Waiting/Fitness_3` |
| `hide_eyes` | `animations/Stand/Waiting/HideEyes_1` |
| `hide_hands` | `animations/Stand/Waiting/HideHands_1` |
| `innocent_wait` | `animations/Stand/Waiting/Innocent_1` |
| `knock_eye` | `animations/Stand/Waiting/KnockEye_1` |
| `look_hand` | `animations/Stand/Waiting/LookHand_1` |
| `look_hand_2` | `animations/Stand/Waiting/LookHand_2` |
| `love_you` | `animations/Stand/Waiting/LoveYou_1` |
| `monster` | `animations/Stand/Waiting/Monster_1` |
| `mystical_power` | `animations/Stand/Waiting/MysticalPower_1` |
| `play_hands` | `animations/Stand/Waiting/PlayHands_1` |
| `play_hands_2` | `animations/Stand/Waiting/PlayHands_2` |
| `play_hands_3` | `animations/Stand/Waiting/PlayHands_3` |
| `relaxation` | `animations/Stand/Waiting/Relaxation_1` |
| `relaxation_2` | `animations/Stand/Waiting/Relaxation_2` |
| `relaxation_3` | `animations/Stand/Waiting/Relaxation_3` |
| `relaxation_4` | `animations/Stand/Waiting/Relaxation_4` |
| `rest` | `animations/Stand/Waiting/Rest_1` |
| `scratch_back` | `animations/Stand/Waiting/ScratchBack_1` |
| `scratch_bottom` | `animations/Stand/Waiting/ScratchBottom_1` |
| `scratch_eye` | `animations/Stand/Waiting/ScratchEye_1` |
| `scratch_hand` | `animations/Stand/Waiting/ScratchHand_1` |
| `scratch_head` | `animations/Stand/Waiting/ScratchHead_1` |
| `scratch_leg` | `animations/Stand/Waiting/ScratchLeg_1` |
| `scratch_torso` | `animations/Stand/Waiting/ScratchTorso_1` |
| `show_muscles` | `animations/Stand/Waiting/ShowMuscles_1` |
| `show_muscles_2` | `animations/Stand/Waiting/ShowMuscles_2` |
| `show_muscles_3` | `animations/Stand/Waiting/ShowMuscles_3` |
| `show_muscles_4` | `animations/Stand/Waiting/ShowMuscles_4` |
| `show_muscles_5` | `animations/Stand/Waiting/ShowMuscles_5` |
| `show_sky_wait` | `animations/Stand/Waiting/ShowSky_1` |
| `show_sky_wait_2` | `animations/Stand/Waiting/ShowSky_2` |
| `stretch_wait` | `animations/Stand/Waiting/Stretch_1` |
| `stretch_wait_2` | `animations/Stand/Waiting/Stretch_2` |
| `stretch_wait_3` | `animations/Stand/Waiting/Stretch_3` |
| `take_picture` | `animations/Stand/Waiting/TakePicture_1` |
| `taxi` | `animations/Stand/Waiting/Taxi_1` |
| `think` | `animations/Stand/Waiting/Think_1` |
| `think_2` | `animations/Stand/Waiting/Think_2` |
| `think_3` | `animations/Stand/Waiting/Think_3` |
| `think_4` | `animations/Stand/Waiting/Think_4` |
| `waddle` | `animations/Stand/Waiting/Waddle_1` |
| `waddle_2` | `animations/Stand/Waiting/Waddle_2` |
| `wake_up` | `animations/Stand/Waiting/WakeUp_1` |

**Positive emotions:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `amused` | `animations/Stand/Emotions/Positive/Amused_1` |
| `confident` | `animations/Stand/Emotions/Positive/Confident_1` |
| `ecstatic` | `animations/Stand/Emotions/Positive/Ecstatic_1` |
| `enthusiastic` | `animations/Stand/Emotions/Positive/Enthusiastic_1` |
| `excited_anim` | `animations/Stand/Emotions/Positive/Excited_1` |
| `excited_anim_2` | `animations/Stand/Emotions/Positive/Excited_2` |
| `excited_anim_3` | `animations/Stand/Emotions/Positive/Excited_3` |
| `happy_anim` | `animations/Stand/Emotions/Positive/Happy_1` |
| `happy_anim_2` | `animations/Stand/Emotions/Positive/Happy_2` |
| `happy_anim_3` | `animations/Stand/Emotions/Positive/Happy_3` |
| `happy_anim_4` | `animations/Stand/Emotions/Positive/Happy_4` |
| `hungry_anim` | `animations/Stand/Emotions/Positive/Hungry_1` |
| `hysterical` | `animations/Stand/Emotions/Positive/Hysterical_1` |
| `laugh_anim` | `animations/Stand/Emotions/Positive/Laugh_1` |
| `laugh_anim_2` | `animations/Stand/Emotions/Positive/Laugh_2` |
| `laugh_anim_3` | `animations/Stand/Emotions/Positive/Laugh_3` |
| `mocker` | `animations/Stand/Emotions/Positive/Mocker_1` |
| `optimistic` | `animations/Stand/Emotions/Positive/Optimistic_1` |
| `peaceful` | `animations/Stand/Emotions/Positive/Peaceful_1` |
| `proud` | `animations/Stand/Emotions/Positive/Proud_1` |
| `proud_2` | `animations/Stand/Emotions/Positive/Proud_2` |
| `proud_3` | `animations/Stand/Emotions/Positive/Proud_3` |
| `relieved` | `animations/Stand/Emotions/Positive/Relieved_1` |
| `shy_anim` | `animations/Stand/Emotions/Positive/Shy_1` |
| `shy_anim_2` | `animations/Stand/Emotions/Positive/Shy_2` |
| `sure` | `animations/Stand/Emotions/Positive/Sure_1` |
| `winner` | `animations/Stand/Emotions/Positive/Winner_1` |
| `winner_2` | `animations/Stand/Emotions/Positive/Winner_2` |

**Negative emotions:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `angry_anim` | `animations/Stand/Emotions/Negative/Angry_1` |
| `angry_anim_2` | `animations/Stand/Emotions/Negative/Angry_2` |
| `angry_anim_3` | `animations/Stand/Emotions/Negative/Angry_3` |
| `angry_anim_4` | `animations/Stand/Emotions/Negative/Angry_4` |
| `anxious` | `animations/Stand/Emotions/Negative/Anxious_1` |
| `bored_anim` | `animations/Stand/Emotions/Negative/Bored_1` |
| `bored_anim_2` | `animations/Stand/Emotions/Negative/Bored_2` |
| `disappointed` | `animations/Stand/Emotions/Negative/Disappointed_1` |
| `exhausted` | `animations/Stand/Emotions/Negative/Exhausted_1` |
| `exhausted_2` | `animations/Stand/Emotions/Negative/Exhausted_2` |
| `fear` | `animations/Stand/Emotions/Negative/Fear_1` |
| `fear_2` | `animations/Stand/Emotions/Negative/Fear_2` |
| `fearful` | `animations/Stand/Emotions/Negative/Fearful_1` |
| `frustrated` | `animations/Stand/Emotions/Negative/Frustrated_1` |
| `humiliated` | `animations/Stand/Emotions/Negative/Humiliated_1` |
| `hurt` | `animations/Stand/Emotions/Negative/Hurt_1` |
| `hurt_2` | `animations/Stand/Emotions/Negative/Hurt_2` |
| `late` | `animations/Stand/Emotions/Negative/Late_1` |
| `sad_anim` | `animations/Stand/Emotions/Negative/Sad_1` |
| `sad_anim_2` | `animations/Stand/Emotions/Negative/Sad_2` |
| `shocked` | `animations/Stand/Emotions/Negative/Shocked_1` |
| `sorry` | `animations/Stand/Emotions/Negative/Sorry_1` |
| `surprised_anim` | `animations/Stand/Emotions/Negative/Surprise_1` |
| `surprised_anim_2` | `animations/Stand/Emotions/Negative/Surprise_2` |
| `surprised_anim_3` | `animations/Stand/Emotions/Negative/Surprise_3` |

**Neutral emotions:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `alienated` | `animations/Stand/Emotions/Neutral/Alienated_1` |
| `annoyed` | `animations/Stand/Emotions/Neutral/Annoyed_1` |
| `ask_attention` | `animations/Stand/Emotions/Neutral/AskForAttention_1` |
| `ask_attention_2` | `animations/Stand/Emotions/Neutral/AskForAttention_2` |
| `ask_attention_3` | `animations/Stand/Emotions/Neutral/AskForAttention_3` |
| `cautious` | `animations/Stand/Emotions/Neutral/Cautious_1` |
| `confused_anim` | `animations/Stand/Emotions/Neutral/Confused_1` |
| `determined` | `animations/Stand/Emotions/Neutral/Determined_1` |
| `embarrassed` | `animations/Stand/Emotions/Neutral/Embarrassed_1` |
| `hello_anim` | `animations/Stand/Emotions/Neutral/Hello_1` |
| `hesitation` | `animations/Stand/Emotions/Neutral/Hesitation_1` |
| `innocent_anim` | `animations/Stand/Emotions/Neutral/Innocent_1` |
| `lonely` | `animations/Stand/Emotions/Neutral/Lonely_1` |
| `mischievous` | `animations/Stand/Emotions/Neutral/Mischievous_1` |
| `puzzled` | `animations/Stand/Emotions/Neutral/Puzzled_1` |
| `sneeze_anim` | `animations/Stand/Emotions/Neutral/Sneeze` |
| `stubborn` | `animations/Stand/Emotions/Neutral/Stubborn_1` |
| `suspicious` | `animations/Stand/Emotions/Neutral/Suspicious_1` |

**Gestures:**

| `motion_name` | Behavior path |
|---------------|---------------|
| `angry_gesture` | `animations/Stand/Gestures/Angry_1` |
| `angry_gesture_2` | `animations/Stand/Gestures/Angry_2` |
| `angry_gesture_3` | `animations/Stand/Gestures/Angry_3` |
| `applause` | `animations/Stand/Gestures/Applause_1` |
| `bow` | `animations/Stand/Gestures/BowShort_1` |
| `but` | `animations/Stand/Gestures/But_1` |
| `calm_down` | `animations/Stand/Gestures/CalmDown_1` |
| `calm_down_2` | `animations/Stand/Gestures/CalmDown_2` |
| `calm_down_3` | `animations/Stand/Gestures/CalmDown_3` |
| `calm_down_4` | `animations/Stand/Gestures/CalmDown_4` |
| `calm_down_5` | `animations/Stand/Gestures/CalmDown_5` |
| `calm_down_6` | `animations/Stand/Gestures/CalmDown_6` |
| `caress` | `animations/Stand/Gestures/Caress_1` |
| `caress_2` | `animations/Stand/Gestures/Caress_2` |
| `catch_fly` | `animations/Stand/Gestures/CatchFly_1` |
| `catch_fly_2` | `animations/Stand/Gestures/CatchFly_2` |
| `choice` | `animations/Stand/Gestures/Choice_1` |
| `choice_2` | `animations/Stand/Gestures/Choice_2` |
| `claw` | `animations/Stand/Gestures/Claw_1` |
| `claw_2` | `animations/Stand/Gestures/Claw_2` |
| `coaxing` | `animations/Stand/Gestures/Coaxing_1` |
| `coaxing_2` | `animations/Stand/Gestures/Coaxing_2` |
| `come_on` | `animations/Stand/Gestures/ComeOn_1` |
| `confused_gesture` | `animations/Stand/Gestures/Confused_1` |
| `confused_gesture_2` | `animations/Stand/Gestures/Confused_2` |
| `count_one` | `animations/Stand/Gestures/CountOne_1` |
| `count_one_2` | `animations/Stand/Gestures/CountOne_2` |
| `count_two` | `animations/Stand/Gestures/CountTwo_1` |
| `count_two_2` | `animations/Stand/Gestures/CountTwo_2` |
| `count_three` | `animations/Stand/Gestures/CountThree_1` |
| `count_three_2` | `animations/Stand/Gestures/CountThree_2` |
| `count_four` | `animations/Stand/Gestures/CountFour_1` |
| `count_four_2` | `animations/Stand/Gestures/CountFour_2` |
| `count_five` | `animations/Stand/Gestures/CountFive_1` |
| `count_five_2` | `animations/Stand/Gestures/CountFive_2` |
| `count_more` | `animations/Stand/Gestures/CountMore_1` |
| `count_more_2` | `animations/Stand/Gestures/CountMore_2` |
| `desperate` | `animations/Stand/Gestures/Desperate_1` |
| `desperate_2` | `animations/Stand/Gestures/Desperate_2` |
| `desperate_3` | `animations/Stand/Gestures/Desperate_3` |
| `desperate_4` | `animations/Stand/Gestures/Desperate_4` |
| `desperate_5` | `animations/Stand/Gestures/Desperate_5` |
| `enthusiastic_g` | `animations/Stand/Gestures/Enthusiastic_1` |
| `enthusiastic_g2` | `animations/Stand/Gestures/Enthusiastic_2` |
| `enthusiastic_g3` | `animations/Stand/Gestures/Enthusiastic_3` |
| `enthusiastic_g4` | `animations/Stand/Gestures/Enthusiastic_4` |
| `enthusiastic_g5` | `animations/Stand/Gestures/Enthusiastic_5` |
| `everything` | `animations/Stand/Gestures/Everything_1` |
| `everything_2` | `animations/Stand/Gestures/Everything_2` |
| `everything_3` | `animations/Stand/Gestures/Everything_3` |
| `everything_4` | `animations/Stand/Gestures/Everything_4` |
| `everything_5` | `animations/Stand/Gestures/Everything_5` |
| `everything_6` | `animations/Stand/Gestures/Everything_6` |
| `excited_gesture` | `animations/Stand/Gestures/Excited_1` |
| `explain` | `animations/Stand/Gestures/Explain_1` |
| `explain_2` | `animations/Stand/Gestures/Explain_2` |
| `explain_3` | `animations/Stand/Gestures/Explain_3` |
| `explain_4` | `animations/Stand/Gestures/Explain_4` |
| `explain_5` | `animations/Stand/Gestures/Explain_5` |
| `explain_6` | `animations/Stand/Gestures/Explain_6` |
| `explain_7` | `animations/Stand/Gestures/Explain_7` |
| `explain_8` | `animations/Stand/Gestures/Explain_8` |
| `explain_9` | `animations/Stand/Gestures/Explain_9` |
| `explain_10` | `animations/Stand/Gestures/Explain_10` |
| `explain_11` | `animations/Stand/Gestures/Explain_11` |
| `far` | `animations/Stand/Gestures/Far_1` |
| `far_2` | `animations/Stand/Gestures/Far_2` |
| `far_3` | `animations/Stand/Gestures/Far_3` |
| `follow` | `animations/Stand/Gestures/Follow_1` |
| `freeze` | `animations/Stand/Gestures/Freeze_1` |
| `give` | `animations/Stand/Gestures/Give_1` |
| `give_2` | `animations/Stand/Gestures/Give_2` |
| `give_3` | `animations/Stand/Gestures/Give_3` |
| `give_4` | `animations/Stand/Gestures/Give_4` |
| `give_5` | `animations/Stand/Gestures/Give_5` |
| `give_6` | `animations/Stand/Gestures/Give_6` |
| `great` | `animations/Stand/Gestures/Great_1` |
| `he_says` | `animations/Stand/Gestures/HeSays_1` |
| `he_says_2` | `animations/Stand/Gestures/HeSays_2` |
| `he_says_3` | `animations/Stand/Gestures/HeSays_3` |
| `hey` | `animations/Stand/Gestures/Hey_1` |
| `hey_2` | `animations/Stand/Gestures/Hey_2` |
| `hey_3` | `animations/Stand/Gestures/Hey_3` |
| `hey_4` | `animations/Stand/Gestures/Hey_4` |
| `hey_5` | `animations/Stand/Gestures/Hey_5` |
| `hey_6` | `animations/Stand/Gestures/Hey_6` |
| `hey_7` | `animations/Stand/Gestures/Hey_7` |
| `hide` | `animations/Stand/Gestures/Hide_1` |
| `hungry_gesture` | `animations/Stand/Gestures/Hungry_1` |
| `i_dont_know` | `animations/Stand/Gestures/IDontKnow_1` |
| `i_dont_know_2` | `animations/Stand/Gestures/IDontKnow_2` |
| `i_dont_know_3` | `animations/Stand/Gestures/IDontKnow_3` |
| `i_dont_know_4` | `animations/Stand/Gestures/IDontKnow_4` |
| `i_dont_know_5` | `animations/Stand/Gestures/IDontKnow_5` |
| `i_dont_know_6` | `animations/Stand/Gestures/IDontKnow_6` |
| `joint_hands` | `animations/Stand/Gestures/JointHands_1` |
| `joint_hands_2` | `animations/Stand/Gestures/JointHands_2` |
| `joint_hands_3` | `animations/Stand/Gestures/JointHands_3` |
| `joy_anim` | `animations/Stand/Gestures/Joy_1` |
| `kisses` | `animations/Stand/Gestures/Kisses_1` |
| `look` | `animations/Stand/Gestures/Look_1` |
| `look_2` | `animations/Stand/Gestures/Look_2` |
| `maybe` | `animations/Stand/Gestures/Maybe_1` |
| `me` | `animations/Stand/Gestures/Me_1` |
| `me_2` | `animations/Stand/Gestures/Me_2` |
| `me_3` | `animations/Stand/Gestures/Me_3` |
| `me_4` | `animations/Stand/Gestures/Me_4` |
| `me_5` | `animations/Stand/Gestures/Me_5` |
| `me_6` | `animations/Stand/Gestures/Me_6` |
| `me_7` | `animations/Stand/Gestures/Me_7` |
| `me_8` | `animations/Stand/Gestures/Me_8` |
| `mime` | `animations/Stand/Gestures/Mime_1` |
| `mime_2` | `animations/Stand/Gestures/Mime_2` |
| `next` | `animations/Stand/Gestures/Next_1` |
| `no_gesture` | `animations/Stand/Gestures/No_1` |
| `no_gesture_2` | `animations/Stand/Gestures/No_2` |
| `no_gesture_3` | `animations/Stand/Gestures/No_3` |
| `no_gesture_4` | `animations/Stand/Gestures/No_4` |
| `no_gesture_5` | `animations/Stand/Gestures/No_5` |
| `no_gesture_6` | `animations/Stand/Gestures/No_6` |
| `no_gesture_7` | `animations/Stand/Gestures/No_7` |
| `no_gesture_8` | `animations/Stand/Gestures/No_8` |
| `no_gesture_9` | `animations/Stand/Gestures/No_9` |
| `nothing` | `animations/Stand/Gestures/Nothing_1` |
| `nothing_2` | `animations/Stand/Gestures/Nothing_2` |
| `on_the_evening` | `animations/Stand/Gestures/OnTheEvening_1` |
| `on_the_evening_2` | `animations/Stand/Gestures/OnTheEvening_2` |
| `on_the_evening_3` | `animations/Stand/Gestures/OnTheEvening_3` |
| `on_the_evening_4` | `animations/Stand/Gestures/OnTheEvening_4` |
| `on_the_evening_5` | `animations/Stand/Gestures/OnTheEvening_5` |
| `please` | `animations/Stand/Gestures/Please_1` |
| `please_2` | `animations/Stand/Gestures/Please_2` |
| `please_3` | `animations/Stand/Gestures/Please_3` |
| `reject` | `animations/Stand/Gestures/Reject_1` |
| `reject_2` | `animations/Stand/Gestures/Reject_2` |
| `reject_3` | `animations/Stand/Gestures/Reject_3` |
| `reject_4` | `animations/Stand/Gestures/Reject_4` |
| `reject_5` | `animations/Stand/Gestures/Reject_5` |
| `reject_6` | `animations/Stand/Gestures/Reject_6` |
| `salute_anim` | `animations/Stand/Gestures/Salute_1` |
| `salute_anim_2` | `animations/Stand/Gestures/Salute_2` |
| `salute_anim_3` | `animations/Stand/Gestures/Salute_3` |
| `shoot` | `animations/Stand/Gestures/Shoot_1` |
| `show_floor` | `animations/Stand/Gestures/ShowFloor_1` |
| `show_floor_2` | `animations/Stand/Gestures/ShowFloor_2` |
| `show_floor_3` | `animations/Stand/Gestures/ShowFloor_3` |
| `show_floor_4` | `animations/Stand/Gestures/ShowFloor_4` |
| `show_floor_5` | `animations/Stand/Gestures/ShowFloor_5` |
| `show_sky` | `animations/Stand/Gestures/ShowSky_1` |
| `show_sky_2` | `animations/Stand/Gestures/ShowSky_2` |
| `show_sky_3` | `animations/Stand/Gestures/ShowSky_3` |
| `show_sky_4` | `animations/Stand/Gestures/ShowSky_4` |
| `show_sky_5` | `animations/Stand/Gestures/ShowSky_5` |
| `show_sky_6` | `animations/Stand/Gestures/ShowSky_6` |
| `show_sky_7` | `animations/Stand/Gestures/ShowSky_7` |
| `show_sky_8` | `animations/Stand/Gestures/ShowSky_8` |
| `show_sky_9` | `animations/Stand/Gestures/ShowSky_9` |
| `show_sky_10` | `animations/Stand/Gestures/ShowSky_10` |
| `show_sky_11` | `animations/Stand/Gestures/ShowSky_11` |
| `show_sky_12` | `animations/Stand/Gestures/ShowSky_12` |
| `shy_gesture` | `animations/Stand/Gestures/Shy_1` |
| `stretch_gesture` | `animations/Stand/Gestures/Stretch_1` |
| `stretch_gesture_2` | `animations/Stand/Gestures/Stretch_2` |
| `surprised_gesture` | `animations/Stand/Gestures/Surprised_1` |
| `take` | `animations/Stand/Gestures/Take_1` |
| `thinking_anim` | `animations/Stand/Gestures/Thinking_1` |
| `thinking_anim_2` | `animations/Stand/Gestures/Thinking_2` |
| `thinking_anim_3` | `animations/Stand/Gestures/Thinking_3` |
| `thinking_anim_4` | `animations/Stand/Gestures/Thinking_4` |
| `thinking_anim_5` | `animations/Stand/Gestures/Thinking_5` |
| `thinking_anim_6` | `animations/Stand/Gestures/Thinking_6` |
| `thinking_anim_7` | `animations/Stand/Gestures/Thinking_7` |
| `thinking_anim_8` | `animations/Stand/Gestures/Thinking_8` |
| `this` | `animations/Stand/Gestures/This_1` |
| `this_2` | `animations/Stand/Gestures/This_2` |
| `this_3` | `animations/Stand/Gestures/This_3` |
| `this_4` | `animations/Stand/Gestures/This_4` |
| `this_5` | `animations/Stand/Gestures/This_5` |
| `this_6` | `animations/Stand/Gestures/This_6` |
| `this_7` | `animations/Stand/Gestures/This_7` |
| `this_8` | `animations/Stand/Gestures/This_8` |
| `this_9` | `animations/Stand/Gestures/This_9` |
| `this_10` | `animations/Stand/Gestures/This_10` |
| `this_11` | `animations/Stand/Gestures/This_11` |
| `this_12` | `animations/Stand/Gestures/This_12` |
| `this_13` | `animations/Stand/Gestures/This_13` |
| `this_14` | `animations/Stand/Gestures/This_14` |
| `this_15` | `animations/Stand/Gestures/This_15` |
| `whats_this` | `animations/Stand/Gestures/WhatSThis_1` |
| `whats_this_2` | `animations/Stand/Gestures/WhatSThis_2` |
| `whats_this_3` | `animations/Stand/Gestures/WhatSThis_3` |
| `whats_this_4` | `animations/Stand/Gestures/WhatSThis_4` |
| `whats_this_5` | `animations/Stand/Gestures/WhatSThis_5` |
| `whats_this_6` | `animations/Stand/Gestures/WhatSThis_6` |
| `whats_this_7` | `animations/Stand/Gestures/WhatSThis_7` |
| `whats_this_8` | `animations/Stand/Gestures/WhatSThis_8` |
| `whats_this_9` | `animations/Stand/Gestures/WhatSThis_9` |
| `whats_this_10` | `animations/Stand/Gestures/WhatSThis_10` |
| `whats_this_11` | `animations/Stand/Gestures/WhatSThis_11` |
| `whats_this_12` | `animations/Stand/Gestures/WhatSThis_12` |
| `whats_this_13` | `animations/Stand/Gestures/WhatSThis_13` |
| `whats_this_14` | `animations/Stand/Gestures/WhatSThis_14` |
| `whats_this_15` | `animations/Stand/Gestures/WhatSThis_15` |
| `whats_this_16` | `animations/Stand/Gestures/WhatSThis_16` |
| `wings` | `animations/Stand/Gestures/Wings_1` |
| `wings_2` | `animations/Stand/Gestures/Wings_2` |
| `wings_3` | `animations/Stand/Gestures/Wings_3` |
| `wings_4` | `animations/Stand/Gestures/Wings_4` |
| `wings_5` | `animations/Stand/Gestures/Wings_5` |
| `yes_anim` | `animations/Stand/Gestures/Yes_1` |
| `yes_anim_2` | `animations/Stand/Gestures/Yes_2` |
| `yes_anim_3` | `animations/Stand/Gestures/Yes_3` |
| `you` | `animations/Stand/Gestures/You_1` |
| `you_2` | `animations/Stand/Gestures/You_2` |
| `you_3` | `animations/Stand/Gestures/You_3` |
| `you_4` | `animations/Stand/Gestures/You_4` |
| `you_5` | `animations/Stand/Gestures/You_5` |
| `you_know_what` | `animations/Stand/Gestures/YouKnowWhat_1` |
| `you_know_what_2` | `animations/Stand/Gestures/YouKnowWhat_2` |
| `you_know_what_3` | `animations/Stand/Gestures/YouKnowWhat_3` |
| `you_know_what_4` | `animations/Stand/Gestures/YouKnowWhat_4` |
| `you_know_what_5` | `animations/Stand/Gestures/YouKnowWhat_5` |
| `you_know_what_6` | `animations/Stand/Gestures/YouKnowWhat_6` |
| `yum` | `animations/Stand/Gestures/Yum_1` |

**Body language (speaking / listening / thinking):**

| `motion_name` | Behavior path |
|---------------|---------------|
| `bodytalk_1` | `animations/Stand/BodyTalk/Speaking/BodyTalk_1` |
| `bodytalk_2` | `animations/Stand/BodyTalk/Speaking/BodyTalk_2` |
| `bodytalk_3` | `animations/Stand/BodyTalk/Speaking/BodyTalk_3` |
| `bodytalk_4` | `animations/Stand/BodyTalk/Speaking/BodyTalk_4` |
| `bodytalk_5` | `animations/Stand/BodyTalk/Speaking/BodyTalk_5` |
| `bodytalk_6` | `animations/Stand/BodyTalk/Speaking/BodyTalk_6` |
| `bodytalk_7` | `animations/Stand/BodyTalk/Speaking/BodyTalk_7` |
| `bodytalk_8` | `animations/Stand/BodyTalk/Speaking/BodyTalk_8` |
| `bodytalk_9` | `animations/Stand/BodyTalk/Speaking/BodyTalk_9` |
| `bodytalk_10` | `animations/Stand/BodyTalk/Speaking/BodyTalk_10` |
| `bodytalk_11` | `animations/Stand/BodyTalk/Speaking/BodyTalk_11` |
| `bodytalk_12` | `animations/Stand/BodyTalk/Speaking/BodyTalk_12` |
| `bodytalk_13` | `animations/Stand/BodyTalk/Speaking/BodyTalk_13` |
| `bodytalk_14` | `animations/Stand/BodyTalk/Speaking/BodyTalk_14` |
| `bodytalk_15` | `animations/Stand/BodyTalk/Speaking/BodyTalk_15` |
| `bodytalk_16` | `animations/Stand/BodyTalk/Speaking/BodyTalk_16` |
| `bodytalk_17` | `animations/Stand/BodyTalk/Speaking/BodyTalk_17` |
| `bodytalk_18` | `animations/Stand/BodyTalk/Speaking/BodyTalk_18` |
| `bodytalk_19` | `animations/Stand/BodyTalk/Speaking/BodyTalk_19` |
| `bodytalk_20` | `animations/Stand/BodyTalk/Speaking/BodyTalk_20` |
| `bodytalk_21` | `animations/Stand/BodyTalk/Speaking/BodyTalk_21` |
| `bodytalk_22` | `animations/Stand/BodyTalk/Speaking/BodyTalk_22` |
| `listening_anim` | `animations/Stand/BodyTalk/Listening/Listening_2` |
| `listening_left` | `animations/Stand/BodyTalk/Listening/ListeningLeft_1` |
| `listening_right` | `animations/Stand/BodyTalk/Listening/ListeningRight_1` |
| `remember` | `animations/Stand/BodyTalk/Thinking/Remember_1` |
| `remember_2` | `animations/Stand/BodyTalk/Thinking/Remember_2` |
| `remember_3` | `animations/Stand/BodyTalk/Thinking/Remember_3` |
| `thinking_loop` | `animations/Stand/BodyTalk/Thinking/ThinkingLoop_1` |
| `thinking_loop_2` | `animations/Stand/BodyTalk/Thinking/ThinkingLoop_2` |

### Motions (QTrobot)

`motion_name` is the gesture name from the robot's animation library, called via `/qt_robot/gesture/play` service.

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'QT/emotions/happy'}"
```

| Category | Names |
|----------|-------|
| Emotions | `QT/emotions/happy`, `QT/emotions/sad`, `QT/emotions/angry`, `QT/emotions/surprised`, `QT/emotions/disgusted`, `QT/emotions/calm`, `QT/emotions/afraid`, `QT/emotions/shy`, `QT/emotions/neutral` |
| Greetings | `hi`, `bye`, `bye-bye`, `adieu`, `send_kiss`, `hug`, `kiss`, `hoora` |
| Head | `nodding-yes`, `yes`, `no`, `head-right-left`, `head_scratch`, `sneezing` |
| Arms/Body | `clapping`, `handclap`, `hands-up`, `hands-side`, `hands-on-hip`, `hands-on-head`, `hands-on-belly`, `one-arm-up`, `show_left`, `show_right`, `point_front`, `up_left`, `up_right`, `hips`, `stretch` |
| Expressions | `curious`, `come`, `strong`, `thanks`, `so`, `ohno`, `so_what`, `laugh`, `peekaboo`, `monkey`, `drink`, `challenge`, `protect` |
| Dance | `Dance`, `Dance-1-1` … `Dance-4-6` |

### Custom Gestures (QTrobot)

Gestures that are not available in the QTrobot animation library are implemented as **joint-keyframe sequences** executed via direct position topics (`/qt_robot/{head,left_arm,right_arm}_position/command`). These run in a daemon thread and interoperate with the same `motion_name` vocabulary as NAO.

| `motion_name` | Description |
|---------------|-------------|
| `fly` / `helicopter` / `air_juggle` / `catch_fly` / `catch_fly_2` | Arms spread wide, flapping motion |
| `drive` / `driving` / `drive_car` | Steering wheel hold with alternating lean |
| `beep` / `beeping` | Quick head dips (beep acknowledgement) |
| `phone_call` / `call_someone` | Right arm raised to ear, head nod |
| `show_face` | Both arms raised framing the face |
| `pretend_play` | Arms open, head turns side to side |

To add a new custom gesture, append to `QT_CUSTOM_GESTURES` in `qt_bridge.py`:

```python
QT_CUSTOM_GESTURES["my_gesture"] = [
    ({"LeftShoulderPitch": -0.8, "RightShoulderPitch": -0.8}, 0.5),  # hold 0.5 s
    ({"HeadYaw": 0.4}, 0.3),
    (_QT_HOME, 0.4),  # return to neutral
]
```

Each step is a `(joint_dict, hold_seconds)` tuple. Joint names use QTrobot convention (`LeftShoulderPitch`, `HeadYaw`, etc.). Joints not listed in a step are unchanged.

### Raw joint control (NAO / Pepper)

Format: `Joint:angle` or `Joint:angle,Joint:angle,...` — angles in **radians**.

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'HeadYaw:0.5', speed: 0.5}"

ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'move', motion_name: 'LHand:1.0', speed: 0.5}"
```

Common joints and neutral values:

| Joint | Neutral | Range |
|-------|---------|-------|
| `HeadYaw` | 0.0 | ±2.0 rad |
| `HeadPitch` | -0.18 | -0.67 to 0.51 rad |
| `LShoulderPitch` / `RShoulderPitch` | 1.47 | ±2.09 rad |
| `LShoulderRoll` | 0.21 | -0.31 to 1.33 rad |
| `RShoulderRoll` | -0.21 | -1.33 to 0.31 rad |
| `LElbowRoll` | -0.42 | -1.54 to -0.03 rad |
| `RElbowRoll` | 0.42 | 0.03 to 1.54 rad |
| `LElbowYaw` / `RElbowYaw` | ∓1.21 | ±2.09 rad |
| `LWristYaw` / `RWristYaw` | 0.0 | ±1.82 rad |
| `LHand` / `RHand` | 0.3 | 0.0 (closed) – 1.0 (open) |

---

## display

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'display', emotion: 'happy', duration_ms: 3000}"
```

**Emotion → LED color:**

| `emotion` | Color | NAO LEDs | Pepper LEDs |
|-----------|-------|----------|-------------|
| `happy` | Yellow | Face + Chest | Face + Shoulder |
| `sad` | Blue | Face + Chest | Face + Shoulder |
| `angry` | Red | Face + Chest | Face + Shoulder |
| `neutral` | White | Face + Chest | Face + Shoulder |
| `surprised` | Cyan | Face + Chest | Face + Shoulder |
| `scared` | Purple | Face + Chest | Face + Shoulder |
| `excited` | Orange | Face + Chest | Face + Shoulder |

**Direct LED color control:**

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'display', led_name: 'eyes', color: 'red', duration_ms: 2000}"

ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'display', led_name: 'left_eye', color: '#FF8800', duration_ms: 1000}"
```

**NAO LED groups:**

| `led_name` | NAOqi group |
|------------|-------------|
| `eyes` | FaceLeds |
| `left_eye` | LeftFaceLeds |
| `right_eye` | RightFaceLeds |
| `ears` | EarLeds |
| `left_ear` | LeftEarLeds |
| `right_ear` | RightEarLeds |
| `chest` | ChestLeds |
| `feet` | FeetLeds |
| `head` | BrainLeds |
| `all` | AllLeds |

**Pepper LED groups:**

| `led_name` | NAOqi group |
|------------|-------------|
| `eyes` | FaceLeds |
| `left_eye` | LeftFaceLeds |
| `right_eye` | RightFaceLeds |
| `chest` | ChestLeds |
| `shoulder` | ShoulderLeds |
| `left_shoulder` | LeftShoulderLeds |
| `right_shoulder` | RightShoulderLeds |
| `all` | AllLeds |

**Named colors:** `red`, `green`, `blue`, `white`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `pink`, `off` — or any `#RRGGBB` hex value.

**QTrobot:** calls `/qt_robot/emotion/show` service with `QT/emotions/<emotion>`.

**Image display (QTrobot only):**
```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'display', image_path: '/path/to/image.png', duration_ms: 3000}"
```

---

## volume

Set the robot's audio output volume.

```bash
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'volume', speed: 0.6}"
```

`speed` is the target level in the `0.0`–`1.0` range (e.g. `0.5` = 50 %).

**NAO / Pepper:** calls `ALAudioDevice.setOutputVolume(0–100)` via qi.  
**QTrobot:** not implemented — command is silently skipped and logged.

The **Macros** tab in the WOZ interface exposes two circular buttons (**+** / **−**) above the left joystick. Each press adjusts the volume by ±10 percentage points (clamped to 0–100). The current level is tracked client-side starting at 50 % and is not displayed.

---

## relax / stiffen

Set joint stiffness to 0 (limp) or 1 (rigid). Use `motion_name` to specify which body part.

```bash
# Relax the whole body
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'relax', motion_name: 'body'}"

# Relax left arm but keep the hand stiff
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'relax', motion_name: 'larm_no_hand'}"

# Stiffen back up
ros2 topic pub --once /robot_cmd ros2_robot_bridge/msg/RobotCmd \
    "{action: 'stiffen', motion_name: 'body'}"
```

| `motion_name` | Joints affected |
|---------------|-----------------|
| `body` | Whole body |
| `head` | Head |
| `larm` / `left_arm` | Left arm + hand |
| `rarm` / `right_arm` | Right arm + hand |
| `arms` | Both arms + hands |
| `larm_no_hand` / `left_arm_no_hand` | Left shoulder + elbow + wrist (no hand) |
| `rarm_no_hand` / `right_arm_no_hand` | Right shoulder + elbow + wrist (no hand) |
| `arms_no_hand` | Both arms without hands |
| `lhand` / `left_hand` | Left hand only |
| `rhand` / `right_hand` | Right hand only |
| `lleg` / `left_leg` | Left leg |
| `rleg` / `right_leg` | Right leg |
| `legs` | Both legs |

---

## Sensor Topics (QTrobot)

`qt_sensor` bridges QTrobot's ROS1 sensor topics into ROS2. All topics are relative to the node namespace (e.g. `qtrobot_1` for IP `…1`).

```bash
ros2 topic echo /qtrobot_1/joint_states   # arm and head joint positions (radians)
ros2 topic echo /qtrobot_1/motor_states   # raw motor state JSON (torque, temperature, errors)
```

| Topic | Type | Description |
|-------|------|-------------|
| `joint_states` | `sensor_msgs/JointState` | Joint positions (radians), republished from `/qt_robot/joints/state` |
| `motor_states` | `std_msgs/String` | Raw motor state as JSON string, from `/qt_robot/motors/states` |

> The `sensor_hz` launch argument caps the joint-state republish rate (default 10 Hz). The robot publishes at ~2 Hz, so any value above 2 effectively forwards all messages.

---

## NAO / Pepper robot administration

### Check installed behaviors
```bash
qicli call ALBehaviorManager.getInstalledBehaviors
```

### Change the robot name
```bash
python3 -c "
import qi
s = qi.Session()
s.connect('tcp://<ROBOT_IP>:9559')
system = s.service('ALSystem')
print('Current name:', system.robotName())
system.setRobotName('new_name')
"
```

### Check NAOqi version
```bash
ssh nao@<NAO_IP> "naoqi --version 2>/dev/null | head -3"
```

---

## Topics Reference

| Topic | Type | Description |
|-------|------|-------------|
| `/robot_cmd` | `RobotCmd` | **Entry point** — send all commands here |
| `/robot_cmd_validated` | `RobotCmd` | Internal — validated commands to bridges |
| `/robot_config` | `RobotConfig` | Active robot type/version (TRANSIENT_LOCAL) |
| `nao_reconnect` | `std_msgs/String` | Internal — woz_node publishes `naoqi_host:<ip>` to reconnect nao_bridge at runtime without restarting |
| `robot_reconfig` | `std_msgs/String` | Internal — woz_node publishes `robot_type:robot_version` to update robot_detector at runtime |
| `/speech` | `std_msgs/String` | NAO/Pepper speech fallback (when qi not available) |
| `/joint_angles` | `JointAnglesWithSpeed` | NAO/Pepper joint fallback (when qi not available) |
| `/cmd_vel` | `geometry_msgs/Twist` | Walking fallback (when qi not available) |

> **Note:** `nao_reconnect` and `robot_reconfig` are retained for backwards compatibility with single-robot setups. In multi-robot WOZ mode, each `_RobotSlot` manages its own qi session directly — robot switching is handled by adding/removing slots on the `/robots` page rather than by republishing these topics.

---

## Sensor Topics (NAO / Pepper)

`nao_sensors` publishes live sensor data. All topics are relative to the node namespace, which is `{robot_type}_{last_ip_octet}` (e.g. `nao_46` for IP `192.168.24.46`).

### List all sensor topics
```bash
ros2 topic list | grep -E "sensor|sonar|battery|audio"
```

### Touch buttons
```bash
ros2 topic echo /nao_46/sensor/chest          # chest button
ros2 topic echo /nao_46/sensor/head_front
ros2 topic echo /nao_46/sensor/head_middle
ros2 topic echo /nao_46/sensor/head_rear
ros2 topic echo /nao_46/sensor/bumper_left    # left foot bumper (NAO) / front-left base (Pepper)
ros2 topic echo /nao_46/sensor/bumper_right
ros2 topic echo /pepper_11/sensor/bumper_back # Pepper only — rear base bumper
```

### Sonar (ultrasonic distance)
```bash
ros2 topic echo /nao_46/sonar/left            # metres, 0 = no echo
ros2 topic echo /nao_46/sonar/right
```

### Battery
```bash
ros2 topic echo /nao_46/battery               # 0.0 (empty) to 1.0 (full)
```

### Audio
```bash
ros2 topic echo /nao_46/audio/sound_detected          # True while sound is detected
ros2 topic echo /nao_46/audio/localization/azimuth    # horizontal angle (rad), 0 = front
ros2 topic echo /nao_46/audio/localization/elevation  # vertical angle (rad), 0 = horizontal
ros2 topic echo /nao_46/audio/localization/confidence # 0.0 to 1.0
```

### Sensor topics reference

| Topic | Type | Description |
|-------|------|-------------|
| `sensor/chest` | `std_msgs/Bool` | Chest button pressed |
| `sensor/head_front` | `std_msgs/Bool` | Head touch — front zone |
| `sensor/head_middle` | `std_msgs/Bool` | Head touch — middle zone |
| `sensor/head_rear` | `std_msgs/Bool` | Head touch — rear zone |
| `sensor/bumper_left` | `std_msgs/Bool` | Left foot bumper (NAO) / front-left base bumper (Pepper) |
| `sensor/bumper_right` | `std_msgs/Bool` | Right foot bumper (NAO) / front-right base bumper (Pepper) |
| `sensor/bumper_back` | `std_msgs/Bool` | **Pepper only** — rear base bumper |
| `sonar/left` | `std_msgs/Float32` | Left ultrasonic distance (m), 0 = no echo |
| `sonar/right` | `std_msgs/Float32` | Right ultrasonic distance (m), 0 = no echo |
| `battery` | `std_msgs/Float32` | Battery charge 0.0–1.0 |
| `audio/sound_detected` | `std_msgs/Bool` | True while a sound is above the detection threshold |
| `audio/localization/azimuth` | `std_msgs/Float32` | Sound azimuth (rad), 0 = front, positive = robot's left |
| `audio/localization/elevation` | `std_msgs/Float32` | Sound elevation (rad), 0 = horizontal, positive = above |
| `audio/localization/confidence` | `std_msgs/Float32` | Localization confidence 0.0–1.0 |

> **Namespace:** replace `nao_46` with your actual namespace (`{robot_type}_{last_ip_octet}`).  
> **Poll rate:** 20 Hz by default; set `sensor_poll_hz` in the launch command to change it.  
> **Sound sensitivity:** set `sound_sensitivity` (0.0–1.0) in the launch command to tune the detection threshold.

---

## Custom Messages

### RobotCmd.msg
```
string action        # speak | move | display | relax | stiffen | volume
string text
string language
string motion_name
float32 speed
string emotion
string led_name
string color
string image_path
int32 duration_ms
```

### RobotConfig.msg
```
string robot_type      # nao | pepper | qtrobot
string robot_version   # v5|v6 (NAO) · v1|v1.8|v2 (Pepper) · qt1|qt2 (QTrobot)
bool is_ready
string status_msg
```

---

## Adding a new bridge

To add support for a new robot, complete the following steps.

### 1. Copy the template

```bash
cp src/ros2_robot_bridge/ros2_robot_bridge/robot_bridge_template.py \
   src/ros2_robot_bridge/ros2_robot_bridge/my_robot_bridge.py
```

`robot_bridge_template.py` is a fully documented starting point. It contains:
- The complete universal motion vocabulary in `MOTION_MAP` (all `None` by default — fill in your robot's names)
- Commented examples for `LED_GROUPS`, `LED_COLOR_NAMES`, `BEHAVIORS`, and `LANGUAGE_MAP`
- Documented method stubs for every interface point with the correct resolution order
- An AI assistant prompt at the end of the file (see below)

### 2. Implement the adapter

| Item | What to do |
|------|-----------|
| `SUPPORTED_TYPES` | Set to the `robot_type` string(s) this bridge handles |
| `MOTION_MAP` | Map each universal motion name to the robot's equivalent, or `None` to skip |
| `EMOTION_MAP` | Map each universal emotion name to the robot's equivalent |
| `LED_GROUPS` | Uncomment and fill in if the robot has addressable LEDs |
| `BEHAVIORS` | Uncomment and fill in if the robot has a named behavior / animation library |
| `connect()` | Open the SDK connection (runs in a background thread — blocking is safe) |
| `disconnect()` | Close the connection cleanly |
| `_on_activate()` | Read ROS2 parameters declared in `__init__` |
| `_on_deactivate()` | Set all SDK handles to `None` |
| `do_speak()` | Send text to the robot's TTS API |
| `do_move()` | Resolve the motion name and send to the robot |
| `do_display()` | Handle LED, image, and emotion display in that priority order |

### 3. Register the robot type

In `robot_detector.py`, add an entry to `VALID_VERSIONS`:

```python
VALID_VERSIONS = {
    # existing entries ...
    "my_robot": ("v1", "v2"),
}
```

### 4. Add to the launch file

In `launch/robot_bridge.launch.py`, declare the node alongside the existing bridges:

```python
Node(
    package="ros2_robot_bridge",
    executable="my_robot_bridge.py",
    name="my_robot_bridge",
    parameters=[{
        "my_robot_host": LaunchConfiguration("my_robot_host"),
        "my_robot_port": LaunchConfiguration("my_robot_port"),
    }],
),
```

### 5. Register in CMakeLists.txt

Add the file to the `install(PROGRAMS ...)` block:

```cmake
install(PROGRAMS
  ...
  ros2_robot_bridge/my_robot_bridge.py
  DESTINATION lib/${PROJECT_NAME}
)
```

### 6. Rebuild

```bash
source /opt/ros/jazzy/setup.bash
cd ~/Lutin/mw_ws
colcon build --packages-select ros2_robot_bridge
source install/setup.bash
```

### Using an AI assistant

The bottom of `robot_bridge_template.py` contains a ready-to-use prompt. Copy everything between the dashed lines into your AI assistant, fill in the robot name, SDK, and capability fields, and the model will produce a complete bridge file using the correct architecture, threading model, and resolution order — and will also output the `robot_detector.py`, `launch`, and `CMakeLists.txt` snippets needed to register it.

---

## Bibliography

This section describes the source code structure of the package: what each file does, how the nodes interact, and the key design decisions.

### Package structure

```
ros2_robot_bridge/
├── ros2_robot_bridge/
│   ├── base_bridge.py             # Abstract base for command bridges (shared ROS2 plumbing)
│   ├── base_sensor.py             # Abstract base for sensor nodes (connect thread + poll timer)
│   ├── robot_detector.py          # Configuration publisher
│   ├── command_dispatcher.py      # Validation & dedup gateway
│   ├── nao_bridge.py              # NAO / Pepper command executor
│   ├── qt_bridge.py               # QTrobot command executor
│   ├── nao_sensors.py             # NAO / Pepper sensor publisher (ALMemory polling via qi)
│   ├── qt_sensor.py               # QTrobot sensor bridge (ROS1 → ROS2 via roslibpy)
│   ├── woz_node.py                # Wizard-of-Oz Flask web interface node (multi-robot)
│   ├── woz_states.py              # WOZ state machine (behaviors and auto-transitions)
│   ├── nao_behavior_tables.py     # Pure-data tables: BEHAVIORS, GESTURES, QT_TO_NAO_* dicts
│   ├── robot_bridge_template.py   # Starting point for new robot adapters (command bridge)
│   └── robot_sensor_template.py   # Starting point for new robot sensor nodes
├── msg/
│   ├── RobotCmd.msg               # Universal command message
│   └── RobotConfig.msg            # Active robot description
├── woz_templates/                 # Flask HTML templates for the WOZ interface
│   ├── robots.html                # Robot list and add-robot form (landing page)
│   ├── login.html
│   ├── scenarios.html
│   ├── reactions.html
│   ├── theatre.html
│   ├── maison.html
│   ├── macros.html                # Macro/gesture buttons tab
│   └── vocal.html                 # Vocal tab (mic button, mode toggle, speed slider, history)
├── woz_static/                    # JS/CSS/image assets served by Flask
│   ├── woz.js / woz.css           # Core UI logic and styles
│   ├── scenarios.js               # Button definitions for the Scenarios tab
│   ├── reactions.js               # Button definitions for the Réactions tab
│   ├── theatre.js                 # Button definitions for the RobotAct tab
│   ├── maison.js                  # Button definitions for the Maison tab
│   └── vocal.js                   # Vocal tab: MediaRecorder, Whisper client, command dispatch
└── launch/
    └── robot_bridge.launch.py     # Single launch file for all robots
requirements.txt                   # pip dependencies (flask, roslibpy, pyopenssl, faster-whisper)
setup.sh                           # Bootstrap script for fresh Ubuntu 22.04 / Jetson systems
```

### robot_detector.py

**Role:** Publishes the active robot identity on the `/robot_config` latched topic.

Reads two launch parameters (`robot_type`, `robot_version`), validates them against a list of known robots, then publishes a `RobotConfig` message. The topic uses `TRANSIENT_LOCAL` durability so any node that subscribes later (including bridges started in any order) always receives the latest config immediately without a re-publish.

The node re-reads parameters every 2 seconds but only publishes when something actually changes — allowing runtime reconfiguration without flooding the bus.

The node also subscribes to the `robot_reconfig` topic (format: `robot_type:robot_version`). When a message arrives it calls `set_parameters()` internally and immediately republishes — this is how the WOZ connect page switches robot type and version at runtime without restarting any node or using `ros2 param set` subprocesses.

**Key data:** `VALID_VERSIONS` dict — the authoritative list of robot types and versions the system recognises.

---

### command_dispatcher.py

**Role:** Single validation and deduplication gateway between the user-facing `/robot_cmd` topic and the internal `robot_cmd_validated` topic consumed by the bridges.

Responsibilities:
- Drops commands if no robot config has been received yet, or if the robot is not marked ready.
- Rejects unknown actions (`speak`, `move`, `display`, `relax`, `stiffen`, `volume` are valid).
- Deduplicates: if the exact same command (all fields) arrives again within 1 second it is silently dropped. This makes it safe to publish with `--times 3` for DDS reliability without executing the action multiple times.
- Prunes the dedup cache periodically so memory stays bounded.

The dispatcher is intentionally **robot-agnostic** — it knows nothing about NAO or QTrobot specifics.

---

### nao_bridge.py

**Role:** Translates validated `RobotCmd` messages into NAOqi service calls for **NAO** (v5/v6) and **Pepper** (v1/v1.8/v2) via the `qi` Python SDK.

#### Connection lifecycle

On receiving an active `RobotConfig`, the node opens a `qi.Session` in a background thread and acquires proxies for six services: `ALRobotPosture`, `ALLeds`, `ALMotion`, `ALTextToSpeech`, `ALBehaviorManager`, and `ALAudioDevice`. If the `qi` SDK is not installed the node falls back to publishing on ROS topics (`/speech`, `/joint_angles`, `/cmd_vel`).

A 60-second keepalive timer calls `ALTextToSpeech.getLanguage()` to prevent the NAOqi TCP connection from closing after long idle periods. If the ping fails, a reconnect thread retries `_connect_qi` up to 5 times with exponential backoff (5 s, 10 s, 15 s, 20 s, 25 s). A `threading.Lock` ensures at most one reconnect thread runs at a time.

The node subscribes to the `nao_reconnect` topic (format: `naoqi_host:<ip>`). When a message arrives it calls `set_parameters([Parameter('naoqi_host', ...)])` from the spin thread, which both updates the parameter store and triggers the `_on_param_change` callback. That callback updates `self._host` and immediately starts a `_reconnect()` thread — so the bridge switches to the new robot IP without any deactivate/reactivate cycle.

#### Command routing in `_do_move`

Motion commands are resolved in priority order:

1. **`behavior:<path>`** escape hatch — bypass all tables, run the path directly via `ALBehaviorManager`.
2. **`QT_TO_NAO_BEHAVIOR`** — map QTrobot dance names to entries in `BEHAVIORS`.
3. **`BEHAVIORS`** — named shortcuts for installed NAOqi behavior paths (`ALBehaviorManager.runBehavior`).
4. **`QT_TO_NAO_MOTION`** — map universal/QTrobot gesture names to NAO gesture names (`None` = silently skip, e.g. for robot-specific gestures that don't exist on NAO).
5. **`GESTURES`** — custom joint-level gesture sequences defined in Python. Each step is a `(joints, angles, speed, pause_s)` tuple. Dict gestures have `init`/`loop`/`cleanup` phases for infinite-loop operation.
6. **`WALK_CMDS`** — walking commands via `ALMotion.moveToward()`. `ALAutonomousLife` is disabled before `wakeUp()` so it cannot override the motion command.
7. **`POSTURE_NAMES`** — named postures via `ALRobotPosture.goToPosture()`.
8. **`Joint:angle,...`** format — raw joint control via `ALMotion.setAngles()` (body joints) or `ALMotion.angleInterpolation()` (hand joints, which require interpolation to work correctly).

All gesture and behavior calls run in daemon threads so the ROS spin loop is never blocked.

#### LED control

`display` with `led_name`+`color` uses `ALLeds.fadeRGB()` on the named group. The LED group tables differ between NAO (ears, feet, brain) and Pepper (shoulders). Emotion-based display fades face + chest (NAO) or face + shoulder (Pepper) to a fixed RGB colour.

#### Stiffness control

`relax`/`stiffen` call `ALMotion.setStiffnesses()`. Full-body relax calls `ALMotion.rest()` so Pepper's safety system cooperates.

#### Autonomous life suppression (Pepper)

`ALAutonomousLife` is disabled at connect time and re-disabled after every command via the `_after_cmd` hook defined in `base_bridge.py`. Pepper's tablet re-enables autonomous life whenever the user interacts with it, so the hook runs unconditionally after each dispatch. The keepalive timer (60 s) also checks the state and disables it if re-enabled externally.

---

### nao_behavior_tables.py

**Role:** Pure-data module shared by `nao_bridge.py` and `woz_node.py`. Contains no ROS or qi imports so it can be loaded in any process without triggering SDK import failures.

| Dict | Contents |
|------|----------|
| `BEHAVIORS` | ~391 entries mapping short names → installed NAOqi behavior paths (`animations/Stand/...`) |
| `GESTURES` | ~50 named joint-angle sequences executed via `ALMotion.angleInterpolationWithSpeed()`. Dict-type gestures have `init`/`loop`/`cleanup` phases. |
| `QT_TO_NAO_BEHAVIOR` | Maps QTrobot gesture paths to `BEHAVIORS` keys |
| `QT_TO_NAO_MOTION` | Maps QTrobot gesture paths to `GESTURES` keys (`None` = silently skip) |

`GESTURES["applause"]` is aliased to `GESTURES["clapping"]` so `applause` degrades gracefully on NAOs that don't have the `Applause_1` behavior pack installed.

---

### woz_node.py

**Role:** Flask web server embedded in a ROS2 node. Manages multiple simultaneous robot connections, each with its own qi session and Flask session namespace.

#### Multi-robot architecture

Each connected robot is represented by a `_RobotSlot` instance that owns:
- A `qi.Session` and six service proxies (same set as `nao_bridge.py`)
- An independent login state and child/therapist name
- A per-slot URL namespace `/r/<rid>/...`

Slots are created via `WozNode.add_robot()` (called from the `/robots` POST handler) and removed via `remove_robot()`. A `threading.Lock` protects the `_robots` dict. The `/robots/status` endpoint returns the live slot list as JSON.

#### Motion resolution in `_RobotSlot._do_move`

Runs in a daemon thread. Resolution order:

1. **`_SLOT_POSTURES`** — `ALRobotPosture.goToPosture()` (stand, sit, …)
2. **`_SLOT_WALK`** — `ALMotion.moveToward()` (walk_forward, stop, …)
3. **`Joint:angle,...`** format — raw joint control via `ALMotion.setAngles()`
4. **`_NAO_BEHAVIORS`** — `ALBehaviorManager.runBehavior()` via `nao_behavior_tables`
5. **`QT_TO_NAO_BEHAVIOR` / `QT_TO_NAO_MOTION`** — QTrobot path translation, then BEHAVIORS lookup
6. **Last resort** — `isBehaviorInstalled()` + `runBehavior()` for raw paths
7. **`_NAO_GESTURES`** — joint-angle step sequences from `nao_behavior_tables.GESTURES`

If a behavior fails with "not installed", execution falls through to the GESTURES check automatically. All errors are logged at WARNING level.

#### TTS and state machine

Button presses send a state name to `/r/<rid>/woz`. The slot looks up the state in `woz_states.py`, strips QTrobot-specific markup, and dispatches `speak`/`move`/`display` commands directly via qi (bypassing the ROS2 topic pipeline). Auto-transitions use a per-slot timer that can be cancelled by any new button press.

---

### qt_bridge.py

**Role:** Translates validated `RobotCmd` messages into QTrobot ROS1 calls forwarded over a **rosbridge** WebSocket using `roslibpy`.

#### Connection lifecycle

On receiving an active `RobotConfig`, the node creates a `roslibpy.Ros` client and connects to the QTrobot's rosbridge server. Once connected (`_on_connected`), the node:
- Logs all available topics and QT-related services (for debugging).
- Subscribes to `/qt_robot/joints/state` to cache current joint positions (used as fallback values when building `Float64MultiArray` commands for joint groups).
- Calls `/qt_robot/gesture/list` to log available gestures at startup.
- Calls `/qt_robot/motors/home` to bring the robot to its home position.
- Pre-advertises all joint command topics so the first publish is instant.

#### Motion routing in `_on_cmd`

1. **`Joint:angle,...`** format — split by joint prefix (`Head`, `Left`, `Right`) and dispatched to the three joint command topics as `std_msgs/Float64MultiArray` in fixed positional order (defined in `QT_JOINT_ORDER`). NAO joint names (`LShoulderPitch` etc.) are automatically translated to QTrobot names (`LeftShoulderPitch`).
2. **`QT_MOTION_MAP`** lookup — maps universal/NAO names to QTrobot gesture names. Values starting with `@` are absolute paths (e.g. `@univ-paris8-2/Gifle` → the custom university package); all other values are prefixed with `QT/` (e.g. `hi` → `QT/hi`). `None` = skip silently.
3. **Unknown names** without `/` — assumed to be top-level QTrobot gestures and prefixed with `QT/` automatically.
4. **Paths containing `/`** — used as-is (already a full gesture path).

All gesture calls use the `/qt_robot/gesture/play` service (`qt_gesture_controller/gesture_play`).

#### Emotion / image display

- `display` with `emotion` calls `/qt_robot/emotion/show` with `QT/<emotion_name>`. If `duration_ms > 0`, a daemon thread sleeps then calls `/qt_robot/emotion/stop`.
- `display` with `image_path` calls `/qt_robot/emotion/show` with the raw path.
- `display` with `led_name` is logged and skipped (QTrobot has no LED API).
- `relax`/`stiffen` are logged and skipped (not supported on QTrobot).

#### `QT_MOTION_MAP` design

The map is intentionally bidirectional in spirit: it covers both universal names (so NAO gesture names work on QTrobot) and QTrobot-native names (so the same message published for a QTrobot session works without any changes). This is what makes the interface truly robot-agnostic from the caller's point of view.

#### Custom gesture system

Gestures that cannot be triggered via `gesture/play` (root-level behavior scripts) are implemented in `QT_CUSTOM_GESTURES` — a dict of `gesture_name → list[(joint_dict, hold_seconds)]`. `do_move()` checks this dict **before** `QT_MOTION_MAP`, so custom implementations always win.

The `_do_custom_gesture()` method groups joints by name prefix (`Head`, `Left`, `Right`), builds a `Float64MultiArray` in the positional order defined by `QT_JOINT_ORDER`, and publishes to the three joint command topics. Steps are executed sequentially with `time.sleep(hold)` between them; the whole sequence runs in a daemon thread.

---

### base_sensor.py

**Role:** Abstract base class for all sensor nodes, mirroring `base_bridge.py` for the command side.

Provides:
- `_start_connect()` — spawns a daemon thread that calls `connect()`. Subclasses call this explicitly as the **last line of `__init__`**, after all `declare_parameter()` calls, to avoid a race between the connection thread and parameter declaration.
- `_start_polling(hz)` — creates a ROS timer that calls `_poll()` at the given rate. Used by polling-style sensors (NAO/Pepper).
- `destroy_node()` — calls `disconnect()` before the ROS node tears down.

Subclasses implement `connect()` (required), `disconnect()` (optional cleanup), and `_poll()` (optional, for timer-based sensors).

---

### nao_sensors.py

**Role:** Polls NAO / Pepper sensor data from ALMemory and publishes it as ROS2 topics.

Inherits `SensorBase`. Uses the ALMemory `getListData()` batch API to minimize Wi-Fi round-trips. Sensors polled: touch buttons (chest, 3 head zones, foot/base bumpers), sonar distances, battery charge, sound detection, and sound localization.

Pepper is auto-detected at connect time (via the `robot_type` parameter or `ALSystem.robotName()`) and switches to platform-specific bumper keys (`Platform/FrontLeft`, `Platform/FrontRight`, `Platform/Back`).

Sound detection uses a timestamp-comparison strategy to distinguish new events from stale ALMemory state (ALMemory never clears the key after a detection — comparing timestamps avoids permanently reporting `True`).

---

### qt_sensor.py

**Role:** Bridges QTrobot ROS1 sensor topics into ROS2 via roslibpy WebSocket subscriptions.

Inherits `SensorBase` using the event-driven pattern (Pattern B): `connect()` calls `client.run()` (blocking) as its last statement; roslibpy calls `_on_connected()` once the WebSocket is ready. Topics bridged: `/qt_robot/joints/state` → `joint_states` (`sensor_msgs/JointState`) and `/qt_robot/motors/states` → `motor_states` (`std_msgs/String`, raw JSON). The `sensor_hz` parameter throttles the joint-state republish rate to avoid flooding ROS2 subscribers.
