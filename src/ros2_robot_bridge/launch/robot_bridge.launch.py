"""
robot_bridge.launch.py
======================
Launches all four nodes of the ros2_robot_bridge package.

Usage examples
--------------
  # NAO v6 (default)
  ros2 launch ros2_robot_bridge robot_bridge.launch.py \\
      robot_type:=nao robot_version:=v6 naoqi_host:=192.168.1.100

  # NAO v5
  ros2 launch ros2_robot_bridge robot_bridge.launch.py \\
      robot_type:=nao robot_version:=v5 naoqi_host:=192.168.1.50

  # QTrobot QT1
  ros2 launch ros2_robot_bridge robot_bridge.launch.py \\
      robot_type:=qtrobot robot_version:=qt1 qt_host:=192.168.1.101

  # QTrobot QT2
  ros2 launch ros2_robot_bridge robot_bridge.launch.py \\
      robot_type:=qtrobot robot_version:=qt2 qt_host:=192.168.1.102

  # With command queuing enabled
  ros2 launch ros2_robot_bridge robot_bridge.launch.py \\
      robot_type:=nao robot_version:=v6 queue_commands:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _make_nodes(context, *args, **kwargs):
    robot_type    = LaunchConfiguration("robot_type").perform(context)
    naoqi_host    = LaunchConfiguration("naoqi_host").perform(context)
    qt_host       = LaunchConfiguration("qt_host").perform(context)

    # Derive namespace from the last octet of the relevant host IP
    host = qt_host if robot_type == "qtrobot" else naoqi_host
    last_octet = host.split(".")[-1]
    ns = f"{robot_type}_{last_octet}"

    is_qt = (robot_type == "qtrobot")

    common_nodes = [
        Node(
            package="ros2_robot_bridge",
            executable="robot_detector.py",
            name="robot_detector",
            namespace=ns,
            output="screen",
            parameters=[{
                "robot_type":    LaunchConfiguration("robot_type"),
                "robot_version": LaunchConfiguration("robot_version"),
            }],
        ),
        Node(
            package="ros2_robot_bridge",
            executable="nao_bridge.py",
            name="nao_bridge",
            namespace=ns,
            output="screen",
            parameters=[{
                "naoqi_host":     LaunchConfiguration("naoqi_host"),
                "naoqi_port":     LaunchConfiguration("naoqi_port"),
                "naoqi_scheme":   LaunchConfiguration("naoqi_scheme"),
                "naoqi_ssl_cert": LaunchConfiguration("naoqi_ssl_cert"),
            }],
        ),
        Node(
            package="ros2_robot_bridge",
            executable="qt_bridge.py",
            name="qt_bridge",
            namespace=ns,
            output="screen",
            parameters=[{
                "qt_host": LaunchConfiguration("qt_host"),
                "qt_port": LaunchConfiguration("qt_port"),
            }],
        ),
        Node(
            package="ros2_robot_bridge",
            executable="command_dispatcher.py",
            name="command_dispatcher",
            namespace=ns,
            output="screen",
            parameters=[{
                "queue_commands": LaunchConfiguration("queue_commands"),
                "cmd_timeout_s":  LaunchConfiguration("cmd_timeout_s"),
            }],
        ),
    ]

    # Sensor node: qt_sensor for QTrobot, nao_sensors for NAO/Pepper.
    if is_qt:
        sensor_node = Node(
            package="ros2_robot_bridge",
            executable="qt_sensor.py",
            name="qt_sensor",
            namespace=ns,
            output="screen",
            parameters=[{
                "qt_host":   LaunchConfiguration("qt_host"),
                "qt_port":   LaunchConfiguration("qt_port"),
                "sensor_hz": LaunchConfiguration("sensor_poll_hz"),
            }],
        )
    else:
        sensor_node = Node(
            package="ros2_robot_bridge",
            executable="nao_sensors.py",
            name="nao_sensors",
            namespace=ns,
            output="screen",
            parameters=[{
                "robot_type":        LaunchConfiguration("robot_type"),
                "naoqi_host":        LaunchConfiguration("naoqi_host"),
                "naoqi_port":        LaunchConfiguration("naoqi_port"),
                "poll_hz":           LaunchConfiguration("sensor_poll_hz"),
                "sound_sensitivity": LaunchConfiguration("sound_sensitivity"),
            }],
        )

    return common_nodes + [sensor_node]


def generate_launch_description() -> LaunchDescription:
    args = [
        DeclareLaunchArgument("robot_type",     default_value="nao",
                              description="Robot family: nao | qtrobot"),
        DeclareLaunchArgument("robot_version",  default_value="",
                              description="Version: v5|v6 (NAO)  qt1|qt2 (QTrobot)  v1|v1.8|v2 (Pepper) — optional for NAO/Pepper"),
        DeclareLaunchArgument("naoqi_host",     default_value="192.168.1.100",
                              description="IP address of the NAO robot"),
        DeclareLaunchArgument("naoqi_port",     default_value="9559",
                              description="NAOqi port on the robot (default 9559)"),
        DeclareLaunchArgument("naoqi_scheme",   default_value="tcp",
                              description="Connection scheme: tcp (NAO) or tcps (Pepper TLS gateway)"),
        DeclareLaunchArgument("naoqi_ssl_cert", default_value="",
                              description="CA certificate path for tcps connections (Pepper gateway)"),
        DeclareLaunchArgument("qt_host",        default_value="192.168.100.1",
                              description="IP address of QTrobot rosbridge"),
        DeclareLaunchArgument("qt_port",        default_value="9090",
                              description="rosbridge port on QTrobot side"),
        DeclareLaunchArgument("queue_commands",   default_value="false",
                              description="Buffer commands for sequential execution"),
        DeclareLaunchArgument("cmd_timeout_s",    default_value="10.0",
                              description="Seconds before a queued command expires"),
        DeclareLaunchArgument("sensor_poll_hz",   default_value="20.0",
                              description="Sensor polling frequency in Hz (buttons, sonar, battery, audio)"),
        DeclareLaunchArgument("sound_sensitivity", default_value="0.5",
                              description="ALSoundDetection sensitivity 0.0 (deaf) to 1.0 (very sensitive)"),
    ]
    return LaunchDescription(args + [OpaqueFunction(function=_make_nodes)])
