import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    package_name = "barista_robot_description"
    package_share = get_package_share_directory(package_name)
    gz_sim_share = get_package_share_directory("ros_gz_sim")

    share_parent = os.path.join(get_package_prefix(package_name), "share")
    existing = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.pathsep.join(
        p for p in [existing, share_parent] if p
    )

    world_path = os.path.join(package_share, "worlds", "barrista_empty.world")
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": f"-r {world_path}"}.items(),
    )

    xacro_path = os.path.join(
        package_share, "xacro", "barista_robot_model.urdf.xacro"
    )

    def robot(name, color, x, y, yaw):
        # Run xacro with this robot's name and color.
        robot_description = ParameterValue(
            Command(f'xacro {xacro_path} robot_name:={name} color:="{color}"'),
            value_type=str,
        )

        robot_state_publisher = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            namespace=name,                    # node + relative topics → /rick/...
            parameters=[{
                "use_sim_time": True,
                "robot_description": robot_description,
                "frame_prefix": f"{name}/",    # TF frames → rick/...
            }],
            output="screen",
        )

        spawn = Node(
            package="ros_gz_sim",
            executable="create",
            namespace=name,                              # → /rick/... node name
            arguments=[
                "-name", name,                           # Gazebo model name
                "-topic", f"/{name}/robot_description",  # read THIS robot's URDF
                "-x", str(x), "-y", str(y), "-z", "0.2",
                "-Y", str(yaw),
            ],
            output="screen",
        )

        bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            namespace=name,                      # → /rick/parameter_bridge
            arguments=[
                f"/{name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
                f"/{name}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
                f"/{name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
                f"/{name}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
                f"/{name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            ],
            remappings=[(f"/{name}/tf", "/tf")],  # join the one shared ROS /tf
            output="screen",
        )

        world_to_odom = Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            namespace=name,
            arguments=[
                "--x", str(x), "--y", str(y), "--yaw", str(yaw),
                "--frame-id", "world",
                "--child-frame-id", f"{name}/odom",
            ],
            parameters=[{"use_sim_time": True}],
            output="screen",
        )

        return [robot_state_publisher, spawn, bridge, world_to_odom]


    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz",
        arguments=["-d", os.path.join(package_share, "rviz", "urdf_vis_two_robots.rviz")],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        gazebo,
        clock_bridge,
        rviz,
        *robot("rick", "1 0 0 1", 0.0, 0.0, 0.0),
        *robot("morty", "0 0 1 1", 1.5, 1.0, 0.0),
    ])