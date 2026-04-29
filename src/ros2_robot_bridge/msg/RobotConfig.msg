# RobotConfig.msg
# Published by the detector node; consumed by bridges and dispatcher.

string robot_type      # "nao" | "qtrobot"
string robot_version   # "v5" | "v6"  for NAO   /   "qt1" | "qt2" for QTrobot
bool   is_ready        # true once the bridge has confirmed the robot is reachable
string status_msg      # human-readable status / error description
