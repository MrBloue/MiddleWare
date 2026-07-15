#!/bin/bash
# setup.sh — bootstrap ROS2 Humble + workspace on a fresh Ubuntu 22.04 machine (e.g. Jetson Orin)
set -e

WS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Locale"
sudo apt-get install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

echo "==> ROS2 Humble apt repo"
sudo apt-get install -y software-properties-common curl
sudo add-apt-repository universe -y
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | sudo gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

echo "==> System packages"
sudo apt-get update
sudo apt-get install -y \
    ros-humble-ros-base \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    libboost-all-dev \
    libssl-dev

echo "==> rosdep"
sudo rosdep init 2>/dev/null || true
rosdep update
rosdep install --from-paths "$WS_DIR/src" --ignore-src -y --rosdistro humble || true

echo "==> Python packages"
pip3 install -r "$WS_DIR/src/ros2_robot_bridge/requirements.txt"

echo "==> Build workspace"
source /opt/ros/humble/setup.bash
cd "$WS_DIR"
colcon build --symlink-install

echo ""
echo "Done. To use the workspace:"
echo "  source /opt/ros/humble/setup.bash"
echo "  source $WS_DIR/install/setup.bash"
