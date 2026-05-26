#!/usr/bin/env python3
# QTrobot bridge adapter.
# Translates RobotCmd messages into QTrobot ROS1 calls forwarded over rosbridge (roslibpy).
import threading
import time
import rclpy
from ros2_robot_bridge.base_bridge import RobotBridge
from ros2_robot_bridge.msg import RobotCmd, RobotConfig

try:
    import roslibpy
    _HAS_ROSLIBPY = True
except ImportError:
    _HAS_ROSLIBPY = False

# Versioned topic names for speech, gesture, and display
QT_TOPICS = {
    "qt1": {
        "speech":          "/qt_robot/speech/say",
        "move":            "/qt_robot/gesture/play",
        "display_emotion": "/qt_robot/emotion/show",
        "display_image":   "/qt_robot/display/image",
    },
    "qt2": {
        "speech":          "/qt_robot/speech/say",
        "move":            "/qt_robot/gesture/play",
        "display_emotion": "/qt_robot/face/emotion",
        "display_image":   "/qt_robot/display/image",
    },
}

# Joint trajectory topics — routed by joint name prefix
QT_JOINT_TOPICS = {
    "head":  "/qt_robot/head_position/command",
    "left":  "/qt_robot/left_arm_position/command",
    "right": "/qt_robot/right_arm_position/command",
}

# Positional order for each Float64MultiArray command topic
QT_JOINT_ORDER = {
    "head":  ["HeadPitch", "HeadYaw"],
    "left":  ["LeftShoulderPitch", "LeftShoulderRoll", "LeftElbowRoll"],
    "right": ["RightShoulderPitch", "RightShoulderRoll", "RightElbowRoll"],
}

# Universal motion name → QTrobot gesture path.
# Two kinds of values:
#   - plain name / relative path  → prefixed with "QT/"   e.g. "hi" → "QT/hi"
#   - starts with "@"             → used as-is (absolute) e.g. "@univ-paris8-2/Gifle"
# None = no equivalent on QTrobot (silently ignored).
# IMPORTANT: QTrobot gesture service is case-sensitive — "Fly" ≠ "fly"
QT_MOTION_MAP = {
    # --- Greetings / waves ---
    "wave":                       "hi",
    "salute":                     "hi",
    "salute_anim":                "hi",
    "hey":                        "hi",
    "kisses":                     "send_kiss",
    "kiss":                       "kiss",
    "bye":                        "bye",
    "adieu":                      "adieu",
    # --- Head ---
    "nod":                        "yes",
    "yes_anim":                   "yes",
    "shake_head":                 "no",
    "look_left":                  "head-right-left",
    "look_right":                 "head-right-left",
    "look_up":                    "yawn",
    "yawn":                       "yawn",
    "look_down":                  None,
    "head_scratch":               "head_scratch",
    "sneezing":                   "sneezing",
    "sneeze_anim":                "sneezing",
    # --- Arms / body ---
    "arms_open":                  "hug",
    "point_forward":              "point_front",
    "think":                      "curious",
    "thinking_anim":              "curious",
    "confused_anim":              "curious",
    "mischievous":                "curious",
    "arm_up":                     "one-arm-up",
    "refuse":                     "refuse",
    "stubborn":                   "refuse",
    "hoora":                      "hoora",
    "yay":                        "hoora",
    "ecstatic":                   "hoora",
    "excited_anim":               "hoora",
    "winner":                     "hoora",
    "winner_2":                   "hoora",
    "optimistic":                 "hoora",
    "joy_anim":                   "hoora",
    "come_on":                    "come",
    "clapping":                   "clapping",
    "play_hands":                 "clapping",
    "peekaboo":                   "peekaboo",
    "peekaboo-back":              "peekaboo-back",
    "peekaboo_back":              "peekaboo-back",
    "hide_eyes":                  "peekaboo",
    "hide_hands":                 "peekaboo",
    "ohno":                       "ohno",
    "shocked":                    "ohno",
    "hips":                       "hips",
    "drink":                      "drink",
    "drink_wait":                 "drink",
    "monkey":                     "monkey",
    "ecrit":                      "ecrit",
    "show_tablet":                "show_tablet",
    "breathing_exercise":         "breathing_exercise",
    "neutral":                    "neutral",
    "innocent_anim":              "neutral",
    "relieved":                   "neutral",
    "sad":                        "sad",
    "sad_anim":                   "sad",
    "disappointed":               "sad",
    "sorry":                      "sad",
    "touch_head_back":            "touch-head-back",
    "hands_on_head":              "hands-on-head",
    "hands_on_belly":             "hands-on-belly",
    "hands_on_hip":               "hands-on-hip",
    "hands_up":                   "hands-up",
    "personal_distance":          "personal-distance",
    "premiere_rencontre":         "premiere_rencontre",
    "premiere_recontre":          "premiere_recontre",
    "fera_mieux":                 "fera_mieux",
    "grandpa":                    "grandpa",
    "luxai_en":                   "luxai_en",
    "stretch_wait":               "stretch",
    "show_muscles":               "strong",
    "confident":                  "strong",
    "proud":                      "strong",
    "enthusiastic":               "challenge",
    "scratch_head":               "head_scratch",
    "love_you":                   "send_kiss",
    "hysterical":                 "laugh",
    "laugh_anim":                 "laugh",
    "amused":                     "laugh",
    "happy_anim":                 "happy",
    "angry_anim":                 "angry",
    "frustrated":                 "angry",
    "bored_anim":                 "bored",
    "exhausted":                  "bored",
    "surprised_anim":             "surprise",
    # --- Emotions subfolder — only at QT/emotions/<name>, NOT at QT/<name> ---
    "surprised":                  "emotions/surprised",
    "disgusted":                  "emotions/disgusted",
    "calm":                       "emotions/calm",
    "afraid":                     "emotions/afraid",
    "shy":                        "emotions/shy",
    "embarrassed":                "emotions/shy",
    # --- Imitation subfolder — only at QT/imitation/<name> ---
    "hands_side":                 "imitation/hands-side",
    "hands_side_back":            "imitation/hands-side-back",
    "hands_on_head_back":         "imitation/hands-on-head-back",
    "hands_on_hip_back":          "imitation/hands-on-hip-back",
    "hands_on_belly_back":        "imitation/hands-on-belly-back",
    "hands_up_back":              "imitation/hands-up-back",
    # --- Handled by QT_CUSTOM_GESTURES (joint keyframe sequences, see below) ---
    "fly":                        None,
    "beep":                       None,
    "drive":                      None,
    "driving":                    None,
    "beeping":                    None,
    "phone_call":                 None,
    "pretend_play":               None,
    "show_face":                  None,
    "show_qt":                    None,
    "qt":                         "show_QT",
    "swipe_right":                "swipe_right",
    "swipe_left":                 "swipe_left",
    # --- Dances (Dance-X-X variants are under QT/ on this robot) ---
    "dance":                      "@Dance-1-1",
    "dance_1_1":                  "@Dance-1-1",
    "dance_1_2":                  "@Dance-1-2",
    "dance_1_3":                  "@Dance-1-3",
    "dance_1_4":                  "@Dance-1-4",
    "dance_2_1":                  "@Dance-2-1",
    "dance_2_2":                  "@Dance-2-2",
    "dance_2_3":                  "@Dance-2-3",
    "dance_2_4":                  "@Dance-2-4",
    "dance_3_1":                  "@Dance-3-1",
    "dance_3_2":                  "@Dance-3-2",
    "dance_3_3":                  "@Dance-3-3",
    "dance_4_1":                  "@Dance-4-1",
    "dance_4_2":                  "@Dance-4-2",
    "dance_4_3":                  "@Dance-4-3",
    "dance_4_4":                  "@Dance-4-4",
    "dance_4_5":                  "@Dance-4-5",
    "dance_4_6":                  "@Dance-4-6",
    # --- Built-in behavior dances → closest QTrobot dance ---
    "funny_dancer":               "@Dance",
    "air_guitar":                 "@Dance",
    "bandmaster":                 "@Dance",
    "robot_dance":                "@Dance",
    # --- Custom university package (univ-paris8-2) — "@" = absolute path, no "QT/" prefix ---
    "gifle":                      "@univ-paris8-2/Gifle",
    "kill":                       "@univ-paris8-2/Kill",
    "ymca":                       "@univ-paris8-2/Ymca",
    "dancing_arms":               "@univ-paris8-2/Dancing.arms",
    "left_righ":                  "@univ-paris8-2/LeftRigh",
    "bla":                        "@univ-paris8-2/Bla",
    "soleil":                     "@univ-paris8-2/QT/Soleil",
    "movinghead":                 "@univ-paris8-2/Movinghead",
    "headright":                  "@univ-paris8-2/Headright",
    "headleft":                   "@univ-paris8-2/Headleft",
    "draw":                       "@univ-paris8-2/Draw",
    "tetehaute":                  "@univ-paris8-2/Tetehaute",
    "tournepoigne":               "@univ-paris8-2/Tournepoigne",
    "hackathon":                  "@univ-paris8-2/Hackathon",
    "fullciao":                   "@univ-paris8-2/FullCiao",
    "ciao":                       "@univ-paris8-2/Ciao",
    "very_sad":                   "@univ-paris8-2/very_sad",
    "very_sad2":                  "@univ-paris8-2/very_sad2",
    "tired":                      "@univ-paris8-2/Tired",
    # --- Hand gestures ---
    "give_hand":                  "hand-front-hold",
    "give_hand_right":            "hand-front-hold",
    "give_hand_sitted":           "hand-front-hold",
    "give_hand_sitted_right":     "hand-front-hold",
    "pat_pat":                    "touch-head",
    # --- NAO waiting animations → closest QT equivalent ---
    "look_down":                  "yes",
    "close_right_hand":           "give_hand",
    "close_left_hand":            "give_hand",
    "six_seven":                  "hips",
    "kung_fu":                    "challenge",
    "zombie":                     "hug",
    "helicopter":                 None,
    "space_shuttle":              "one-arm-up",
    "drive_car":                  None,   # handled by QT_CUSTOM_GESTURES alias
    "fitness":                    "stretch",
    "fitness_2":                  "stretch",
    "fitness_3":                  "stretch",
    "monster":                    "angry",
    "mystical_power":             "hoora",
    "waddle":                     "hips",
    "waddle_2":                   "hips",
    "wake_up":                    "stretch",
    "bow":                        "yes",
    "calm_down":                  "emotions/calm",
    "calm_down_2":                "emotions/calm",
    "calm_down_3":                "emotions/calm",
    "calm_down_4":                "emotions/calm",
    "calm_down_5":                "emotions/calm",
    "calm_down_6":                "emotions/calm",
    "wings":                      "hug",
    "wings_2":                    "hug",
    "wings_3":                    "hug",
    "wings_4":                    "hug",
    "wings_5":                    "hug",
    "fearful":                    "emotions/afraid",
    "back_rubs":                  "head_scratch",
    "binoculars":                 "curious",
    "call_someone":               None,
    "knock_eye":                  "curious",
    "look_hand":                  "curious",
    "look_hand_2":                "curious",
    "take_picture":               "show_face",
    "taxi":                       "one-arm-up",
    "air_juggle":                 None,
    "funny_slide":                "@Dance",
    "headbang":                   "@Dance",
    "knight":                     "challenge",
    "vacuum":                     "hug",
    "happy_birthday":             "hoora",
    "show_muscles_2":             "strong",
    "show_muscles_3":             "strong",
    "show_muscles_4":             "strong",
    "show_muscles_5":             "strong",
    "stretch_wait_2":             "stretch",
    "stretch_wait_3":             "stretch",
    "relaxation":                 "breathing_exercise",
    "relaxation_2":               "breathing_exercise",
    "relaxation_3":               "breathing_exercise",
    "relaxation_4":               "breathing_exercise",
    "rest":                       "neutral",
    "scratch_back":               "head_scratch",
    "scratch_eye":                "head_scratch",
    "scratch_hand":               "head_scratch",
    "scratch_torso":              "head_scratch",
    "show_sky_wait":              "one-arm-up",
    "show_sky_wait_2":            "one-arm-up",
    "innocent_wait":              "neutral",
    "play_hands_2":               "clapping",
    "play_hands_3":               "clapping",
    # --- NAO emotion variants → QT equivalents ---
    "hungry_anim":                "drink",
    "mocker":                     "laugh",
    "peaceful":                   "emotions/calm",
    "shy_anim":                   "emotions/shy",
    "shy_anim_2":                 "emotions/shy",
    "sure":                       "strong",
    "happy_anim_2":               "happy",
    "happy_anim_3":               "happy",
    "happy_anim_4":               "happy",
    "excited_anim_2":             "hoora",
    "excited_anim_3":             "hoora",
    "proud_2":                    "strong",
    "proud_3":                    "strong",
    "angry_anim_2":               "angry",
    "angry_anim_3":               "angry",
    "angry_anim_4":               "angry",
    "anxious":                    "emotions/afraid",
    "bored_anim_2":               "bored",
    "fear":                       "emotions/afraid",
    "fear_2":                     "emotions/afraid",
    "humiliated":                 "sad",
    "hurt":                       "sad",
    "hurt_2":                     "sad",
    "late":                       "bored",
    "sad_anim_2":                 "sad",
    "surprised_anim_2":           "surprise",
    "surprised_anim_3":           "surprise",
    "alienated":                  "bored",
    "annoyed":                    "angry",
    "ask_attention":              "point_front",
    "ask_attention_2":            "point_front",
    "ask_attention_3":            "point_front",
    "cautious":                   "emotions/calm",
    "determined":                 "strong",
    "hello_anim":                 "hi",
    "hesitation":                 "curious",
    "lonely":                     "sad",
    "puzzled":                    "curious",
    "suspicious":                 "curious",
    # --- NAO gestures → QT equivalents ---
    "angry_gesture":              "angry",
    "angry_gesture_2":            "angry",
    "angry_gesture_3":            "angry",
    "applause":                   "clapping",
    "but":                        "refuse",
    "caress":                     "touch-head",
    "caress_2":                   "touch-head",
    "catch_fly":                  None,
    "catch_fly_2":                None,
    "choice":                     "curious",
    "choice_2":                   "curious",
    "claw":                       "refuse",
    "claw_2":                     "refuse",
    "coaxing":                    "come",
    "coaxing_2":                  "come",
    "confused_gesture":           "curious",
    "confused_gesture_2":         "curious",
    "count_one":                  "point_front",
    "count_one_2":                "point_front",
    "count_two":                  "point_front",
    "count_two_2":                "point_front",
    "count_three":                "point_front",
    "count_three_2":              "point_front",
    "count_four":                 "point_front",
    "count_four_2":               "point_front",
    "count_five":                 "point_front",
    "count_five_2":               "point_front",
    "count_more":                 "hug",
    "count_more_2":               "hug",
    "desperate":                  "sad",
    "desperate_2":                "sad",
    "desperate_3":                "sad",
    "desperate_4":                "sad",
    "desperate_5":                "sad",
    "enthusiastic_g":             "hoora",
    "enthusiastic_g2":            "hoora",
    "enthusiastic_g3":            "hoora",
    "enthusiastic_g4":            "hoora",
    "enthusiastic_g5":            "hoora",
    "everything":                 "hug",
    "everything_2":               "hug",
    "everything_3":               "hug",
    "everything_4":               "hug",
    "everything_5":               "hug",
    "everything_6":               "hug",
    "excited_gesture":            "hoora",
    "explain":                    "point_front",
    "explain_2":                  "point_front",
    "explain_3":                  "point_front",
    "explain_4":                  "point_front",
    "explain_5":                  "point_front",
    "explain_6":                  "point_front",
    "explain_7":                  "point_front",
    "explain_8":                  "point_front",
    "explain_9":                  "point_front",
    "explain_10":                 "point_front",
    "explain_11":                 "point_front",
    "far":                        "hug",
    "far_2":                      "hug",
    "far_3":                      "hug",
    "follow":                     "come",
    "freeze":                     "neutral",
    "give":                       "give_hand",
    "give_2":                     "give_hand",
    "give_3":                     "give_hand",
    "give_4":                     "give_hand",
    "give_5":                     "give_hand",
    "give_6":                     "give_hand",
    "great":                      "hoora",
    "he_says":                    "point_front",
    "he_says_2":                  "point_front",
    "he_says_3":                  "point_front",
    "hey_2":                      "hi",
    "hey_3":                      "hi",
    "hey_4":                      "hi",
    "hey_5":                      "hi",
    "hey_6":                      "hi",
    "hey_7":                      "hi",
    "hide":                       "peekaboo",
    "hungry_gesture":             "drink",
    "i_dont_know":                "curious",
    "i_dont_know_2":              "curious",
    "i_dont_know_3":              "curious",
    "i_dont_know_4":              "curious",
    "i_dont_know_5":              "curious",
    "i_dont_know_6":              "curious",
    "joint_hands":                "hug",
    "joint_hands_2":              "hug",
    "joint_hands_3":              "hug",
    "look":                       "curious",
    "look_2":                     "curious",
    "maybe":                      "curious",
    "me":                         "point_front",
    "me_2":                       "point_front",
    "me_3":                       "point_front",
    "me_4":                       "point_front",
    "me_5":                       "point_front",
    "me_6":                       "point_front",
    "me_7":                       "point_front",
    "me_8":                       "point_front",
    "mime":                       "neutral",
    "mime_2":                     "neutral",
    "next":                       "point_front",
    "no_gesture":                 "no",
    "no_gesture_2":               "no",
    "no_gesture_3":               "no",
    "no_gesture_4":               "no",
    "no_gesture_5":               "no",
    "no_gesture_6":               "no",
    "no_gesture_7":               "no",
    "no_gesture_8":               "no",
    "no_gesture_9":               "no",
    "nothing":                    "neutral",
    "nothing_2":                  "neutral",
    "on_the_evening":             "yes",
    "on_the_evening_2":           "yes",
    "on_the_evening_3":           "yes",
    "on_the_evening_4":           "yes",
    "on_the_evening_5":           "yes",
    "please":                     "hug",
    "please_2":                   "hug",
    "please_3":                   "hug",
    "reject":                     "refuse",
    "reject_2":                   "refuse",
    "reject_3":                   "refuse",
    "reject_4":                   "refuse",
    "reject_5":                   "refuse",
    "reject_6":                   "refuse",
    "salute_anim_2":              "hi",
    "salute_anim_3":              "hi",
    "shoot":                      "point_front",
    "show_floor":                 "point_front",
    "show_floor_2":               "point_front",
    "show_floor_3":               "point_front",
    "show_floor_4":               "point_front",
    "show_floor_5":               "point_front",
    "show_sky":                   "one-arm-up",
    "show_sky_2":                 "one-arm-up",
    "show_sky_3":                 "one-arm-up",
    "show_sky_4":                 "one-arm-up",
    "show_sky_5":                 "one-arm-up",
    "show_sky_6":                 "one-arm-up",
    "show_sky_7":                 "one-arm-up",
    "show_sky_8":                 "one-arm-up",
    "show_sky_9":                 "one-arm-up",
    "show_sky_10":                "one-arm-up",
    "show_sky_11":                "one-arm-up",
    "show_sky_12":                "one-arm-up",
    "shy_gesture":                "emotions/shy",
    "stretch_gesture":            "stretch",
    "stretch_gesture_2":          "stretch",
    "surprised_gesture":          "surprise",
    "take":                       "give_hand",
    "this":                       "point_front",
    "this_2":                     "point_front",
    "this_3":                     "point_front",
    "this_4":                     "point_front",
    "this_5":                     "point_front",
    "this_6":                     "point_front",
    "this_7":                     "point_front",
    "this_8":                     "point_front",
    "this_9":                     "point_front",
    "this_10":                    "point_front",
    "this_11":                    "point_front",
    "this_12":                    "point_front",
    "this_13":                    "point_front",
    "this_14":                    "point_front",
    "this_15":                    "point_front",
    "whats_this":                 "curious",
    "whats_this_2":               "curious",
    "whats_this_3":               "curious",
    "whats_this_4":               "curious",
    "whats_this_5":               "curious",
    "whats_this_6":               "curious",
    "whats_this_7":               "curious",
    "whats_this_8":               "curious",
    "whats_this_9":               "curious",
    "whats_this_10":              "curious",
    "whats_this_11":              "curious",
    "whats_this_12":              "curious",
    "whats_this_13":              "curious",
    "whats_this_14":              "curious",
    "whats_this_15":              "curious",
    "whats_this_16":              "curious",
    "yes_anim_2":                 "yes",
    "yes_anim_3":                 "yes",
    "you":                        "point_front",
    "you_2":                      "point_front",
    "you_3":                      "point_front",
    "you_4":                      "point_front",
    "you_5":                      "point_front",
    "you_know_what":              "curious",
    "you_know_what_2":            "curious",
    "you_know_what_3":            "curious",
    "you_know_what_4":            "curious",
    "you_know_what_5":            "curious",
    "you_know_what_6":            "curious",
    "yum":                        "drink",
    # --- NAO body-talk / listening → QT equivalents ---
    "bodytalk_1":                 "neutral",
    "bodytalk_2":                 "neutral",
    "bodytalk_3":                 "neutral",
    "bodytalk_4":                 "neutral",
    "bodytalk_5":                 "neutral",
    "bodytalk_6":                 "neutral",
    "bodytalk_7":                 "neutral",
    "bodytalk_8":                 "neutral",
    "bodytalk_9":                 "neutral",
    "bodytalk_10":                "neutral",
    "bodytalk_11":                "neutral",
    "bodytalk_12":                "neutral",
    "bodytalk_13":                "neutral",
    "bodytalk_14":                "neutral",
    "bodytalk_15":                "neutral",
    "bodytalk_16":                "neutral",
    "bodytalk_17":                "neutral",
    "bodytalk_18":                "neutral",
    "bodytalk_19":                "neutral",
    "bodytalk_20":                "neutral",
    "bodytalk_21":                "neutral",
    "bodytalk_22":                "neutral",
    "listening_anim":             "yes",
    "listening_left":             "yes",
    "listening_right":            "yes",
    "remember":                   "curious",
    "remember_2":                 "curious",
    "remember_3":                 "curious",
    "thinking_loop":              "curious",
    "thinking_loop_2":            "curious",
    # --- NAO postures → no equivalent on QTrobot ---
    "stand":                      None,
    "standinit":                  None,
    "standzero":                  None,
    "sit":                        None,
    "sitrelax":                   None,
    "crouch":                     None,
    "lyingback":                  None,
    "lyingbelly":                 None,
    # --- NAO walking → no equivalent on QTrobot ---
    "walk_forward":               None,
    "walk_backward":              None,
    "walk_left":                  None,
    "walk_right":                 None,
    "turn_left":                  None,
    "turn_right":                 None,
    "stop":                       None,
    # --- Scratch gestures involving legs → skip ---
    "scratch_bottom":             None,
    "scratch_leg":                None,
    "walk_in_the_shit":           None,
}

# ── Custom joint-keyframe gestures ────────────────────────────────────────────
#
# For gestures that cannot be triggered via /qt_robot/gesture/play (behaviour
# scripts, missing files, etc.) we define them here as a sequence of joint
# position snapshots.  Each step is (joint_dict, hold_seconds).
#
# Available joints and approximate ranges (radians):
#   HeadPitch          -40° … +40°   (neg = look up, pos = look down)
#   HeadYaw            -85° … +85°   (neg = right, pos = left)
#   LeftShoulderPitch  -115° … +30°  (neg = arm up/forward, pos = arm down)
#   LeftShoulderRoll     0° … +85°   (pos = away from body)
#   LeftElbowRoll      -85° … 0°     (neg = elbow bent)
#   RightShoulderPitch -115° … +30°
#   RightShoulderRoll  -85° … 0°     (neg = away from body)
#   RightElbowRoll       0° … +85°   (pos = elbow bent)
#
# Only the joints listed in each step are updated; others hold their position.
# Checked BEFORE QT_MOTION_MAP so these override the service-call path.

_QT_HOME = {
    "LeftShoulderPitch": 0.0, "LeftShoulderRoll": 0.0, "LeftElbowRoll": 0.0,
    "RightShoulderPitch": 0.0, "RightShoulderRoll": 0.0, "RightElbowRoll": 0.0,
    "HeadPitch": 0.0, "HeadYaw": 0.0,
}

QT_CUSTOM_GESTURES: dict[str, list[tuple[dict, float]]] = {
    # Arms wide, flap twice, return home
    "fly": [
        ({"LeftShoulderPitch": -70, "LeftShoulderRoll":  55, "LeftElbowRoll": -15,
          "RightShoulderPitch": -70, "RightShoulderRoll": -55, "RightElbowRoll": 15}, 0.6),
        ({"LeftShoulderPitch": -30, "LeftShoulderRoll":  40,
          "RightShoulderPitch": -30, "RightShoulderRoll": -40}, 0.3),
        ({"LeftShoulderPitch": -70, "LeftShoulderRoll":  55,
          "RightShoulderPitch": -70, "RightShoulderRoll": -55}, 0.3),
        ({"LeftShoulderPitch": -30, "LeftShoulderRoll":  40,
          "RightShoulderPitch": -30, "RightShoulderRoll": -40}, 0.3),
        (dict(_QT_HOME), 0.5),
    ],
    # Right hand to ear, head tilted, small nod × 2
    "phone_call": [
        ({"RightShoulderPitch": -60, "RightShoulderRoll": -10, "RightElbowRoll": 75,
          "HeadYaw": 25}, 0.5),
        ({"HeadPitch": 10}, 0.25),
        ({"HeadPitch":  0}, 0.25),
        ({"HeadPitch": 10}, 0.25),
        ({"HeadPitch":  0}, 0.25),
        (dict(_QT_HOME), 0.5),
    ],
    # Steering-wheel pose, turn left-right twice
    "drive": [
        ({"LeftShoulderPitch": -45, "LeftShoulderRoll":  25, "LeftElbowRoll": -30,
          "RightShoulderPitch": -45, "RightShoulderRoll": -25, "RightElbowRoll": 30}, 0.4),
        ({"LeftShoulderPitch": -35, "LeftShoulderRoll":  35, "LeftElbowRoll": -20,
          "RightShoulderPitch": -55, "RightShoulderRoll": -10, "RightElbowRoll": 40}, 0.4),
        ({"LeftShoulderPitch": -55, "LeftShoulderRoll":  10, "LeftElbowRoll": -40,
          "RightShoulderPitch": -35, "RightShoulderRoll": -35, "RightElbowRoll": 20}, 0.4),
        ({"LeftShoulderPitch": -45, "LeftShoulderRoll":  25, "LeftElbowRoll": -30,
          "RightShoulderPitch": -45, "RightShoulderRoll": -25, "RightElbowRoll": 30}, 0.4),
        (dict(_QT_HOME), 0.5),
    ],
    # Two quick head dips (no sound on QT, but conveys the idea)
    "beep": [
        ({"HeadPitch": 15}, 0.15),
        ({"HeadPitch":  0}, 0.15),
        ({"HeadPitch": 15}, 0.15),
        ({"HeadPitch":  0}, 0.15),
    ],
    # Hands framing face — arms raised, elbows bent inward, tilt head
    "show_face": [
        ({"LeftShoulderPitch": -80, "LeftShoulderRoll":  25, "LeftElbowRoll": -55,
          "RightShoulderPitch": -80, "RightShoulderRoll": -25, "RightElbowRoll": 55,
          "HeadPitch": -10}, 0.7),
        ({"HeadPitch": 0}, 0.3),
        (dict(_QT_HOME), 0.5),
    ],
    # Both arms shoot up in a V, pump twice, return — celebration cheer
    "hoora": [
        ({"LeftShoulderPitch": -85, "LeftShoulderRoll":  30, "LeftElbowRoll": -10,
          "RightShoulderPitch": -85, "RightShoulderRoll": -30, "RightElbowRoll": 10,
          "HeadPitch": -10}, 0.5),
        ({"LeftShoulderPitch": -65, "RightShoulderPitch": -65}, 0.2),
        ({"LeftShoulderPitch": -125, "RightShoulderPitch": -125}, 0.2),
        ({"LeftShoulderPitch": -65, "RightShoulderPitch": -65}, 0.2),
        ({"LeftShoulderPitch": -125, "RightShoulderPitch": -125}, 0.2),
        (dict(_QT_HOME), 0.5),
    ],
    # Hands out, look left then right — playful curiosity
    "pretend_play": [
        ({"LeftShoulderPitch": -30, "LeftShoulderRoll":  45, "LeftElbowRoll": -30,
          "RightShoulderPitch": -30, "RightShoulderRoll": -45, "RightElbowRoll": 30,
          "HeadPitch": -10}, 0.5),
        ({"HeadYaw":  30}, 0.35),
        ({"HeadYaw": -30}, 0.35),
        ({"HeadYaw": 0, "HeadPitch": 0}, 0.2),
        (dict(_QT_HOME), 0.5),
    ],
}
# Aliases
QT_CUSTOM_GESTURES["driving"]     = QT_CUSTOM_GESTURES["drive"]
QT_CUSTOM_GESTURES["drive_car"]   = QT_CUSTOM_GESTURES["drive"]
QT_CUSTOM_GESTURES["beeping"]     = QT_CUSTOM_GESTURES["beep"]
QT_CUSTOM_GESTURES["show_qt"]     = QT_CUSTOM_GESTURES["show_face"]
QT_CUSTOM_GESTURES["call_someone"]= QT_CUSTOM_GESTURES["phone_call"]
QT_CUSTOM_GESTURES["helicopter"]  = QT_CUSTOM_GESTURES["fly"]
QT_CUSTOM_GESTURES["air_juggle"]  = QT_CUSTOM_GESTURES["fly"]
QT_CUSTOM_GESTURES["catch_fly"]   = QT_CUSTOM_GESTURES["fly"]
QT_CUSTOM_GESTURES["catch_fly_2"] = QT_CUSTOM_GESTURES["fly"]

# Universal emotion names → QTrobot emotion file name (under /QT/ on the robot)
QT_EMOTION_MAP = {
    "happy":    "happy",
    "sad":      "sad",
    "angry":    "angry",
    "surprised":"surprise",
    "surprise": "surprise",
    "neutral":  "neutral",
    "scared":   "scared",
    "excited":  "excited",
    "disgusted":"disgusted",
    "calm":     "calm",
    "afraid":   "afraid",
    "shy":      "shy",
}


class QTBridge(RobotBridge):
    """QTrobot bridge adapter: roslibpy WebSocket → QTrobot ROS1 topics/services."""

    SUPPORTED_TYPES = ("qtrobot",)

    def __init__(self):
        super().__init__("qt_bridge")
        self.declare_parameter("qt_host", "192.168.1.101")
        self.declare_parameter("qt_port", 9090)
        # Connection state
        self._host = self.get_parameter("qt_host").get_parameter_value().string_value
        self._port = self.get_parameter("qt_port").get_parameter_value().integer_value
        self._version = "qt1"
        self._client = None
        self._pubs: dict = {}               # cached roslibpy.Topic publishers
        self._joint_positions: dict = {}    # joint_name → last commanded angle (degrees)
        self._joint_names_logged = False    # log joint names only once at startup

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_activate(self, msg: RobotConfig):
        """Read connection parameters and clear publisher cache on (re)activation."""
        self._host = self.get_parameter("qt_host").get_parameter_value().string_value
        self._port = self.get_parameter("qt_port").get_parameter_value().integer_value
        self._version = msg.robot_version or "qt1"
        self._pubs.clear()

    def _on_deactivate(self):
        """Clear publisher cache on deactivation."""
        self._pubs.clear()
        self._joint_names_logged = False

    def connect(self):
        """Open the roslibpy WebSocket connection to QTrobot's rosbridge server."""
        if not _HAS_ROSLIBPY:
            self.get_logger().warning("[QtBridge] roslibpy not installed — dry-run mode.")
            return
        try:
            self.get_logger().info(
                f"[QtBridge] Connecting to rosbridge @ {self._host}:{self._port} ..."
            )
            self._client = roslibpy.Ros(host=self._host, port=self._port)
            self._client.on_ready(self._on_connected)
            self._client.run()  # blocking — must be called in a background thread
        except Exception as exc:
            self.get_logger().error(f"[QtBridge] Could not connect: {exc}")
            self._client = None

    def disconnect(self):
        """Terminate the roslibpy WebSocket cleanly."""
        if self._client:
            try:
                self._client.terminate()
            except Exception:
                pass
            self._client = None

    def _on_connected(self):
        """Called by roslibpy when the WebSocket is ready; log topics, subscribe to joints."""
        self.get_logger().info(
            f"[QtBridge] rosbridge CONNECTED @ {self._host}:{self._port}"
        )

        def _log_topics(result):
            try:
                topic_list = result["topics"]
                type_list  = result.get("types", [])
            except (KeyError, TypeError):
                topic_list = list(result)
                type_list  = []
            cmd_topics = list(QT_JOINT_TOPICS.values())
            self.get_logger().info(
                "[QtBridge] Available topics:\n" + "\n".join(f"  {t}" for t in sorted(topic_list))
            )
            for t, tp in zip(topic_list, type_list):
                if t in cmd_topics:
                    self.get_logger().info(f"[QtBridge] command topic type → {t} : {tp}")

        def _log_services(result):
            try:
                svc_list = result["services"]
            except (KeyError, TypeError):
                svc_list = list(result)
            qt_svcs = [s for s in sorted(svc_list) if "qt" in s.lower()]
            self.get_logger().info(
                "[QtBridge] QT services:\n" + "\n".join(f"  {s}" for s in qt_svcs)
            )

        self._client.get_topics(_log_topics)
        self._client.get_services(_log_services)

        # Subscribe to joint states only to learn the joint names at startup.
        # We do NOT use the feedback positions as fallback values because the robot
        # publishes them in radians while our commands are in degrees — mixing units
        # causes unspecified joints to snap to ~0° on every partial command.
        # Instead, _pub_joint_trajectory() records what it commanded so fallbacks
        # always stay in degrees.
        def _on_joint_state(msg):
            if not self._joint_names_logged:
                self._joint_names_logged = True
                self.get_logger().info(
                    f"[QtBridge] Joint names on robot: {msg.get('name', [])}"
                )
        try:
            sub = roslibpy.Topic(
                self._client, "/qt_robot/joints/state", "sensor_msgs/JointState"
            )
            sub.subscribe(_on_joint_state)
        except Exception as exc:
            self.get_logger().warning(f"[QtBridge] joint state subscribe failed: {exc}")

        # Log available gestures at startup
        def _log_gestures(result):
            self.get_logger().info(f"[QtBridge] Gesture list response: {result}")
        try:
            svc = roslibpy.Service(
                self._client, "/qt_robot/gesture/list", "std_srvs/Trigger"
            )
            svc.call(roslibpy.ServiceRequest(), _log_gestures, _log_gestures)
        except Exception as exc:
            self.get_logger().warning(f"[QtBridge] gesture/list call failed: {exc}")

        # Send robot to home position
        try:
            home_svc = roslibpy.Service(
                self._client, "/qt_robot/motors/home", "std_srvs/Trigger"
            )
            home_svc.call(
                roslibpy.ServiceRequest(),
                lambda r: self.get_logger().info(f"[QtBridge] motors/home: {r}"),
                lambda e: self.get_logger().warning(f"[QtBridge] motors/home error: {e}"),
            )
        except Exception as exc:
            self.get_logger().warning(f"[QtBridge] motors/home call failed: {exc}")

        # Pre-advertise joint command topics so the first publish is instant
        for group_key, topic_name in QT_JOINT_TOPICS.items():
            key = f"traj_{group_key}"
            if key not in self._pubs:
                t = roslibpy.Topic(
                    self._client, topic_name, "std_msgs/Float64MultiArray"
                )
                t.advertise()
                self._pubs[key] = t
                self.get_logger().info(f"[QtBridge] pre-advertised {topic_name}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pub_ros1(self, key, payload):
        """Publish a String message to the versioned QTrobot topic for `key`."""
        if self._client is None or not self._client.is_connected:
            self.get_logger().warning(f"[QtBridge][NOT CONNECTED] dropped {key} → {payload}")
            return
        if key not in self._pubs:
            self._pubs[key] = roslibpy.Topic(
                self._client, QT_TOPICS[self._version][key], "std_msgs/String"
            )
        self._pubs[key].publish(roslibpy.Message(payload))

    def _pub_joint_trajectory(self, group_key, joints, angles):
        """Send a Float64MultiArray to the given joint group topic in fixed positional order."""
        if self._client is None or not self._client.is_connected:
            return
        topic_name = QT_JOINT_TOPICS[group_key]
        order = QT_JOINT_ORDER[group_key]
        requested = dict(zip(joints, angles))
        # Unspecified joints fall back to the last value WE commanded (degrees), not the
        # robot's JointState feedback (which is in radians). Without this, a partial command
        # like "LeftShoulderRoll:120" would send the other two joints to ~0° (radian values
        # misread as degrees), causing the arm to wiggle unpredictably on every call.
        data = [requested.get(j, self._joint_positions.get(j, 0.0)) for j in order]
        # Immediately record what we commanded so future fallbacks use degree values.
        for j, v in zip(order, data):
            self._joint_positions[j] = v
        key = f"traj_{group_key}"
        if key not in self._pubs:
            t = roslibpy.Topic(self._client, topic_name, "std_msgs/Float64MultiArray")
            t.advertise()
            self._pubs[key] = t
        self._pubs[key].publish(roslibpy.Message({
            "layout": {"dim": [], "data_offset": 0},
            "data": data,
        }))

    # NAO joint names → QTrobot joint names
    _NAO_TO_QT_JOINT = {
        "LShoulderPitch": "LeftShoulderPitch",
        "LShoulderRoll":  "LeftShoulderRoll",
        "LElbowRoll":     "LeftElbowRoll",
        "LElbowYaw":      "LeftElbowYaw",
        "RShoulderPitch": "RightShoulderPitch",
        "RShoulderRoll":  "RightShoulderRoll",
        "RElbowRoll":     "RightElbowRoll",
        "RElbowYaw":      "RightElbowYaw",
    }

    

    # ------------------------------------------------------------------
    # speak
    # ------------------------------------------------------------------

    def do_speak(self, msg: RobotCmd):
        """Publish speech text to /qt_robot/speech/say via rosbridge."""
        if not msg.text:
            return
        lang = msg.language or "fr-FR"
        self.get_logger().info(f"[QtBridge] speak [{lang}]: {msg.text}")
        self._pub_ros1("speech", {"data": msg.text})

    # ------------------------------------------------------------------
    # move
    # ------------------------------------------------------------------

    def _do_joint_control(self, spec, speed):
        """Parse 'Joint:angle,…' spec and dispatch to the correct joint group topic."""
        head_joints, head_angles   = [], []
        left_joints, left_angles   = [], []
        right_joints, right_angles = [], []
        for token in spec.split(","):
            token = token.strip()
            if ":" not in token:
                continue
            joint, angle_str = token.split(":", 1)
            joint = self._NAO_TO_QT_JOINT.get(joint.strip(), joint.strip())
            try:
                angle = float(angle_str.strip())
            except ValueError:
                self.get_logger().warning(f"[QtBridge] joint parse error: '{token}'")
                continue
            if joint.startswith("Head"):
                head_joints.append(joint);  head_angles.append(angle)
            elif joint.startswith("Left"):
                left_joints.append(joint);  left_angles.append(angle)
            elif joint.startswith("Right"):
                right_joints.append(joint); right_angles.append(angle)
            else:
                self.get_logger().warning(f"[QtBridge] unknown joint group for '{joint}'")
        for topic_key, joints, angles in [
            ("head",  head_joints,  head_angles),
            ("left",  left_joints,  left_angles),
            ("right", right_joints, right_angles),
        ]:
            if joints:
                self.get_logger().info(
                    f"[QtBridge] joint → {topic_key}: {dict(zip(joints, angles))}"
                )
                self._pub_joint_trajectory(topic_key, joints, angles)

    def _do_custom_gesture(self, steps: list):
        """Execute a QT_CUSTOM_GESTURES sequence: send joint positions step by step."""
        for joints, hold in steps:
            head_j, head_a = [], []
            left_j, left_a = [], []
            right_j, right_a = [], []
            for joint, angle in joints.items():
                if joint.startswith("Head"):
                    head_j.append(joint);  head_a.append(angle)
                elif joint.startswith("Left"):
                    left_j.append(joint);  left_a.append(angle)
                elif joint.startswith("Right"):
                    right_j.append(joint); right_a.append(angle)
            for key, jl, al in [("head", head_j, head_a),
                                                                    ("left", left_j, left_a),
                                                                    ("right", right_j, right_a)]:
                if jl:
                    self._pub_joint_trajectory(key, jl, al)
            time.sleep(hold)

    def do_move(self, msg: RobotCmd):
        """Resolve the gesture name and call /qt_robot/gesture/play via rosbridge."""
        raw = (msg.motion_name or "").strip()
        if not raw:
            return

        # Direct joint control: "Joint:angle,Joint:angle,..."
        if ":" in raw:
            self._do_joint_control(raw, msg.speed)
            return

        # Custom joint-keyframe gestures (checked before QT_MOTION_MAP)
        if raw.lower() in QT_CUSTOM_GESTURES:
            steps = QT_CUSTOM_GESTURES[raw.lower()]
            self.get_logger().info(f"[QtBridge] move (custom gesture): {raw}")
            threading.Thread(target=self._do_custom_gesture, args=(steps,), daemon=True).start()
            return

        # Translate universal/NAO names to QTrobot names via QT_MOTION_MAP
        if raw.lower() in QT_MOTION_MAP:
            qt_name = QT_MOTION_MAP[raw.lower()]
            if qt_name is None:
                self.get_logger().info(
                    f"[QtBridge] move: '{raw}' has no QTrobot equivalent — skipped."
                )
                return
            # The mapped name may itself be a custom gesture (e.g. "hoora" → joint sequence)
            if qt_name in QT_CUSTOM_GESTURES:
                steps = QT_CUSTOM_GESTURES[qt_name]
                self.get_logger().info(f"[QtBridge] move (custom gesture via map): {qt_name}")
                threading.Thread(target=self._do_custom_gesture, args=(steps,), daemon=True).start()
                return
            # "@" prefix = absolute path (custom package); strip "@", no "QT/" prepend
            name = qt_name[1:] if qt_name.startswith("@") else f"QT/{qt_name}"
        elif "/" not in raw:
            # Unknown name without a slash → assume top-level QTrobot gesture
            name = f"QT/{raw}"
        else:
            name = raw

        self.get_logger().info(f"[QtBridge] move (gesture service): {name}")

        def _on_result(result):
            self.get_logger().info(f"[QtBridge] gesture result: {result}")

        def _on_error(err):
            self.get_logger().warning(f"[QtBridge] gesture error: {err}")

        try:
            svc = roslibpy.Service(
                self._client, "/qt_robot/gesture/play", "qt_gesture_controller/gesture_play"
            )
            svc.call(roslibpy.ServiceRequest({"name": name}), _on_result, _on_error)
        except Exception as exc:
            self.get_logger().error(f"[QtBridge] gesture service call failed: {exc}")

    # ------------------------------------------------------------------
    # display
    # ------------------------------------------------------------------

    def do_display(self, msg: RobotCmd):
        """Show emotion, image, or log-and-skip LED requests."""
        if msg.led_name:
            self.get_logger().info(
                f"[QtBridge] display led '{msg.led_name}' color='{msg.color}' "
                "— not supported on QTrobot, skipped."
            )
            return

        if msg.image_path:
            self.get_logger().info(f"[QtBridge] display image: {msg.image_path}")
            try:
                svc = roslibpy.Service(
                    self._client, "/qt_robot/emotion/show", "qt_robot_interface/emotion_show"
                )
                svc.call(
                    roslibpy.ServiceRequest({"name": msg.image_path}),
                    lambda r: self.get_logger().info(f"[QtBridge] image display result: {r}"),
                    lambda e: self.get_logger().warning(f"[QtBridge] image display error: {e}"),
                )
            except Exception as exc:
                self.get_logger().error(f"[QtBridge] image display service call failed: {exc}")
            return

        if msg.emotion:
            raw_emotion = msg.emotion.strip()
            if '/' in raw_emotion:
                # Raw QT emotion path (e.g. 'QT/showing_smile' from WOZ interface) — use as-is
                emotion_path = raw_emotion
            else:
                emotion_key = raw_emotion.lower()
                if emotion_key not in QT_EMOTION_MAP:
                    self.get_logger().warning(
                        f"[QtBridge] unknown emotion '{emotion_key}'. "
                        f"Valid: {', '.join(QT_EMOTION_MAP.keys())}"
                    )
                    return
                emotion_path = f"QT/{QT_EMOTION_MAP[emotion_key]}"
            duration_ms = msg.duration_ms
            self.get_logger().info(
                f"[QtBridge] display emotion: {emotion_path}"
                + (f" for {duration_ms}ms" if duration_ms > 0 else "")
            )

            def _on_result(result):
                if result.get("status"):
                    self.get_logger().info(f"[QtBridge] emotion '{emotion_path}' done.")
                else:
                    self.get_logger().warning(
                        f"[QtBridge] emotion '{emotion_path}' returned status=False. "
                        "Check that the emotion file exists on the robot."
                    )

            def _on_error(err):
                self.get_logger().warning(f"[QtBridge] emotion error: {err}")

            try:
                svc = roslibpy.Service(
                    self._client, "/qt_robot/emotion/show", "qt_robot_interface/emotion_show"
                )
                svc.call(roslibpy.ServiceRequest({"name": emotion_path}), _on_result, _on_error)
                if duration_ms > 0:
                    def _auto_stop():
                        time.sleep(duration_ms / 1000.0)
                        try:
                            stop_svc = roslibpy.Service(
                                self._client, "/qt_robot/emotion/stop", "std_srvs/Trigger"
                            )
                            stop_svc.call(
                                roslibpy.ServiceRequest(),
                                lambda r: self.get_logger().info(
                                    f"[QtBridge] emotion stopped after {duration_ms}ms"
                                ),
                                lambda e: self.get_logger().warning(
                                    f"[QtBridge] emotion stop error: {e}"
                                ),
                            )
                        except Exception as ex:
                            self.get_logger().warning(f"[QtBridge] emotion stop failed: {ex}")
                    threading.Thread(target=_auto_stop, daemon=True).start()
            except Exception as exc:
                self.get_logger().error(f"[QtBridge] emotion service call failed: {exc}")


def main(args=None):
    rclpy.init(args=args)
    node = QTBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
