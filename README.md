# rosorin-pro-gazebo-slam-navigation

## 1. Research Question

How can I use a simulated 2D LiDAR with ROS 2 to map an environment and
navigate a robot to goals in Gazebo?

## 2. Objective

Set up the ROSOrin Pro model in Gazebo, view its simulated sensors, build and
save a 2D map with SLAM Toolbox, then use Nav2 to localize on that map and
plan routes to one or more goals.

## 3. System Architecture

```text
Gazebo world and robot
       | /scan, /odom, TF, /clock
       v
ROS-Gazebo bridge
       |                         saved map
       v                              |
SLAM Toolbox --> /map                 v
                                Nav2 localization + planner
                                          | path
                                          v
                                  Nav2 controller
                                          | /cmd_vel
                                          v
                         bridge --> /controller/cmd_vel
                                          |
                                          v
                                    Gazebo robot
```

| Part | Responsibility | Input | Output |
| --- | --- | --- | --- |
| Gazebo LiDAR | Simulate 2D laser measurements | World and robot pose | `/scan` |
| ROS-Gazebo bridge | Pass sensor, odometry, clock, and velocity data between ROS and Gazebo | Gazebo topics and ROS topics | `/scan`, `/odom`, `/clock`, velocity command |
| SLAM Toolbox | Build a map while the robot moves | `/scan`, odometry, TF | `/map` and map-to-odom transform |
| Nav2 localization | Estimate the robot's pose on the saved map | `/scan`, `/odom`, map, TF | Robot pose and map-to-odom transform |
| Nav2 planner/controller | Plan a route and calculate motion commands | Map, robot pose, goal, sensor data | Path and `/cmd_vel` |
| Gazebo drive plugin | Move the simulated robot | `/controller/cmd_vel` | Robot motion and odometry |

## 4. Method

1. Start Gazebo with the ROSOrin Pro robot and its simulated sensors.
2. Check that the LiDAR is publishing `sensor_msgs/msg/LaserScan` on `/scan`.
3. Run SLAM Toolbox with simulation time enabled.
4. Drive around the environment so SLAM can build a map.
5. Save the map as a YAML file and an image.
6. Stop SLAM, restart Gazebo with navigation command routing enabled, and
   launch Nav2 using the saved map.
7. Set the robot's initial pose in RViz, then send a single goal or a list of
   waypoints.

## 5. Simulation Environment

The simulation is in `ros2_ws`, with the robot description in
`ros2_ws/src/simulations/rosorin_description` and the Gazebo package in
`ros2_ws/src/simulations/robot_gazebo`.

The simulated GPU LiDAR is attached to `lidar_frame`. It is configured for
10 Hz, 270 samples, approximately 156 degrees of field of view, and a range
of 0.15 to 12 metres. The ROS-Gazebo bridge exposes its scan on `/scan`.

The robot uses Gazebo's Mecanum drive plugin. Its command input is
`/controller/cmd_vel`. The Nav2 launch publishes the final command on
`/cmd_vel`, so start the simulation with `nav:=true` for the bridge to route
the command to the drive plugin.

## 6. Implementation

The ROS 2 packages used by the workflow are:

```text
ros2_ws/src/
├── simulations/
│   ├── robot_gazebo/          # Gazebo worlds, sensor setup, bridge, Nav2 config
│   └── rosorin_description/   # Robot model and LiDAR frame
└── slam/
    └── maps/                  # Saved map files
```

Install the ROS 2 Humble navigation and mapping packages if they are missing:

```bash
sudo apt update
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-slam-toolbox ros-humble-nav2-map-server
```

Build the workspace:

```bash
cd ~/EyeCodeEntry/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select rosorin_description robot_gazebo
source install/setup.bash
```

Run the `source` commands again in each new terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/EyeCodeEntry/ros2_ws/install/setup.bash
```

### Start Gazebo and drive the robot

In Terminal 1:

```bash
ros2 launch robot_gazebo room_worlds.launch.py
```

To drive manually, open another sourced terminal:

```bash
ros2 run robot_gazebo teleop_key_control
```

Use the keys printed by the teleop node (W/A/S/D). The Gazebo terminal needs
to stay running.

### Check and view the simulated sensors

From a sourced terminal:

```bash
ros2 topic list
ros2 topic hz /scan
ros2 topic echo /scan --once
```

In RViz, add a **LaserScan** display and set its topic to `/scan`. Use
`base_link` or `lidar_frame` as the Fixed Frame. Use `ros2 topic list` to see
the other bridged sensor topics, such as the camera and IMU.

### Run SLAM and save a map

Start Gazebo normally, then run SLAM in another sourced terminal:

```bash
ros2 launch "$(ros2 pkg prefix robot_gazebo)/share/robot_gazebo/launch/include/slam.launch.py" \
  use_sim_time:=true
```

The launch file is nested in `launch/include`, so launching it by package name
as `robot_gazebo include/slam.launch.py` may not find it. The command above
uses the installed launch file directly.

The SLAM launch also tries to open RViz. If RViz does not open, start it
separately:

```bash
rviz2 -d "$(ros2 pkg prefix robot_gazebo)/share/robot_gazebo/rviz/slam.rviz"
```

Drive slowly around the area to map it. When the map looks good, keep Gazebo
and SLAM running and save it:

```bash
mkdir -p ~/EyeCodeEntry/ros2_ws/src/slam/maps
ros2 run nav2_map_server map_saver_cli \
  -f ~/EyeCodeEntry/ros2_ws/src/slam/maps/map_01 \
  --ros-args -p map_subscribe_transient_local:=true
```

This should create `map_01.yaml` and `map_01.pgm` in
`ros2_ws/src/slam/maps`. Make sure `true` has no extra characters after it.

### Run autonomous navigation

Stop the SLAM launch with Ctrl+C. Restart Gazebo with navigation routing
enabled:

```bash
ros2 launch robot_gazebo room_worlds.launch.py nav:=true
```

In another sourced terminal, start Nav2 with the saved map:

```bash
ros2 launch "$(ros2 pkg prefix robot_gazebo)/share/robot_gazebo/launch/include/navigation.launch.py" \
  use_sim_time:=true \
  map:="$HOME/EyeCodeEntry/ros2_ws/src/slam/maps/map_01.yaml"
```

In the Nav2 RViz window:

1. Wait for the map and robot to appear.
2. Select **2D Goal Pose**, then click and drag at a reachable destination.
3. Nav2 should plan a path and send motion commands to the robot.

### Send multiple waypoints

In RViz, click **Waypoint / Nav Through Poses Mode**, then click the goal
poses on the map in the order you want the robot to visit them. Nav2 should
plan a route through the selected poses.


## 7. Experiments

| ID | Scenario | Expected behaviour | Status |
| --- | --- | --- | --- |
| E1 | Start the simulated robot | Robot and sensor topics are available | Gazebo launch was used |
| E2 | View LiDAR in RViz | Scan appears from `/scan` | Check with the commands above |
| E3 | Drive while SLAM is running | A map builds as the robot explores | Map was saved as `map_01` |
| E4 | Set one Nav2 goal | Robot follows the planned path | Path appeared; robot movement still needs verification |
| E5 | Send multiple waypoints | Robot visits each waypoint in order | Not yet confirmed |

## 8. Results

The Gazebo setup publishes a simulated LiDAR scan, and the SLAM workflow
produced a saved map at `ros2_ws/src/slam/maps/map_01`. Nav2 displayed a path
for a goal, but the robot did not move during the reported test. The Gazebo
launch was updated to pass `nav:=true` to the bridge, and the package built
successfully. Navigation still needs to be tested again with that setting.

## 9. Failure cases

- Sometimes the SLAM map becomes misaligned in parts of the room, so I have
  to scan that area again.
- A path can appear even when the robot is stationary. Check that Nav2 is
  publishing velocity commands and that they reach Gazebo:

  ```bash
  ros2 topic echo /cmd_vel --once
  ros2 topic echo /controller/cmd_vel --once
  ```

## 10. Discussion

This setup uses the same LiDAR topic for mapping and navigation. SLAM builds
the map while the robot moves; after saving the map, Nav2 uses it to localize
the robot and plan paths. Seeing a planned path is not by itself proof that
the robot is moving: the velocity command also has to reach the Gazebo drive
plugin.

## 11. Limitations

- This README covers the Gazebo simulation, not connecting a physical LiDAR.
- The map and navigation depend on working scan data, odometry, and TF.

## 12. Future works

- Find out why parts of the SLAM map sometimes become misaligned, then test
  possible fixes so I don't have to rescan those areas.
- Check whether the static `map -> odom` transform should be disabled during
  AMCL localization.
- Tune the SLAM and Nav2 settings for the simulated robot.

## 13. References

- [ROS 2 Humble documentation](https://docs.ros.org/en/humble/)
- [Hiwonder ROSOrin Pro User Manual] (https://wiki.hiwonder.com/projects/rosorin-pro/en/latest/docs/)
- [Nav2 documentation](https://docs.nav2.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- `robot_gazebo/urdf/lidar.gazebo.xacro` — simulated LiDAR settings.
- `robot_gazebo/launch/ros_ign_bridge.launch.py` — ROS-Gazebo topic bridge.
- `robot_gazebo/config/slam.yaml` — SLAM Toolbox settings.
- `robot_gazebo/config/nav2_params.yaml` — Nav2 settings.
