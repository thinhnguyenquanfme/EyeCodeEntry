import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/thinhnguyen/EyeCodeEntry/install/robot_gazebo'
