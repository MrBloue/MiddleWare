# RobotCmd.msg
# Unified command message for speak, move, and display actions.

string action          # "speak" | "move" | "display"

# --- speak ---
string text            # text to say (TTS)
string language        # e.g. "en-US", "fr-FR" (optional, defaults to "en-US")

# --- move ---
string motion_name     # predefined motion key, e.g. "wave", "bow", "nod"
float32 speed          # 0.0–1.0  (optional, defaults to 1.0)

# --- display ---
string image_path      # absolute path or package-relative path to image file
string emotion         # emotion keyword, e.g. "happy", "sad", "neutral"
int32  duration_ms     # how long to hold display, 0 = indefinite

# --- led ---
string led_name        # group: "eyes","left_eye","right_eye","ears","chest","feet","head","all"
string color           # hex "#RRGGBB" or name: "red","green","blue","white","yellow","off"…
