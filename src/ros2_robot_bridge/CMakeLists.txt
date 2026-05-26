cmake_minimum_required(VERSION 3.8)
project(ros2_robot_bridge)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RobotCmd.msg"
  "msg/RobotConfig.msg"
  DEPENDENCIES std_msgs
)

install(PROGRAMS
  ros2_robot_bridge/robot_detector.py
  ros2_robot_bridge/nao_bridge.py
  ros2_robot_bridge/nao_sensors.py
  ros2_robot_bridge/qt_bridge.py
  ros2_robot_bridge/qt_sensor.py
  ros2_robot_bridge/command_dispatcher.py
  ros2_robot_bridge/woz_node.py
  ros2_robot_bridge/robot_bridge_template.py
  ros2_robot_bridge/robot_sensor_template.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
install(DIRECTORY config  DESTINATION share/${PROJECT_NAME})
install(DIRECTORY woz_templates DESTINATION share/${PROJECT_NAME})
install(DIRECTORY woz_static    DESTINATION share/${PROJECT_NAME})

# Shared modules imported by bridge/sensor/woz nodes — not standalone executables
install(FILES
  ros2_robot_bridge/__init__.py
  ros2_robot_bridge/base_bridge.py
  ros2_robot_bridge/base_sensor.py
  ros2_robot_bridge/woz_states.py
  DESTINATION ${PYTHON_INSTALL_DIR}/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
