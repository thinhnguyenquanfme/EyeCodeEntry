import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/thinhnguyen/EyeCodeEntry/ros2_ws/install/robot_gazebo'
