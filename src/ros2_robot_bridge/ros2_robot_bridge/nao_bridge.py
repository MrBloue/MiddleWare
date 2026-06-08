#!/usr/bin/env python3
# NAO / Pepper bridge adapter.
# Translates RobotCmd messages into NAOqi service calls via the qi SDK.
# Falls back to ROS topics (/speech, /joint_angles, /cmd_vel) when qi is unavailable.
import threading
import time
import rclpy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from naoqi_bridge_msgs.msg import JointAnglesWithSpeed
from ros2_robot_bridge.base_bridge import RobotBridge
from ros2_robot_bridge.msg import RobotCmd, RobotConfig

try:
    import qi
    _HAS_QI = True
except ImportError:
    _HAS_QI = False

# ROS2 language code → NAOqi language name
LANG_MAP = {
    "fr-FR": "French", "fr": "French",
    "en-US": "English", "en-GB": "English", "en": "English",
    "de-DE": "German", "de": "German",
    "es-ES": "Spanish", "es": "Spanish",
    "it-IT": "Italian", "it": "Italian",
    "ja-JP": "Japanese", "zh-CN": "Chinese",
}

# Emotion → RGB for eye LEDs (r, g, b) in 0.0–1.0
EMOTION_LEDS = {
    "happy":     (1.0, 1.0, 0.0),
    "sad":       (0.0, 0.0, 1.0),
    "angry":     (1.0, 0.0, 0.0),
    "neutral":   (1.0, 1.0, 1.0),
    "surprised": (0.0, 1.0, 1.0),
    "scared":    (0.5, 0.0, 0.5),
    "excited":   (1.0, 0.5, 0.0),
}

# QTrobot / universal motion name → NAO gesture name (None = silently ignored).
QT_TO_NAO_MOTION = {
    # --- Greetings ---
    "hi":               "wave",
    "bye":              "wave",
    "bye-bye":          "wave",
    "adieu":            "wave",
    "send_kiss":        "wave",
    "kiss":             "wave",
    # --- Head ---
    "nodding-yes":      "nod",
    "yes":              "nod",
    "thanks":           "nod",
    "no":               "shake_head",
    "head-right-left":  "shake_head",
    "yawn":             "look_up",
    # --- Arms / body ---
    "curious":          "think",
    "bored":            "think",
    "bored_long":       "think",
    "point_front":      "point_forward",
    "come":             "point_forward",
    "show_left":        "point_forward",
    "show_right":       "point_forward",
    "rappel":           "point_forward",
    "begin":            "point_forward",
    "one-arm-up":       "arm_up",
    "up_left":          "arm_up",
    "up_right":         "arm_up",
    "hug":              "arms_open",
    "hands-up":         "arms_open",
    "hands-side":       "arms_open",
    "strong":           "arms_open",
    "challenge":        "arms_open",
    "stretch":          "arms_open",
    "hoora":            "yay",
    "laugh":            "yay",
    "happy":            "yay",
    "surprise":         "yay",
    "refuse":           "refuse",
    "so_what":          "refuse",
    "protect":          "refuse",
    "angry":            "refuse",
    "so":               "refuse",
    "hand-front-hold":  "give_hand",
    "touch-head":       "pat_pat",
    "clapping":           "clapping",
    "handclap":           "clapping",
    "sneezing":           "sneezing",
    "head_scratch":       "head_scratch",
    "peekaboo":           "peekaboo",
    "peekaboo-back":      "peekaboo",
    "ohno":               "ohno",
    "hips":               "hips",
    "hands-on-hip":       "hips",
    "drink":              "drink",
    "monkey":             "monkey",
    "ecrit":              "ecrit",
    "show_tablet":        "show_tablet",
    "breathing_exercise": "breathing_exercise",
    "neutral":            "neutral",
    "sad":                "sad",
    "cry":                "sad",
    "touch-head-back":    "touch_head_back",
    "hands-on-head":      "hands_on_head",
    "hands-on-belly":     "hands_on_belly",
    "personal-distance":  "personal_distance",
    "premiere_rencontre": "premiere_rencontre",
    "premiere_recontre":  "premiere_rencontre",
    "fera_mieux":         "fera_mieux",
    "grandpa":            "grandpa",
    "luxai_en":           "luxai_en",
    "test":               "test",
    "shy":                "think",
    # --- QTrobot emotion subfolder names ---
    "surprised":          "yay",
    "disgusted":          "refuse",
    "calm":               "think",
    "afraid":             "think",
    # --- QTrobot imitation / hands variants → no direct NAO equivalent ---
    "hands_side":         None,
    "hands_side_back":    None,
    "hands_on_head_back": None,
    "hands_on_hip_back":  None,
    "hands_on_belly_back":None,
    "hands_up_back":      None,
    # --- QTrobot-only gestures (no NAO equivalent) ---
    "fly":                None,
    "beep":               None,
    "drive":              None,
    "driving":            None,
    "beeping":            None,
    "phone_call":         None,
    "pretend_play":       None,
    "show_face":          None,
    "show_qt":            None,
    "swipe_right":        None,
    "swipe_left":         None,
    "dance":              None,
    "dance_1_1":          None,
    "dance_1_2":          None,
    "dance_1_3":          None,
    "dance_1_4":          None,
    "dance_2_1":          None,
    "dance_2_2":          None,
    "dance_2_3":          None,
    "dance_2_4":          None,
    "dance_3_1":          None,
    "dance_3_2":          None,
    "dance_3_3":          None,
    "dance_4_1":          None,
    "dance_4_2":          None,
    "dance_4_3":          None,
    "dance_4_4":          None,
    "dance_4_5":          None,
    "dance_4_6":          None,
    # --- Custom university package gestures (QTrobot-only) ---
    "gifle":              None,
    "kill":               None,
    "ymca":               None,
    "dancing_arms":       None,
    "left_righ":          None,
    "bla":                None,
    "soleil":             None,
    "movinghead":         None,
    "headright":          None,
    "headleft":           None,
    "draw":               None,
    "tetehaute":          None,
    "tournepoigne":       None,
    "hackathon":          None,
    "fullciao":           None,
    "ciao":               None,
    "very_sad":           None,
    "very_sad2":          None,
    "tired":              None,
    # --- QTrobot full-path forms missing from QT_TO_NAO_BEHAVIOR ---
    "qt/neutral":         None,
}

# Universal LED group name → NAOqi ALLeds group name
LED_GROUPS_NAO = {
    "eyes":       "FaceLeds",
    "left_eye":   "LeftFaceLeds",
    "right_eye":  "RightFaceLeds",
    "ears":       "EarLeds",
    "left_ear":   "LeftEarLeds",
    "right_ear":  "RightEarLeds",
    "chest":      "ChestLeds",
    "feet":       "FeetLeds",
    "left_foot":  "LeftFootLeds",
    "right_foot": "RightFootLeds",
    "head":       "BrainLeds",
    "all":        "AllLeds",
}

# Pepper variant: eyes + shoulders only (no ears/feet/brain)
LED_GROUPS_PEPPER = {
    "eyes":          "FaceLeds",
    "left_eye":      "LeftFaceLeds",
    "right_eye":     "RightFaceLeds",
    "chest":         "ChestLeds",
    "shoulder":      "ShoulderLeds",
    "left_shoulder": "LeftShoulderLeds",
    "right_shoulder":"RightShoulderLeds",
    "all":           "AllLeds",
}

LED_GROUPS = LED_GROUPS_NAO  # backward-compat alias

# Named color strings → (r, g, b) in 0–255
LED_COLOR_NAMES = {
    "red":     (255,   0,   0),
    "green":   (  0, 255,   0),
    "blue":    (  0,   0, 255),
    "white":   (255, 255, 255),
    "yellow":  (255, 255,   0),
    "cyan":    (  0, 255, 255),
    "magenta": (255,   0, 255),
    "orange":  (255, 128,   0),
    "purple":  (128,   0, 128),
    "pink":    (255, 105, 180),
    "off":     (  0,   0,   0),
}

def _parse_color(color_str):
    """'#RRGGBB', 'RRGGBB', or named color → (r, g, b) int tuple, or None."""
    s = color_str.strip().lower()
    if s in LED_COLOR_NAMES:
        return LED_COLOR_NAMES[s]
    s = s.lstrip("#")
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except ValueError:
            pass
    return None

# Universal posture name → ALRobotPosture name
POSTURE_NAMES = {
    "stand":      "Stand",
    "standinit":  "StandInit",
    "standzero":  "StandZero",
    "sit":        "Sit",
    "sitrelax":   "SitRelax",
    "crouch":     "Crouch",
    "lyingback":  "LyingBack",
    "lyingbelly": "LyingBelly",
}

# Custom gesture library. Each entry: list of steps (joints, angles_rad, speed, pause_s).
# Dict entries use {"init", "loop", "cleanup"} for looping gestures.
GESTURES = {
    # --- Head ---
    "look_left": [
        (["HeadYaw"], [0.7], 0.4, 1.5),
        (["HeadYaw"], [0.0], 0.3, 0.0),
    ],
    "look_right": [
        (["HeadYaw"], [-0.7], 0.4, 1.5),
        (["HeadYaw"], [0.0], 0.3, 0.0),
    ],
    "look_up": [
        (["HeadPitch"], [-0.4], 0.4, 1.5),
        (["HeadPitch"], [-0.18], 0.3, 0.0),
    ],
    "look_down": [
        (["HeadPitch"], [0.5], 0.4, 1.5),
        (["HeadPitch"], [-0.18], 0.3, 0.0),
    ],
    # --- Arms ---
    "arms_open": [
        # Spread both arms wide open — welcoming gesture
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LHand",
          "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [0.5, 1.0, -0.05, -1.57, 1.0,
          0.5, -1.0,  0.05,  1.57, 1.0], 0.4, 2.0),
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LHand",
          "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3], 0.3, 0.0),
    ],
    "point_forward": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [0.0, -0.1, 0.05, 1.57, 0.1], 0.4, 2.0),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [1.47, -0.21, 0.42, 1.21, 0.3], 0.3, 0.0),
    ],
    "salute": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand",
          "HeadPitch"],
         [-0.4, -0.3, 0.9, 0.8, 0.5, 0.0, -0.1], 0.4, 1.5),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand",
          "HeadPitch"],
         [1.47, -0.21, 0.42, 1.21, 0.08, 0.3, -0.18], 0.3, 0.0),
    ],
    "think": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand",
          "HeadPitch", "HeadYaw"],
         [0.6, -0.2, 1.2, 0.4, 0.3, 0.2, 0.2], 0.3, 3.0),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand",
          "HeadPitch", "HeadYaw"],
         [1.47, -0.21, 0.42, 1.21, 0.3, -0.18, 0.0], 0.3, 0.0),
    ],
    "refuse": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "HeadYaw"],
         [0.5, -0.8, 0.5, 0.4], 0.5, 0.3),
        (["HeadYaw"], [-0.4], 0.6, 0.3),
        (["HeadYaw"], [0.4], 0.6, 0.3),
        (["HeadYaw"], [-0.4], 0.6, 0.3),
        (["HeadYaw"], [0.0], 0.4, 0.2),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll"],
         [1.47, -0.21, 0.42], 0.3, 0.0),
    ],
    "arm_up": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw"],
         [-1.57, -0.1, 0.05, 1.57], 0.3, 1.2),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw"],
         [1.47, -0.21, 0.42, 1.21], 0.3, 0.0),
    ],
    "wave": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw"],
         [-0.5, -0.3, 0.05, 1.57], 0.4, 0.6),
        (["RWristYaw"], [-1.0], 0.8, 0.4),
        (["RWristYaw"], [1.0], 0.8, 0.4),
        (["RWristYaw"], [-1.0], 0.8, 0.4),
        (["RWristYaw"], [1.0], 0.8, 0.4),
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw"],
         [1.47, -0.21, 0.42, 1.21, 0.08], 0.3, 0.0),
    ],
    "pat_pat": {
        "init": [
            (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw", "LHand"],
             [0.1, 0.3, 0.5, -1.57, 1.57, 1.0], 0.4, 0.4),
        ],
        "loop": [
            (["LShoulderPitch"], [0.2], 0.4, 0.5),
            (["LHand"], [0.4], 0.15, 0.6),
            (["LHand"], [1.0], 0.15, 0.4),
            (["LHand"], [0.4], 0.15, 0.6),
            (["LHand"], [1.0], 0.15, 0.4),
            (["LHand"], [0.4], 0.15, 0.6),
            (["LHand"], [1.0], 0.15, 0.3),
            (["LShoulderPitch"], [0.1], 0.4, 0.4),
        ],
        "cleanup": [
            (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw", "LHand"],
             [1.47, 0.21, -0.42, -1.21, 0.0, 0.3], 0.3, 0.0),
        ],
    },
    "nod": [
        (["HeadPitch"], [0.4], 0.5, 0.4),
        (["HeadPitch"], [-0.1], 0.5, 0.3),
        (["HeadPitch"], [0.4], 0.5, 0.4),
        (["HeadPitch"], [-0.18], 0.3, 0.0),
    ],
    "give_hand": [
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LHand"],
         [1.2, 0.1, -0.05, -1.57, 1.0], 0.4, 3.0),
        (["LHand"], [0.0], 0.08, 0.0),
    ],
    "give_hand_sitted": [
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw", "LHand"],
         [0.2, 0.1, -0.05, -1.57, -1.57, 1.0], 0.4, 3.0),
        (["LHand"], [0.0], 0.08, 0.0),
    ],
    "give_hand_right": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [1.2, -0.1, 0.05, 1.57, 1.0], 0.4, 3.0),
        (["RHand"], [0.0], 0.08, 0.0),
    ],
    "give_hand_sitted_right": [
        (["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw", "RHand"],
         [0.2, -0.1, 0.05, 1.57, 1.57, 1.0], 0.4, 3.0),
        (["RHand"], [0.0], 0.08, 0.0),
    ],
    "close_right_hand": [
        (["RHand"], [ 1.0], 0.4, 3.0),
        (["RHand"], [-1.0], 0.08, 0.0),
    ],
    "close_left_hand": [
        (["LHand"], [1.0], 0.4, 3.0),
        (["LHand"], [0.1], 0.08, 0.0),
    ],
    "yay": [
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LHand",
          "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [-1.5, 0.3, -0.05, -1.57, 1.0,
          -1.5, -0.3,  0.05,  1.57, 1.0], 0.6, 0.5),
        (["LShoulderPitch", "RShoulderPitch"], [-1.7, -1.7], 0.8, 0.25),
        (["LShoulderPitch", "RShoulderPitch"], [-1.5, -1.5], 0.8, 0.25),
        (["LShoulderPitch", "RShoulderPitch"], [-1.7, -1.7], 0.8, 0.25),
        (["LShoulderPitch", "RShoulderPitch"], [-1.5, -1.5], 0.8, 0.5),
        (["LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LHand",
          "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RHand"],
         [1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3], 0.3, 0.0),
    ],
    "shake_head": [
        (["HeadYaw"], [0.5], 0.5, 0.3),
        (["HeadYaw"], [-0.5], 0.5, 0.3),
        (["HeadYaw"], [0.5], 0.5, 0.3),
        (["HeadYaw"], [-0.5], 0.5, 0.3),
        (["HeadYaw"], [0.0], 0.3, 0.0),
    ],
    "clapping": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [0.9, -0.1, -0.3, -0.5, 0.8,
          0.9,  0.1,  0.3,  0.5, 0.8], 0.4, 0.3),
        (["LElbowRoll","RElbowRoll"], [-0.05, 0.05], 0.9, 0.1),
        (["LElbowRoll","RElbowRoll"], [-0.3,  0.3],  0.9, 0.1),
        (["LElbowRoll","RElbowRoll"], [-0.05, 0.05], 0.9, 0.1),
        (["LElbowRoll","RElbowRoll"], [-0.3,  0.3],  0.9, 0.1),
        (["LElbowRoll","RElbowRoll"], [-0.05, 0.05], 0.9, 0.1),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3], 0.3, 0.0),
    ],
    "sneezing": [
        (["HeadPitch","RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw"],
         [-0.3, 0.5, -0.1, 0.6, 0.8], 0.25, 0.9),
        (["HeadPitch","RShoulderPitch"], [0.45, 1.3], 1.0, 0.4),
        (["HeadPitch","RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw"],
         [-0.18, 1.47, -0.21, 0.42, 1.21], 0.3, 0.0),
    ],
    "head_scratch": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [-0.2, -0.3, 1.3, 1.0, 0.0], 0.4, 0.4),
        (["RShoulderPitch"], [-0.1], 0.5, 0.25),
        (["RShoulderPitch"], [-0.35], 0.5, 0.25),
        (["RShoulderPitch"], [-0.1], 0.5, 0.25),
        (["RShoulderPitch"], [-0.35], 0.5, 0.25),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.47, -0.21, 0.42, 1.21, 0.0], 0.3, 0.0),
    ],
    "peekaboo": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [0.4, 0.0, -0.7, -1.0, 0.2,
          0.4, 0.0,  0.7,  1.0, 0.2], 0.4, 0.8),
        (["LShoulderRoll","LHand","RShoulderRoll","RHand"],
         [0.8, 1.0, -0.8, 1.0], 0.6, 0.7),
        (["LShoulderRoll","LHand","RShoulderRoll","RHand"],
         [0.0, 0.2,  0.0, 0.2], 0.5, 0.7),
        (["LShoulderRoll","LHand","RShoulderRoll","RHand"],
         [0.8, 1.0, -0.8, 1.0], 0.6, 0.5),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3], 0.3, 0.0),
    ],
    "ohno": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","HeadPitch"],
         [-0.1, 0.5, -0.9, -1.5,
          -0.1, -0.5,  0.9,  1.5, 0.2], 0.5, 1.5),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","HeadPitch"],
         [1.47, 0.21, -0.42, -1.21,
          1.47, -0.21,  0.42,  1.21, -0.18], 0.3, 0.0),
    ],
    "hips": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.3, 0.6, -1.3, -0.5, 0.0,
          1.3, -0.6,  1.3,  0.5, 0.0], 0.4, 2.0),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.47, 0.21, -0.42, -1.21, 0.0,
          1.47, -0.21,  0.42,  1.21, 0.0], 0.3, 0.0),
    ],
    "drink": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [0.6, -0.1, 0.9, 1.0, -1.0, 0.5], 0.4, 0.5),
        (["HeadPitch"], [0.3], 0.3, 1.2),
        (["HeadPitch","RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [-0.18, 1.47, -0.21, 0.42, 1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "monkey": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [0.3, 0.8, -0.8, -1.5, 0.6,
          0.3, -0.8,  0.8,  1.5, 0.6], 0.4, 0.3),
        (["LShoulderPitch","RShoulderPitch","HeadYaw"], [0.5, 0.1, -0.3], 0.4, 0.4),
        (["LShoulderPitch","RShoulderPitch","HeadYaw"], [0.1, 0.5,  0.3], 0.4, 0.4),
        (["LShoulderPitch","RShoulderPitch","HeadYaw"], [0.5, 0.1, -0.3], 0.4, 0.4),
        (["LShoulderPitch","RShoulderPitch","HeadYaw"], [0.1, 0.5,  0.3], 0.4, 0.3),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand","HeadYaw"],
         [1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3, 0.0], 0.3, 0.0),
    ],
    "ecrit": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.1, -0.1, 0.3, 0.6, 0.0, 0.1], 0.3, 0.3),
        (["RShoulderPitch","RShoulderRoll"], [1.0, -0.2], 0.5, 0.2),
        (["RShoulderPitch","RShoulderRoll"], [1.2,  0.0], 0.5, 0.2),
        (["RShoulderPitch","RShoulderRoll"], [1.0, -0.15], 0.5, 0.2),
        (["RShoulderPitch","RShoulderRoll"], [1.2,  0.05], 0.5, 0.2),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.47, -0.21, 0.42, 1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "show_tablet": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [0.9, -0.1, -0.3, -0.5, 0.9, 0.7,
          0.9,  0.1,  0.3,  0.5, -0.9, 0.7], 0.4, 2.5),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.47, 0.21, -0.42, -1.21, 0.0, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "breathing_exercise": [
        (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [0.3, 0.3, 0.3, -0.3], 0.15, 3.0),
        (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [1.47, 0.21, 1.47, -0.21], 0.15, 2.5),
        (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [0.3, 0.3, 0.3, -0.3], 0.15, 3.0),
        (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [1.47, 0.21, 1.47, -0.21], 0.15, 0.0),
    ],
    "neutral": [
        (["HeadYaw","HeadPitch",
          "LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand"],
         [0.0, -0.18,
          1.47, 0.21, -0.42, -1.21, 0.3,
          1.47, -0.21,  0.42,  1.21, 0.3], 0.25, 0.0),
    ],
    "sad": [
        (["HeadPitch","LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [0.45, 1.6, 0.1, 1.6, -0.1], 0.2, 3.0),
        (["HeadPitch","LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll"],
         [-0.18, 1.47, 0.21, 1.47, -0.21], 0.3, 0.0),
    ],
    "touch_head_back": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [-0.5, -0.2, 1.45, 0.3, 0.0], 0.4, 1.5),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.47, -0.21, 0.42, 1.21, 0.0], 0.3, 0.0),
    ],
    "hands_on_head": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw"],
         [-0.1, 0.5, -0.9, -1.5,
          -0.1, -0.5,  0.9,  1.5], 0.4, 2.0),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw"],
         [1.47, 0.21, -0.42, -1.21,
          1.47, -0.21,  0.42,  1.21], 0.3, 0.0),
    ],
    "hands_on_belly": [
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.3, -0.1, -0.9, -1.0, 0.5,
          1.3,  0.1,  0.9,  1.0, -0.5], 0.4, 2.0),
        (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw",
          "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw"],
         [1.47, 0.21, -0.42, -1.21, 0.0,
          1.47, -0.21,  0.42,  1.21, 0.0], 0.3, 0.0),
    ],
    "personal_distance": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [0.2, -0.1, 0.05, 1.57, 0.0, 0.9], 0.4, 2.0),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.47, -0.21, 0.42, 1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "premiere_rencontre": [
        (["HeadPitch"], [0.35], 0.3, 0.5),
        (["HeadPitch"], [-0.18], 0.3, 0.3),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [-0.4, -0.3, 0.05, 1.57, 0.0, 0.9], 0.4, 0.3),
        (["RWristYaw"], [-1.0], 0.8, 0.2),
        (["RWristYaw"], [ 1.0], 0.8, 0.2),
        (["RWristYaw"], [-1.0], 0.8, 0.2),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.47, -0.21, 0.42, 1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "fera_mieux": [
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [0.8, -0.2, 0.3, 1.0, -1.5, 0.1], 0.4, 0.5),
        (["HeadPitch"], [0.2], 0.4, 0.3),
        (["HeadPitch"], [-0.1], 0.4, 0.3),
        (["HeadPitch"], [0.2], 0.4, 0.3),
        (["HeadPitch"], [-0.18], 0.4, 0.2),
        (["RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw","RHand"],
         [1.47, -0.21, 0.42, 1.21, 0.0, 0.3], 0.3, 0.0),
    ],
    "grandpa": [
        (["HeadYaw","HeadPitch","RShoulderPitch","RElbowRoll"],
         [0.4, 0.1, 1.0, 0.7], 0.15, 1.5),
        (["HeadYaw"], [-0.4], 0.15, 1.5),
        (["HeadYaw","HeadPitch"], [0.0, 0.2], 0.15, 0.8),
        (["HeadPitch","RShoulderPitch","RElbowRoll"],
         [-0.18, 1.47, 0.42], 0.2, 0.0),
    ],
    "luxai_en": [
        (["LShoulderPitch","RShoulderPitch"], [0.0, 1.47], 0.5, 0.3),
        (["LShoulderPitch","RShoulderPitch"], [1.47, 0.0], 0.5, 0.3),
        (["LShoulderPitch","RShoulderPitch"], [0.0, 1.47], 0.5, 0.3),
        (["LShoulderPitch","RShoulderPitch"], [1.47, 0.0], 0.5, 0.3),
        (["LShoulderPitch","RShoulderPitch"], [1.47, 1.47], 0.4, 0.0),
    ],
    "six_seven": {
        # Pendulum swing: both arms swing together left ↔ right indefinitely
        "init": [
            (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand","LWristYaw",
              "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand","RWristYaw"],
             [0.6, 0.2, -0.5, -1.0, 1.0, -1.57,
              0.6, -0.2,  0.5,  1.0, 1.0, 1.57], 1.0, 0.0),
        ],
        "loop": [
            (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll","HeadYaw"],
             [0.55, -0.05, 1.05, 0.05, 0.35], 0.55, 0.35),
            (["LShoulderPitch","LShoulderRoll","RShoulderPitch","RShoulderRoll","HeadYaw"],
             [1.05, -0.05, 0.55, 0.05, -0.35], 0.55, 0.35),
        ],
        "cleanup": [
            (["LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LHand",
              "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RHand","HeadYaw"],
             [1.47, 0.21, -0.42, -1.21, 0.3,
              1.47, -0.21,  0.42,  1.21, 0.3, 0.0], 0.3, 0.0),
        ],
    },
}

# Built-in NAOqi behavior paths (verified on Pepper 2.5).
# Pass `behavior:<path>` as motion_name to bypass this map entirely.
BEHAVIORS = {
    # --- Dance / performance ---
    "funny_dancer":       "animations/Stand/Waiting/FunnyDancer_1",
    "air_guitar":         "animations/Stand/Waiting/AirGuitar_1",
    "bandmaster":         "animations/Stand/Waiting/Bandmaster_1",
    "kung_fu":            "animations/Stand/Waiting/KungFu_1",
    "robot_dance":        "animations/Stand/Waiting/Robot_1",
    "zombie":             "animations/Stand/Waiting/Zombie_1",
    "happy_birthday":     "animations/Stand/Waiting/HappyBirthday_1",
    "helicopter":         "animations/Stand/Waiting/Helicopter_1",
    "space_shuttle":      "animations/Stand/Waiting/SpaceShuttle_1",
    "drive_car":          "animations/Stand/Waiting/DriveCar_1",
    "air_juggle":         "animations/Stand/Waiting/AirJuggle_1",
    "funny_slide":        "animations/Stand/Waiting/FunnySlide_1",
    "headbang":           "animations/Stand/Waiting/Headbang_1",
    "knight":             "animations/Stand/Waiting/Knight_1",
    "vacuum":             "animations/Stand/Waiting/Vacuum_1",
    "walk_in_the_shit":   "animations/Stand/Waiting/WalkInTheShit_1",
    # --- Fun / waiting ---
    "show_muscles":       "animations/Stand/Waiting/ShowMuscles_1",
    "show_muscles_2":     "animations/Stand/Waiting/ShowMuscles_2",
    "show_muscles_3":     "animations/Stand/Waiting/ShowMuscles_3",
    "show_muscles_4":     "animations/Stand/Waiting/ShowMuscles_4",
    "show_muscles_5":     "animations/Stand/Waiting/ShowMuscles_5",
    "fitness":            "animations/Stand/Waiting/Fitness_1",
    "fitness_2":          "animations/Stand/Waiting/Fitness_2",
    "fitness_3":          "animations/Stand/Waiting/Fitness_3",
    "stretch_wait":       "animations/Stand/Waiting/Stretch_1",
    "stretch_wait_2":     "animations/Stand/Waiting/Stretch_2",
    "stretch_wait_3":     "animations/Stand/Waiting/Stretch_3",
    "back_rubs":          "animations/Stand/Waiting/BackRubs_1",
    "binoculars":         "animations/Stand/Waiting/Binoculars_1",
    "call_someone":       "animations/Stand/Waiting/CallSomeone_1",
    "drink_wait":         "animations/Stand/Waiting/Drink_1",
    "hide_eyes":          "animations/Stand/Waiting/HideEyes_1",
    "hide_hands":         "animations/Stand/Waiting/HideHands_1",
    "innocent_wait":      "animations/Stand/Waiting/Innocent_1",
    "knock_eye":          "animations/Stand/Waiting/KnockEye_1",
    "look_hand":          "animations/Stand/Waiting/LookHand_1",
    "look_hand_2":        "animations/Stand/Waiting/LookHand_2",
    "love_you":           "animations/Stand/Waiting/LoveYou_1",
    "monster":            "animations/Stand/Waiting/Monster_1",
    "mystical_power":     "animations/Stand/Waiting/MysticalPower_1",
    "play_hands":         "animations/Stand/Waiting/PlayHands_1",
    "play_hands_2":       "animations/Stand/Waiting/PlayHands_2",
    "play_hands_3":       "animations/Stand/Waiting/PlayHands_3",
    "relaxation":         "animations/Stand/Waiting/Relaxation_1",
    "relaxation_2":       "animations/Stand/Waiting/Relaxation_2",
    "relaxation_3":       "animations/Stand/Waiting/Relaxation_3",
    "relaxation_4":       "animations/Stand/Waiting/Relaxation_4",
    "rest":               "animations/Stand/Waiting/Rest_1",
    "scratch_back":       "animations/Stand/Waiting/ScratchBack_1",
    "scratch_bottom":     "animations/Stand/Waiting/ScratchBottom_1",
    "scratch_eye":        "animations/Stand/Waiting/ScratchEye_1",
    "scratch_hand":       "animations/Stand/Waiting/ScratchHand_1",
    "scratch_head":       "animations/Stand/Waiting/ScratchHead_1",
    "scratch_leg":        "animations/Stand/Waiting/ScratchLeg_1",
    "scratch_torso":      "animations/Stand/Waiting/ScratchTorso_1",
    "show_sky_wait":      "animations/Stand/Waiting/ShowSky_1",
    "show_sky_wait_2":    "animations/Stand/Waiting/ShowSky_2",
    "take_picture":       "animations/Stand/Waiting/TakePicture_1",
    "taxi":               "animations/Stand/Waiting/Taxi_1",
    "think":              "animations/Stand/Waiting/Think_1",
    "think_2":            "animations/Stand/Waiting/Think_2",
    "think_3":            "animations/Stand/Waiting/Think_3",
    "think_4":            "animations/Stand/Waiting/Think_4",
    "waddle":             "animations/Stand/Waiting/Waddle_1",
    "waddle_2":           "animations/Stand/Waiting/Waddle_2",
    "wake_up":            "animations/Stand/Waiting/WakeUp_1",
    # --- Positive emotions ---
    "ecstatic":           "animations/Stand/Emotions/Positive/Ecstatic_1",
    "enthusiastic":       "animations/Stand/Emotions/Positive/Enthusiastic_1",
    "excited_anim":       "animations/Stand/Emotions/Positive/Excited_1",
    "excited_anim_2":     "animations/Stand/Emotions/Positive/Excited_2",
    "excited_anim_3":     "animations/Stand/Emotions/Positive/Excited_3",
    "happy_anim":         "animations/Stand/Emotions/Positive/Happy_1",
    "happy_anim_2":       "animations/Stand/Emotions/Positive/Happy_2",
    "happy_anim_3":       "animations/Stand/Emotions/Positive/Happy_3",
    "happy_anim_4":       "animations/Stand/Emotions/Positive/Happy_4",
    "hungry_anim":        "animations/Stand/Emotions/Positive/Hungry_1",
    "hysterical":         "animations/Stand/Emotions/Positive/Hysterical_1",
    "laugh_anim":         "animations/Stand/Emotions/Positive/Laugh_1",
    "laugh_anim_2":       "animations/Stand/Emotions/Positive/Laugh_2",
    "laugh_anim_3":       "animations/Stand/Emotions/Positive/Laugh_3",
    "mocker":             "animations/Stand/Emotions/Positive/Mocker_1",
    "optimistic":         "animations/Stand/Emotions/Positive/Optimistic_1",
    "peaceful":           "animations/Stand/Emotions/Positive/Peaceful_1",
    "proud":              "animations/Stand/Emotions/Positive/Proud_1",
    "proud_2":            "animations/Stand/Emotions/Positive/Proud_2",
    "proud_3":            "animations/Stand/Emotions/Positive/Proud_3",
    "relieved":           "animations/Stand/Emotions/Positive/Relieved_1",
    "shy_anim":           "animations/Stand/Emotions/Positive/Shy_1",
    "shy_anim_2":         "animations/Stand/Emotions/Positive/Shy_2",
    "sure":               "animations/Stand/Emotions/Positive/Sure_1",
    "winner":             "animations/Stand/Emotions/Positive/Winner_1",
    "winner_2":           "animations/Stand/Emotions/Positive/Winner_2",
    "amused":             "animations/Stand/Emotions/Positive/Amused_1",
    "confident":          "animations/Stand/Emotions/Positive/Confident_1",
    # --- Negative emotions ---
    "angry_anim":         "animations/Stand/Emotions/Negative/Angry_1",
    "angry_anim_2":       "animations/Stand/Emotions/Negative/Angry_2",
    "angry_anim_3":       "animations/Stand/Emotions/Negative/Angry_3",
    "angry_anim_4":       "animations/Stand/Emotions/Negative/Angry_4",
    "anxious":            "animations/Stand/Emotions/Negative/Anxious_1",
    "bored_anim":         "animations/Stand/Emotions/Negative/Bored_1",
    "bored_anim_2":       "animations/Stand/Emotions/Negative/Bored_2",
    "disappointed":       "animations/Stand/Emotions/Negative/Disappointed_1",
    "exhausted":          "animations/Stand/Emotions/Negative/Exhausted_1",
    "exhausted_2":        "animations/Stand/Emotions/Negative/Exhausted_2",
    "fear":               "animations/Stand/Emotions/Negative/Fear_1",
    "fear_2":             "animations/Stand/Emotions/Negative/Fear_2",
    "fearful":            "animations/Stand/Emotions/Negative/Fearful_1",
    "frustrated":         "animations/Stand/Emotions/Negative/Frustrated_1",
    "humiliated":         "animations/Stand/Emotions/Negative/Humiliated_1",
    "hurt":               "animations/Stand/Emotions/Negative/Hurt_1",
    "hurt_2":             "animations/Stand/Emotions/Negative/Hurt_2",
    "late":               "animations/Stand/Emotions/Negative/Late_1",
    "sad_anim":           "animations/Stand/Emotions/Negative/Sad_1",
    "sad_anim_2":         "animations/Stand/Emotions/Negative/Sad_2",
    "shocked":            "animations/Stand/Emotions/Negative/Shocked_1",
    "sorry":              "animations/Stand/Emotions/Negative/Sorry_1",
    "surprised_anim":     "animations/Stand/Emotions/Negative/Surprise_1",
    "surprised_anim_2":   "animations/Stand/Emotions/Negative/Surprise_2",
    "surprised_anim_3":   "animations/Stand/Emotions/Negative/Surprise_3",
    # --- Neutral emotions ---
    "alienated":          "animations/Stand/Emotions/Neutral/Alienated_1",
    "annoyed":            "animations/Stand/Emotions/Neutral/Annoyed_1",
    "ask_attention":      "animations/Stand/Emotions/Neutral/AskForAttention_1",
    "ask_attention_2":    "animations/Stand/Emotions/Neutral/AskForAttention_2",
    "ask_attention_3":    "animations/Stand/Emotions/Neutral/AskForAttention_3",
    "cautious":           "animations/Stand/Emotions/Neutral/Cautious_1",
    "confused_anim":      "animations/Stand/Emotions/Neutral/Confused_1",
    "determined":         "animations/Stand/Emotions/Neutral/Determined_1",
    "embarrassed":        "animations/Stand/Emotions/Neutral/Embarrassed_1",
    "hello_anim":         "animations/Stand/Emotions/Neutral/Hello_1",
    "hesitation":         "animations/Stand/Emotions/Neutral/Hesitation_1",
    "innocent_anim":      "animations/Stand/Emotions/Neutral/Innocent_1",
    "lonely":             "animations/Stand/Emotions/Neutral/Lonely_1",
    "mischievous":        "animations/Stand/Emotions/Neutral/Mischievous_1",
    "puzzled":            "animations/Stand/Emotions/Neutral/Puzzled_1",
    "sneeze_anim":        "animations/Stand/Emotions/Neutral/Sneeze",
    "stubborn":           "animations/Stand/Emotions/Neutral/Stubborn_1",
    "suspicious":         "animations/Stand/Emotions/Neutral/Suspicious_1",
    # --- Gestures ---
    "angry_gesture":      "animations/Stand/Gestures/Angry_1",
    "angry_gesture_2":    "animations/Stand/Gestures/Angry_2",
    "angry_gesture_3":    "animations/Stand/Gestures/Angry_3",
    "applause":           "animations/Stand/Gestures/Applause_1",
    "bow":                "animations/Stand/Gestures/BowShort_1",
    "but":                "animations/Stand/Gestures/But_1",
    "calm_down":          "animations/Stand/Gestures/CalmDown_1",
    "calm_down_2":        "animations/Stand/Gestures/CalmDown_2",
    "calm_down_3":        "animations/Stand/Gestures/CalmDown_3",
    "calm_down_4":        "animations/Stand/Gestures/CalmDown_4",
    "calm_down_5":        "animations/Stand/Gestures/CalmDown_5",
    "calm_down_6":        "animations/Stand/Gestures/CalmDown_6",
    "caress":             "animations/Stand/Gestures/Caress_1",
    "caress_2":           "animations/Stand/Gestures/Caress_2",
    "catch_fly":          "animations/Stand/Gestures/CatchFly_1",
    "catch_fly_2":        "animations/Stand/Gestures/CatchFly_2",
    "choice":             "animations/Stand/Gestures/Choice_1",
    "choice_2":           "animations/Stand/Gestures/Choice_2",
    "claw":               "animations/Stand/Gestures/Claw_1",
    "claw_2":             "animations/Stand/Gestures/Claw_2",
    "coaxing":            "animations/Stand/Gestures/Coaxing_1",
    "coaxing_2":          "animations/Stand/Gestures/Coaxing_2",
    "come_on":            "animations/Stand/Gestures/ComeOn_1",
    "confused_gesture":   "animations/Stand/Gestures/Confused_1",
    "confused_gesture_2": "animations/Stand/Gestures/Confused_2",
    "count_one":          "animations/Stand/Gestures/CountOne_1",
    "count_one_2":        "animations/Stand/Gestures/CountOne_2",
    "count_two":          "animations/Stand/Gestures/CountTwo_1",
    "count_two_2":        "animations/Stand/Gestures/CountTwo_2",
    "count_three":        "animations/Stand/Gestures/CountThree_1",
    "count_three_2":      "animations/Stand/Gestures/CountThree_2",
    "count_four":         "animations/Stand/Gestures/CountFour_1",
    "count_four_2":       "animations/Stand/Gestures/CountFour_2",
    "count_five":         "animations/Stand/Gestures/CountFive_1",
    "count_five_2":       "animations/Stand/Gestures/CountFive_2",
    "count_more":         "animations/Stand/Gestures/CountMore_1",
    "count_more_2":       "animations/Stand/Gestures/CountMore_2",
    "desperate":          "animations/Stand/Gestures/Desperate_1",
    "desperate_2":        "animations/Stand/Gestures/Desperate_2",
    "desperate_3":        "animations/Stand/Gestures/Desperate_3",
    "desperate_4":        "animations/Stand/Gestures/Desperate_4",
    "desperate_5":        "animations/Stand/Gestures/Desperate_5",
    "enthusiastic_g":     "animations/Stand/Gestures/Enthusiastic_1",
    "enthusiastic_g2":    "animations/Stand/Gestures/Enthusiastic_2",
    "enthusiastic_g3":    "animations/Stand/Gestures/Enthusiastic_3",
    "enthusiastic_g4":    "animations/Stand/Gestures/Enthusiastic_4",
    "enthusiastic_g5":    "animations/Stand/Gestures/Enthusiastic_5",
    "everything":         "animations/Stand/Gestures/Everything_1",
    "everything_2":       "animations/Stand/Gestures/Everything_2",
    "everything_3":       "animations/Stand/Gestures/Everything_3",
    "everything_4":       "animations/Stand/Gestures/Everything_4",
    "everything_5":       "animations/Stand/Gestures/Everything_5",
    "everything_6":       "animations/Stand/Gestures/Everything_6",
    "excited_gesture":    "animations/Stand/Gestures/Excited_1",
    "explain":            "animations/Stand/Gestures/Explain_1",
    "explain_2":          "animations/Stand/Gestures/Explain_2",
    "explain_3":          "animations/Stand/Gestures/Explain_3",
    "explain_4":          "animations/Stand/Gestures/Explain_4",
    "explain_5":          "animations/Stand/Gestures/Explain_5",
    "explain_6":          "animations/Stand/Gestures/Explain_6",
    "explain_7":          "animations/Stand/Gestures/Explain_7",
    "explain_8":          "animations/Stand/Gestures/Explain_8",
    "explain_9":          "animations/Stand/Gestures/Explain_9",
    "explain_10":         "animations/Stand/Gestures/Explain_10",
    "explain_11":         "animations/Stand/Gestures/Explain_11",
    "far":                "animations/Stand/Gestures/Far_1",
    "far_2":              "animations/Stand/Gestures/Far_2",
    "far_3":              "animations/Stand/Gestures/Far_3",
    "follow":             "animations/Stand/Gestures/Follow_1",
    "freeze":             "animations/Stand/Gestures/Freeze_1",
    "give":               "animations/Stand/Gestures/Give_1",
    "give_2":             "animations/Stand/Gestures/Give_2",
    "give_3":             "animations/Stand/Gestures/Give_3",
    "give_4":             "animations/Stand/Gestures/Give_4",
    "give_5":             "animations/Stand/Gestures/Give_5",
    "give_6":             "animations/Stand/Gestures/Give_6",
    "great":              "animations/Stand/Gestures/Great_1",
    "he_says":            "animations/Stand/Gestures/HeSays_1",
    "he_says_2":          "animations/Stand/Gestures/HeSays_2",
    "he_says_3":          "animations/Stand/Gestures/HeSays_3",
    "hey":                "animations/Stand/Gestures/Hey_1",
    "hey_2":              "animations/Stand/Gestures/Hey_2",
    "hey_3":              "animations/Stand/Gestures/Hey_3",
    "hey_4":              "animations/Stand/Gestures/Hey_4",
    "hey_5":              "animations/Stand/Gestures/Hey_5",
    "hey_6":              "animations/Stand/Gestures/Hey_6",
    "hey_7":              "animations/Stand/Gestures/Hey_7",
    "hide":               "animations/Stand/Gestures/Hide_1",
    "hungry_gesture":     "animations/Stand/Gestures/Hungry_1",
    "i_dont_know":        "animations/Stand/Gestures/IDontKnow_1",
    "i_dont_know_2":      "animations/Stand/Gestures/IDontKnow_2",
    "i_dont_know_3":      "animations/Stand/Gestures/IDontKnow_3",
    "i_dont_know_4":      "animations/Stand/Gestures/IDontKnow_4",
    "i_dont_know_5":      "animations/Stand/Gestures/IDontKnow_5",
    "i_dont_know_6":      "animations/Stand/Gestures/IDontKnow_6",
    "joint_hands":        "animations/Stand/Gestures/JointHands_1",
    "joint_hands_2":      "animations/Stand/Gestures/JointHands_2",
    "joint_hands_3":      "animations/Stand/Gestures/JointHands_3",
    "joy_anim":           "animations/Stand/Gestures/Joy_1",
    "kisses":             "animations/Stand/Gestures/Kisses_1",
    "look":               "animations/Stand/Gestures/Look_1",
    "look_2":             "animations/Stand/Gestures/Look_2",
    "maybe":              "animations/Stand/Gestures/Maybe_1",
    "me":                 "animations/Stand/Gestures/Me_1",
    "me_2":               "animations/Stand/Gestures/Me_2",
    "me_3":               "animations/Stand/Gestures/Me_3",
    "me_4":               "animations/Stand/Gestures/Me_4",
    "me_5":               "animations/Stand/Gestures/Me_5",
    "me_6":               "animations/Stand/Gestures/Me_6",
    "me_7":               "animations/Stand/Gestures/Me_7",
    "me_8":               "animations/Stand/Gestures/Me_8",
    "mime":               "animations/Stand/Gestures/Mime_1",
    "mime_2":             "animations/Stand/Gestures/Mime_2",
    "next":               "animations/Stand/Gestures/Next_1",
    "no_gesture":         "animations/Stand/Gestures/No_1",
    "no_gesture_2":       "animations/Stand/Gestures/No_2",
    "no_gesture_3":       "animations/Stand/Gestures/No_3",
    "no_gesture_4":       "animations/Stand/Gestures/No_4",
    "no_gesture_5":       "animations/Stand/Gestures/No_5",
    "no_gesture_6":       "animations/Stand/Gestures/No_6",
    "no_gesture_7":       "animations/Stand/Gestures/No_7",
    "no_gesture_8":       "animations/Stand/Gestures/No_8",
    "no_gesture_9":       "animations/Stand/Gestures/No_9",
    "nothing":            "animations/Stand/Gestures/Nothing_1",
    "nothing_2":          "animations/Stand/Gestures/Nothing_2",
    "on_the_evening":     "animations/Stand/Gestures/OnTheEvening_1",
    "on_the_evening_2":   "animations/Stand/Gestures/OnTheEvening_2",
    "on_the_evening_3":   "animations/Stand/Gestures/OnTheEvening_3",
    "on_the_evening_4":   "animations/Stand/Gestures/OnTheEvening_4",
    "on_the_evening_5":   "animations/Stand/Gestures/OnTheEvening_5",
    "please":             "animations/Stand/Gestures/Please_1",
    "please_2":           "animations/Stand/Gestures/Please_2",
    "please_3":           "animations/Stand/Gestures/Please_3",
    "reject":             "animations/Stand/Gestures/Reject_1",
    "reject_2":           "animations/Stand/Gestures/Reject_2",
    "reject_3":           "animations/Stand/Gestures/Reject_3",
    "reject_4":           "animations/Stand/Gestures/Reject_4",
    "reject_5":           "animations/Stand/Gestures/Reject_5",
    "reject_6":           "animations/Stand/Gestures/Reject_6",
    "salute_anim":        "animations/Stand/Gestures/Salute_1",
    "salute_anim_2":      "animations/Stand/Gestures/Salute_2",
    "salute_anim_3":      "animations/Stand/Gestures/Salute_3",
    "shoot":              "animations/Stand/Gestures/Shoot_1",
    "show_floor":         "animations/Stand/Gestures/ShowFloor_1",
    "show_floor_2":       "animations/Stand/Gestures/ShowFloor_2",
    "show_floor_3":       "animations/Stand/Gestures/ShowFloor_3",
    "show_floor_4":       "animations/Stand/Gestures/ShowFloor_4",
    "show_floor_5":       "animations/Stand/Gestures/ShowFloor_5",
    "show_sky":           "animations/Stand/Gestures/ShowSky_1",
    "show_sky_2":         "animations/Stand/Gestures/ShowSky_2",
    "show_sky_3":         "animations/Stand/Gestures/ShowSky_3",
    "show_sky_4":         "animations/Stand/Gestures/ShowSky_4",
    "show_sky_5":         "animations/Stand/Gestures/ShowSky_5",
    "show_sky_6":         "animations/Stand/Gestures/ShowSky_6",
    "show_sky_7":         "animations/Stand/Gestures/ShowSky_7",
    "show_sky_8":         "animations/Stand/Gestures/ShowSky_8",
    "show_sky_9":         "animations/Stand/Gestures/ShowSky_9",
    "show_sky_10":        "animations/Stand/Gestures/ShowSky_10",
    "show_sky_11":        "animations/Stand/Gestures/ShowSky_11",
    "show_sky_12":        "animations/Stand/Gestures/ShowSky_12",
    "shy_gesture":        "animations/Stand/Gestures/Shy_1",
    "stretch_gesture":    "animations/Stand/Gestures/Stretch_1",
    "stretch_gesture_2":  "animations/Stand/Gestures/Stretch_2",
    "surprised_gesture":  "animations/Stand/Gestures/Surprised_1",
    "take":               "animations/Stand/Gestures/Take_1",
    "thinking_anim":      "animations/Stand/Gestures/Thinking_1",
    "thinking_anim_2":    "animations/Stand/Gestures/Thinking_2",
    "thinking_anim_3":    "animations/Stand/Gestures/Thinking_3",
    "thinking_anim_4":    "animations/Stand/Gestures/Thinking_4",
    "thinking_anim_5":    "animations/Stand/Gestures/Thinking_5",
    "thinking_anim_6":    "animations/Stand/Gestures/Thinking_6",
    "thinking_anim_7":    "animations/Stand/Gestures/Thinking_7",
    "thinking_anim_8":    "animations/Stand/Gestures/Thinking_8",
    "this":               "animations/Stand/Gestures/This_1",
    "this_2":             "animations/Stand/Gestures/This_2",
    "this_3":             "animations/Stand/Gestures/This_3",
    "this_4":             "animations/Stand/Gestures/This_4",
    "this_5":             "animations/Stand/Gestures/This_5",
    "this_6":             "animations/Stand/Gestures/This_6",
    "this_7":             "animations/Stand/Gestures/This_7",
    "this_8":             "animations/Stand/Gestures/This_8",
    "this_9":             "animations/Stand/Gestures/This_9",
    "this_10":            "animations/Stand/Gestures/This_10",
    "this_11":            "animations/Stand/Gestures/This_11",
    "this_12":            "animations/Stand/Gestures/This_12",
    "this_13":            "animations/Stand/Gestures/This_13",
    "this_14":            "animations/Stand/Gestures/This_14",
    "this_15":            "animations/Stand/Gestures/This_15",
    "whats_this":         "animations/Stand/Gestures/WhatSThis_1",
    "whats_this_2":       "animations/Stand/Gestures/WhatSThis_2",
    "whats_this_3":       "animations/Stand/Gestures/WhatSThis_3",
    "whats_this_4":       "animations/Stand/Gestures/WhatSThis_4",
    "whats_this_5":       "animations/Stand/Gestures/WhatSThis_5",
    "whats_this_6":       "animations/Stand/Gestures/WhatSThis_6",
    "whats_this_7":       "animations/Stand/Gestures/WhatSThis_7",
    "whats_this_8":       "animations/Stand/Gestures/WhatSThis_8",
    "whats_this_9":       "animations/Stand/Gestures/WhatSThis_9",
    "whats_this_10":      "animations/Stand/Gestures/WhatSThis_10",
    "whats_this_11":      "animations/Stand/Gestures/WhatSThis_11",
    "whats_this_12":      "animations/Stand/Gestures/WhatSThis_12",
    "whats_this_13":      "animations/Stand/Gestures/WhatSThis_13",
    "whats_this_14":      "animations/Stand/Gestures/WhatSThis_14",
    "whats_this_15":      "animations/Stand/Gestures/WhatSThis_15",
    "whats_this_16":      "animations/Stand/Gestures/WhatSThis_16",
    "wings":              "animations/Stand/Gestures/Wings_1",
    "wings_2":            "animations/Stand/Gestures/Wings_2",
    "wings_3":            "animations/Stand/Gestures/Wings_3",
    "wings_4":            "animations/Stand/Gestures/Wings_4",
    "wings_5":            "animations/Stand/Gestures/Wings_5",
    "yes_anim":           "animations/Stand/Gestures/Yes_1",
    "yes_anim_2":         "animations/Stand/Gestures/Yes_2",
    "yes_anim_3":         "animations/Stand/Gestures/Yes_3",
    "you":                "animations/Stand/Gestures/You_1",
    "you_2":              "animations/Stand/Gestures/You_2",
    "you_3":              "animations/Stand/Gestures/You_3",
    "you_4":              "animations/Stand/Gestures/You_4",
    "you_5":              "animations/Stand/Gestures/You_5",
    "you_know_what":      "animations/Stand/Gestures/YouKnowWhat_1",
    "you_know_what_2":    "animations/Stand/Gestures/YouKnowWhat_2",
    "you_know_what_3":    "animations/Stand/Gestures/YouKnowWhat_3",
    "you_know_what_4":    "animations/Stand/Gestures/YouKnowWhat_4",
    "you_know_what_5":    "animations/Stand/Gestures/YouKnowWhat_5",
    "you_know_what_6":    "animations/Stand/Gestures/YouKnowWhat_6",
    "yum":                "animations/Stand/Gestures/Yum_1",
    # --- Body language (speaking / listening / thinking) ---
    "bodytalk_1":         "animations/Stand/BodyTalk/Speaking/BodyTalk_1",
    "bodytalk_2":         "animations/Stand/BodyTalk/Speaking/BodyTalk_2",
    "bodytalk_3":         "animations/Stand/BodyTalk/Speaking/BodyTalk_3",
    "bodytalk_4":         "animations/Stand/BodyTalk/Speaking/BodyTalk_4",
    "bodytalk_5":         "animations/Stand/BodyTalk/Speaking/BodyTalk_5",
    "bodytalk_6":         "animations/Stand/BodyTalk/Speaking/BodyTalk_6",
    "bodytalk_7":         "animations/Stand/BodyTalk/Speaking/BodyTalk_7",
    "bodytalk_8":         "animations/Stand/BodyTalk/Speaking/BodyTalk_8",
    "bodytalk_9":         "animations/Stand/BodyTalk/Speaking/BodyTalk_9",
    "bodytalk_10":        "animations/Stand/BodyTalk/Speaking/BodyTalk_10",
    "bodytalk_11":        "animations/Stand/BodyTalk/Speaking/BodyTalk_11",
    "bodytalk_12":        "animations/Stand/BodyTalk/Speaking/BodyTalk_12",
    "bodytalk_13":        "animations/Stand/BodyTalk/Speaking/BodyTalk_13",
    "bodytalk_14":        "animations/Stand/BodyTalk/Speaking/BodyTalk_14",
    "bodytalk_15":        "animations/Stand/BodyTalk/Speaking/BodyTalk_15",
    "bodytalk_16":        "animations/Stand/BodyTalk/Speaking/BodyTalk_16",
    "bodytalk_17":        "animations/Stand/BodyTalk/Speaking/BodyTalk_17",
    "bodytalk_18":        "animations/Stand/BodyTalk/Speaking/BodyTalk_18",
    "bodytalk_19":        "animations/Stand/BodyTalk/Speaking/BodyTalk_19",
    "bodytalk_20":        "animations/Stand/BodyTalk/Speaking/BodyTalk_20",
    "bodytalk_21":        "animations/Stand/BodyTalk/Speaking/BodyTalk_21",
    "bodytalk_22":        "animations/Stand/BodyTalk/Speaking/BodyTalk_22",
    "listening_anim":     "animations/Stand/BodyTalk/Listening/Listening_2",
    "listening_left":     "animations/Stand/BodyTalk/Listening/ListeningLeft_1",
    "listening_right":    "animations/Stand/BodyTalk/Listening/ListeningRight_1",
    "remember":           "animations/Stand/BodyTalk/Thinking/Remember_1",
    "remember_2":         "animations/Stand/BodyTalk/Thinking/Remember_2",
    "remember_3":         "animations/Stand/BodyTalk/Thinking/Remember_3",
    "thinking_loop":      "animations/Stand/BodyTalk/Thinking/ThinkingLoop_1",
    "thinking_loop_2":    "animations/Stand/BodyTalk/Thinking/ThinkingLoop_2",
}

# QTrobot dance names → BEHAVIORS keys
QT_TO_NAO_BEHAVIOR = {
    # Short alias form (legacy)
    "dance":           "funny_dancer",
    "dance_funny":     "funny_dancer",
    "air_guitar":      "air_guitar",
    "bandmaster":      "bandmaster",
    "kung_fu":         "kung_fu",
    "robot_dance":     "robot_dance",
    "zombie":          "zombie",
    "happy_birthday":  "happy_birthday",
    "show_muscles":    "show_muscles",
    "fitness":         "fitness",
    "winner":          "winner",
    "hysterical":      "hysterical",
    "ecstatic":        "ecstatic",
    # Full QTrobot path form (from WOZ state table)
    "qt/happy":                        "happy_anim",
    "qt/laugh":                        "laugh_anim",
    "qt/yes":                          "yes_anim",
    "qt/no":                           "shake_head",
    "qt/so":                           "i_dont_know",
    "qt/so_what":                      "i_dont_know",
    "qt/curious":                      "puzzled",
    "qt/handclap":                     "applause",
    "qt/thanks":                       "bow",
    "qt/bye":                          "wave",
    "qt/strong":                       "show_muscles",
    "qt/challenge":                    "enthusiastic_g",
    "qt/bored":                        "bored_anim",
    "qt/angry":                        "angry_anim",
    "qt/yawn":                         "relaxation",
    "qt/stretch":                      "stretch_wait",
    "qt/peekaboo":                     "hide_eyes",
    "qt/head_scratch":                 "scratch_head",
    "qt/touch-head-back":              "scratch_head",
    "qt/monkey":                       "funny_dancer",
    "qt/hips":                         "funny_dancer",
    "qt/swipe_right":                  "far",
    "qt/show_tablet":                  "give",
    "qt/imitation/head-right-left":    "shake_head",
    "qt/imitation/hands-on-hip":       "show_muscles",
    "qt/imitation/nodding-yes":        "nod",
    # --- QTrobot full-path forms not yet mapped ---
    "qt/hi":                           "wave",
    "qt/surprise":                     "yay",
    "qt/touch-head":                   "pat_pat",
    "qt/emotions/sad":                 "sad",
    "qt/kiss":                         "love_you",
    "qt/face":                         "hide_eyes",
}

# Walking commands → (linear.x, linear.y, angular.z) at full speed
# Max speeds at speed=1.0: forward/backward 0.35 m/s, lateral 0.2 m/s, rotation 0.5 rad/s
WALK_CMDS = {
    "walk_forward":  ( 0.35,  0.0,  0.0),
    "walk_backward": (-0.35,  0.0,  0.0),
    "walk_left":     ( 0.0,   0.2,  0.0),
    "walk_right":    ( 0.0,  -0.2,  0.0),
    "turn_left":     ( 0.0,   0.0,  0.5),
    "turn_right":    ( 0.0,   0.0, -0.5),
    "stop":          ( 0.0,   0.0,  0.0),
}


class NaoBridge(RobotBridge):
    """NAO / Pepper bridge adapter: qi SDK → NAOqi service calls."""

    SUPPORTED_TYPES = ("nao", "pepper")

    def __init__(self):
        super().__init__("nao_bridge")
        # NAOqi connection parameters (set from ROS2 launch args)
        self.declare_parameter("naoqi_host", "192.168.1.100")
        self.declare_parameter("naoqi_port", 9559)
        self.declare_parameter("naoqi_scheme", "tcp")       # tcp or tcps (TLS gateway)
        self.declare_parameter("naoqi_ssl_cert", "")        # CA cert for tcps
        # Connection state
        self._host = ""
        self._port = 9559
        self._scheme = "tcp"
        self._ssl_cert = ""
        # qi SDK session and service proxies (None when not connected)
        self._qi_session = None
        self._posture_proxy = None
        self._leds_proxy = None
        self._motion_proxy = None
        self._tts_proxy = None
        self._behavior_proxy = None
        self._gesture_stop = threading.Event()  # set to interrupt a running gesture
        self._reconnect_lock = threading.Lock()  # prevents concurrent reconnect threads
        # TTS lock: ensures only one say() call runs at a time so NAOqi doesn't
        # queue a second speech when the same command slips past the dedup window.
        # Non-blocking acquire: if TTS is already speaking, drop the duplicate.
        self._tts_lock = threading.Lock()
        # Fallback publishers used when qi SDK is unavailable
        self._speech_pub = self.create_publisher(String, "/speech", 10)
        self._joint_pub = self.create_publisher(JointAnglesWithSpeed, "/joint_angles", 10)
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.add_on_set_parameters_callback(self._on_param_change)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_param_change(self, params):
        """Reconnect immediately when naoqi_host is changed at runtime."""
        from rcl_interfaces.msg import SetParametersResult
        for p in params:
            if p.name == 'naoqi_host' and self._active:
                new_host = p.value  # rclpy Parameter.value is already a Python str
                if new_host and new_host != self._host:
                    self._host = new_host
                    self.get_logger().info(
                        f'[NaoBridge] naoqi_host → {new_host}, reconnecting'
                    )
                    threading.Thread(target=self._reconnect, daemon=True).start()
        return SetParametersResult(successful=True)

    def _on_activate(self, msg: RobotConfig):
        """Read NAOqi connection parameters from the launch configuration."""
        self._host = self.get_parameter("naoqi_host").get_parameter_value().string_value
        self._port = self.get_parameter("naoqi_port").get_parameter_value().integer_value
        self._scheme = self.get_parameter("naoqi_scheme").get_parameter_value().string_value or "tcp"
        self._ssl_cert = self.get_parameter("naoqi_ssl_cert").get_parameter_value().string_value
        self.get_logger().info(
            f"[NaoBridge] Connecting to {self._scheme}://{self._host}:{self._port}"
        )

    def _on_deactivate(self):
        """Clear all proxies so they are not used after deactivation."""
        self._qi_session = None
        self._posture_proxy = None
        self._leds_proxy = None
        self._motion_proxy = None
        self._tts_proxy = None
        self._behavior_proxy = None

    def connect(self):
        """Open a qi session and acquire all service proxies."""
        if not _HAS_QI:
            self.get_logger().warning(
                "[NaoBridge] qi SDK not available — posture/LED commands disabled."
            )
            return
        try:
            url = f"{self._scheme}://{self._host}:{self._port}"
            if self._scheme == "tcps" and self._ssl_cert:
                app_args = ["nao_bridge", "--qi-url", url, "--qi-ssl-ca-cert", self._ssl_cert]
                app = qi.Application(app_args)
                app.start()
                session = app.session
            else:
                session = qi.Session()
                session.listen("tcp://0.0.0.0:0")
                session.connect(url)
            self._qi_session = session
            self._posture_proxy = session.service("ALRobotPosture")
            self._leds_proxy = session.service("ALLeds")
            self._motion_proxy = session.service("ALMotion")
            self._tts_proxy = session.service("ALTextToSpeech")
            self._behavior_proxy = session.service("ALBehaviorManager")
            # Clear any TTS speech that was queued during a previous session
            # (e.g. from duplicate say() calls before the node was killed).
            try:
                self._tts_proxy.stopAll()
            except Exception:
                pass
            # Disable ALAutonomousLife for the whole session so it never fights
            # incoming motion commands (it re-applies postures and interrupts moves).
            # We deliberately do NOT restore it on disconnect — the user can re-enable
            # it manually via the tablet or a reboot.
            try:
                life = session.service("ALAutonomousLife")
                state = life.getState()
                if state != "disabled":
                    life.setState("disabled")
                    self.get_logger().info(
                        f"[NaoBridge] ALAutonomousLife disabled (was '{state}')."
                    )
            except Exception:
                pass
            # Wake up motors once at connect so the robot is immediately ready.
            try:
                self._motion_proxy.wakeUp()
            except Exception:
                pass
            self.get_logger().info(
                "[NaoBridge] qi session connected — posture, LED, TTS & behaviors available."
            )
            self.create_timer(60.0, self._keepalive)
        except Exception as exc:
            self.get_logger().warning(
                f"[NaoBridge] qi connect failed: {exc} — posture/LED in dry-run mode."
            )
            self._qi_session = None

    def disconnect(self):
        """Clear proxies on deactivation or shutdown."""
        self._on_deactivate()

    def _keepalive(self):
        """Ping NAOqi every 60 s to keep the TCP connection alive; reconnect on failure."""
        if not self._active or self._qi_session is None:
            return
        try:
            self._tts_proxy.getLanguage()
        except Exception:
            self.get_logger().warning("[NaoBridge] Keepalive failed — reconnecting...")
            threading.Thread(target=self._reconnect, daemon=True).start()

    def _reconnect(self):
        """Clear proxies and retry connect() up to 5 times with backoff.

        Uses a lock to prevent concurrent reconnect threads (e.g. from
        simultaneous keepalive failure and a command error).
        """
        if not self._reconnect_lock.acquire(blocking=False):
            return  # reconnect already in progress
        try:
            self._on_deactivate()
            for attempt in range(1, 6):
                try:
                    time.sleep(min(5 * attempt, 30))
                    self.connect()
                    if self._qi_session is not None:
                        self.get_logger().info("[NaoBridge] Reconnected successfully.")
                        return
                except Exception:
                    pass
                self.get_logger().warning(f"[NaoBridge] Reconnect attempt {attempt}/5 failed.")
            self.get_logger().error("[NaoBridge] Could not reconnect after 5 attempts.")
        finally:
            self._reconnect_lock.release()

    def _is_connection_error(self, exc):
        """True if the exception looks like a dropped TCP connection."""
        msg = str(exc).lower()
        return any(k in msg for k in (
            "socket", "not connected", "disconnected", "broken pipe", "connection reset"
        ))

    # ------------------------------------------------------------------
    # speak
    # ------------------------------------------------------------------

    def do_speak(self, msg: RobotCmd):
        """Speak text via ALTextToSpeech (or fallback /speech topic)."""
        if not msg.text:
            return
        naoqi_lang = LANG_MAP.get(msg.language or "fr-FR", "French")
        self.get_logger().info(f"[NaoBridge] speak [{naoqi_lang}]: {msg.text}")
        if self._tts_proxy is not None:
            threading.Thread(
                target=self._tts_say, args=(naoqi_lang, msg.text), daemon=True
            ).start()
        else:
            out = String()
            out.data = f"\\lang={naoqi_lang}\\ {msg.text}"
            self._speech_pub.publish(out)

    def _tts_say(self, lang, text):
        if not self._tts_lock.acquire(blocking=False):
            self.get_logger().warning("[NaoBridge] TTS busy — duplicate speak dropped.")
            return
        try:
            self._tts_proxy.stopAll()      # cancel any lingering queued speech
            self._tts_proxy.setLanguage(lang)
            self.get_logger().info(f"[NaoBridge] TTS → calling say()")
            self._tts_proxy.say(text)
            self.get_logger().info(f"[NaoBridge] TTS ← say() returned")
        except Exception as exc:
            self.get_logger().error(f"[NaoBridge] TTS error: {exc}")
            if self._is_connection_error(exc):
                threading.Thread(target=self._reconnect, daemon=True).start()
        finally:
            self._tts_lock.release()

    # ------------------------------------------------------------------
    # move
    # ------------------------------------------------------------------

    def do_move(self, msg: RobotCmd):
        """Dispatch a move command: behavior → gesture → walk → posture → raw joints."""
        name = (msg.motion_name or "").strip()
        if not name:
            self.get_logger().warning("[NaoBridge] move: motion_name is empty.")
            return

        speed = max(0.1, msg.speed)

        # Raw behavior path escape hatch: "behavior:path/to/behavior"
        if name.lower().startswith("behavior:"):
            behavior_path = name[len("behavior:"):]
            self._gesture_stop.set()
            self._gesture_stop = threading.Event()
            threading.Thread(
                target=self._run_behavior,
                args=(behavior_path, self._gesture_stop),
                daemon=True,
            ).start()
            return

        # Translate QTrobot behavior names
        if name.lower() in QT_TO_NAO_BEHAVIOR:
            name = QT_TO_NAO_BEHAVIOR[name.lower()]

        # Built-in NAOqi animation behaviors
        if name.lower() in BEHAVIORS:
            behavior_path = BEHAVIORS[name.lower()]
            self._gesture_stop.set()
            self._gesture_stop = threading.Event()
            threading.Thread(
                target=self._run_behavior,
                args=(behavior_path, self._gesture_stop),
                daemon=True,
            ).start()
            self.get_logger().info(f"[NaoBridge] behavior → {behavior_path}")
            return

        # Translate universal/QTrobot names to NAO gesture names
        if name.lower() in QT_TO_NAO_MOTION:
            mapped = QT_TO_NAO_MOTION[name.lower()]
            if mapped is None:
                self.get_logger().info(
                    f"[NaoBridge] move: '{name}' has no NAO equivalent — skipped."
                )
                return
            self.get_logger().info(f"[NaoBridge] move: '{name}' → '{mapped}'")
            name = mapped

        # Predefined gesture sequences
        if name.lower() in GESTURES:
            self._gesture_stop.set()   # stop any running gesture first
            self._gesture_stop = threading.Event()
            threading.Thread(
                target=self._execute_gesture,
                args=(name.lower(), speed, self._gesture_stop),
                daemon=True,
            ).start()
            self.get_logger().info(f"[NaoBridge] gesture → {name}")
            return

        # Any other motion stops a running gesture
        self._gesture_stop.set()

        # Walking commands via ALMotion.moveToward (no naoqi_driver2 needed)
        if name.lower() in WALK_CMDS:
            vx, vy, vth = WALK_CMDS[name.lower()]
            vx  *= speed
            vy  *= speed
            vth *= speed
            self.get_logger().info(
                f"[NaoBridge] walk '{name}' → vx={vx:.3f} vy={vy:.3f} vth={vth:.3f}"
            )
            if self._motion_proxy is not None:
                def _do_walk():
                    try:
                        self._motion_proxy.wakeUp()
                        self._motion_proxy.setStiffnesses("Body", 1.0)
                        if name.lower() == "stop":
                            self._motion_proxy.stopMove()
                        else:
                            if self._posture_proxy is not None:
                                self._posture_proxy.goToPosture("Stand", 0.5)
                            self._motion_proxy.moveInit()
                            self._motion_proxy.moveToward(vx, vy, vth)
                    except Exception as exc:
                        self.get_logger().error(f"[NaoBridge] walk error: {exc}")
                threading.Thread(target=_do_walk, daemon=True).start()
            else:
                # Fallback: /cmd_vel for naoqi_driver2
                twist = Twist()
                twist.linear.x  = vx
                twist.linear.y  = vy
                twist.angular.z = vth
                self._cmd_vel_pub.publish(twist)
            return

        # Named postures via ALRobotPosture
        if name.lower() in POSTURE_NAMES:
            naoqi_name = POSTURE_NAMES[name.lower()]
            if self._posture_proxy is not None:
                threading.Thread(
                    target=self._posture_proxy.goToPosture,
                    args=(naoqi_name, speed),
                    daemon=True,
                ).start()
                self.get_logger().info(f"[NaoBridge] posture → {naoqi_name} @ {speed:.2f}")
            else:
                self.get_logger().warning(
                    f"[NaoBridge][DRY-RUN] posture → {naoqi_name} @ {speed:.2f} (qi not connected)"
                )
            return

        # Raw joint control: "Joint:angle,Joint:angle,…" in radians
        # Hands (LHand/RHand) require angleInterpolation; other joints use setAngles
        if ":" in name:
            try:
                pairs = [p.strip().split(":") for p in name.split(",")]
                joint_names  = [p[0].strip() for p in pairs]
                joint_angles = [float(p[1].strip()) for p in pairs]
                hand_joints  = [(j, a) for j, a in zip(joint_names, joint_angles)
                                if j in ("LHand", "RHand")]
                body_joints  = [(j, a) for j, a in zip(joint_names, joint_angles)
                                if j not in ("LHand", "RHand")]
                if self._motion_proxy is not None:
                    if body_joints:
                        self._motion_proxy.setAngles(
                            [j for j, _ in body_joints],
                            [float(a) for _, a in body_joints],
                            speed,
                        )
                    if hand_joints:
                        self._motion_proxy.angleInterpolation(
                            [j for j, _ in hand_joints],
                            [[float(a)] for _, a in hand_joints],
                            [[1.0] for _ in hand_joints],
                            True,
                        )
                else:
                    jmsg = JointAnglesWithSpeed()
                    jmsg.joint_names  = [j for j, _ in body_joints] or joint_names
                    jmsg.joint_angles = [float(a) for _, a in body_joints] or joint_angles
                    jmsg.speed = speed
                    jmsg.relative = 0
                    self._joint_pub.publish(jmsg)
                self.get_logger().info(f"[NaoBridge] joints: {name} @ speed={speed:.2f}")
            except Exception as exc:
                self.get_logger().error(f"[NaoBridge] joint parse error: {exc}")
        else:
            if name.lower().startswith("qt/"):
                self.get_logger().debug(f"[NaoBridge] QT-only animation skipped on NAO: '{name}'")
            else:
                self.get_logger().warning(
                    f"[NaoBridge] Unknown motion_name '{name}'. "
                    "Use a posture keyword (Stand/Sit/…), a gesture name, or 'Joint:angle,…' format."
                )

    def _run_behavior(self, behavior_path, stop_event):
        """Run an installed NAOqi behavior; warn if not found on this robot."""
        if self._behavior_proxy is None:
            self.get_logger().warning(
                f"[NaoBridge][DRY-RUN] behavior '{behavior_path}' (qi not connected)"
            )
            return
        try:
            if not self._behavior_proxy.isBehaviorInstalled(behavior_path):
                self.get_logger().warning(
                    f"[NaoBridge] Behavior '{behavior_path}' not found on this robot. "
                    "Check with: qicli call ALBehaviorManager.getInstalledBehaviors"
                )
                return
            self.get_logger().info(f"[NaoBridge] Running behavior: {behavior_path}")
            self._behavior_proxy.runBehavior(behavior_path)  # blocking until done
        except Exception as exc:
            if not stop_event.is_set():
                self.get_logger().error(f"[NaoBridge] behavior error: {exc}")
        finally:
            try:
                self._behavior_proxy.stopBehavior(behavior_path)
            except Exception:
                pass

    def _run_steps(self, steps, speed, stop_event):
        """Execute a sequence of (joints, angles, speed, pause) steps; returns False if interrupted."""
        for joint_names, joint_angles, step_speed, pause in steps:
            if stop_event.is_set():
                return False
            effective_speed = float(min(speed, 1.0))
            if self._motion_proxy is not None:
                try:
                    # angleInterpolationWithSpeed moves all joints simultaneously
                    # and blocks until done — hands included
                    self._motion_proxy.angleInterpolationWithSpeed(
                        list(joint_names),
                        [float(a) for a in joint_angles],
                        effective_speed,
                    )
                except Exception as exc:
                    self.get_logger().error(f"[NaoBridge] motion error: {exc}")
                    if self._is_connection_error(exc):
                        threading.Thread(target=self._reconnect, daemon=True).start()
                    return False
            else:
                jmsg = JointAnglesWithSpeed()
                jmsg.joint_names = joint_names
                jmsg.joint_angles = [float(a) for a in joint_angles]
                jmsg.speed = effective_speed
                jmsg.relative = 0
                self._joint_pub.publish(jmsg)
            if pause > 0:
                time.sleep(pause / speed)
        return True

    @staticmethod
    def _gesture_joints(gesture):
        """Collect all joint names used by a gesture (for selective stiffening)."""
        joints = set()
        steps = gesture if isinstance(gesture, list) else (
            gesture.get("init", []) + gesture.get("loop", []) + gesture.get("cleanup", [])
        )
        for joint_names, *_ in steps:
            joints.update(joint_names)
        return list(joints)

    def _execute_gesture(self, name, speed, stop_event):
        """Run a named gesture from GESTURES; handles both one-shot and looping types."""
        if self._motion_proxy is not None:
            try:
                self._motion_proxy.wakeUp()
            except Exception:
                pass
            try:
                # Only stiffen the joints this gesture uses — relaxed parts stay relaxed
                used_joints = self._gesture_joints(GESTURES[name])
                self._motion_proxy.setStiffnesses(used_joints, [1.0] * len(used_joints))
            except Exception as exc:
                self.get_logger().warning(f"[NaoBridge] setStiffnesses failed: {exc}")
        gesture = GESTURES[name]
        if isinstance(gesture, list):
            self._run_steps(gesture, speed, stop_event)
        else:
            if not self._run_steps(gesture["init"], speed, stop_event):
                return
            while not stop_event.is_set():
                if not self._run_steps(gesture["loop"], speed, stop_event):
                    break
            self._run_steps(gesture["cleanup"], speed, threading.Event())

    # ------------------------------------------------------------------
    # display
    # ------------------------------------------------------------------

    def do_display(self, msg: RobotCmd):
        """Set LED colors: by led_name+color, or by emotion name."""
        duration = max(0.5, msg.duration_ms / 1000.0) if msg.duration_ms > 0 else 3.0

        # Direct LED color control: led_name + color fields
        if msg.led_name:
            group_key = msg.led_name.lower().strip()
            color_str = (msg.color or "white").strip()
            led_map = LED_GROUPS_PEPPER if self._robot_type == "pepper" else LED_GROUPS_NAO
            naoqi_group = led_map.get(group_key)
            if naoqi_group is None:
                self.get_logger().warning(
                    f"[NaoBridge] unknown led_name '{group_key}'. "
                    f"Valid: {', '.join(led_map.keys())}"
                )
                return
            rgb = _parse_color(color_str)
            if rgb is None:
                self.get_logger().warning(
                    f"[NaoBridge] unknown color '{color_str}'. "
                    "Use '#RRGGBB' or: red, green, blue, white, yellow, cyan, magenta, orange, purple, pink, off."
                )
                return
            r, g, b = rgb
            color_int = (r << 16) | (g << 8) | b
            self.get_logger().info(
                f"[NaoBridge] display led '{group_key}' ({naoqi_group}) → "
                f"#{r:02X}{g:02X}{b:02X} for {duration:.1f}s"
            )
            if self._leds_proxy is not None:
                threading.Thread(
                    target=self._leds_proxy.fadeRGB,
                    args=(naoqi_group, color_int, duration),
                    daemon=True,
                ).start()
            else:
                self.get_logger().warning("[NaoBridge][DRY-RUN] led (qi not connected)")
            return

        # Emotion → face + chest/shoulder LEDs
        emotion = (msg.emotion or "neutral").lower().strip()
        rgb_f = EMOTION_LEDS.get(emotion, EMOTION_LEDS["neutral"])
        r = int(rgb_f[0] * 255) & 0xFF
        g = int(rgb_f[1] * 255) & 0xFF
        b = int(rgb_f[2] * 255) & 0xFF
        color_int = (r << 16) | (g << 8) | b
        if self._leds_proxy is not None:
            emotion_groups = (
                ("FaceLeds", "ShoulderLeds") if self._robot_type == "pepper"
                else ("FaceLeds", "ChestLeds")
            )
            def _fade_group(g):
                try:
                    self._leds_proxy.fadeRGB(g, color_int, duration)
                except Exception as exc:
                    self.get_logger().warning(
                        f"[NaoBridge] LED group '{g}' not available: {exc}"
                    )
            for group in emotion_groups:
                threading.Thread(target=_fade_group, args=(group,), daemon=True).start()
            self.get_logger().info(
                f"[NaoBridge] display '{emotion}' → "
                f"{'+'.join(emotion_groups)} RGB=({r},{g},{b}) for {duration:.1f}s"
            )
        else:
            self.get_logger().warning(
                f"[NaoBridge][DRY-RUN] display '{emotion}' → "
                f"RGB=({r},{g},{b}) for {duration:.1f}s (qi not connected)"
            )

    # ------------------------------------------------------------------
    # relax / stiffen
    # ------------------------------------------------------------------

    # NAOqi body-part names accepted by ALMotion.setStiffnesses
    _STIFFNESS_PARTS = {
        "body":              "Body",
        "head":              "Head",
        "larm":              "LArm",
        "rarm":              "RArm",
        "left_arm":          "LArm",
        "right_arm":         "RArm",
        "arms":              "Arms",
        "lhand":             "LHand",
        "rhand":             "RHand",
        "left_hand":         "LHand",
        "right_hand":        "RHand",
        "lleg":              "LLeg",
        "rleg":              "RLeg",
        "left_leg":          "LLeg",
        "right_leg":         "RLeg",
        "legs":              "Legs",
        # Arm without hand (shoulder + elbow + wrist only)
        "larm_no_hand":      ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"],
        "rarm_no_hand":      ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"],
        "left_arm_no_hand":  ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"],
        "right_arm_no_hand": ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"],
        "arms_no_hand":      ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw",
                              "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"],
    }

    def do_stiffness(self, msg: RobotCmd, stiff: bool):
        """Set joint stiffness to 0 (relax) or 1 (stiffen) for the specified body part."""
        part_key = (msg.motion_name or "body").strip().lower()
        naoqi_part = self._STIFFNESS_PARTS.get(part_key, part_key)
        value = 1.0 if stiff else 0.0
        label = "stiffen" if stiff else "relax"
        self.get_logger().info(f"[NaoBridge] {label} → {naoqi_part} (stiffness={value})")
        if self._motion_proxy is not None:
            threading.Thread(
                target=self._apply_stiffness,
                args=(naoqi_part, value, label),
                daemon=True,
            ).start()
        else:
            self.get_logger().warning(
                f"[NaoBridge][DRY-RUN] {label} '{naoqi_part}' (qi not connected)"
            )

    def _apply_stiffness(self, naoqi_part, value, label):
        try:
            # Full-body relax: use rest() so Pepper's safety system cooperates
            # (setStiffnesses("Body", 0.0) is silently blocked while standing).
            # Partial relax (arms, head, …) can skip directly to setStiffnesses.
            if value == 0.0 and naoqi_part == "Body":
                self._motion_proxy.rest()
            else:
                self._motion_proxy.setStiffnesses(naoqi_part, value)
            self.get_logger().info(f"[NaoBridge] {label} '{naoqi_part}' done.")
        except Exception as exc:
            self.get_logger().error(f"[NaoBridge] stiffness error: {exc}")
            if self._is_connection_error(exc):
                threading.Thread(target=self._reconnect, daemon=True).start()


def main(args=None):
    rclpy.init(args=args)
    node = NaoBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
