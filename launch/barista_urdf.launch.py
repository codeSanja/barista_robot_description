"""Launch Gazebo, the Barista robot description, RViz, and the robot spawner."""

import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_name = "barista_robot_description"
    package_share = get_package_share_directory(package_name)
    gz_sim_share = get_package_share_directory("ros_gz_sim")

    # Preserve the model / mesh search paths from start_world.launch.py.
    # The my_box_bot_description dependency comes from the original launch file.
    box_bot_share = get_package_share_directory("my_box_bot_description")
    resource_paths = [
        os.path.join(get_package_prefix(package_name), "share"),
        os.path.join(get_package_prefix("my_box_bot_description"), "share"),
        os.path.join(package_share, "models"),
        os.path.join(box_bot_share, "meshes"),
    ]
    existing_paths = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    os.environ["GZ_SIM_RESOURCE_PATH"] = os.pathsep.join(
        dict.fromkeys(path for path in [existing_paths, *resource_paths] if path)
    )

    world_path = os.path.join(package_share, "worlds", "barrista_empty.world")
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": f"-r {world_path}"}.items(),
    )

    urdf_path = os.path.join(package_share, "urdf", "barista_robot_model.urdf")
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher_node",
        parameters=[
            {
                # Kept from the original barista_urdf.launch.py.
                "use_sim_time": False,
                "robot_description": ParameterValue(
                    Command(["xacro ", urdf_path]), value_type=str
                ),
            }
        ],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz_node",
        parameters=[{"use_sim_time": True}],
        arguments=["-d", os.path.join(package_share, "rviz", "urdf_vis.rviz")],
        output="screen",
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        name="my_robot_spawn",
        arguments=[
            "-name", LaunchConfiguration("model_name"),
            "-allow_renaming", "true",
            "-topic", "robot_description",
            "-x", LaunchConfiguration("x"),
            "-y", LaunchConfiguration("y"),
            "-z", LaunchConfiguration("z"),
            "-Y", LaunchConfiguration("yaw"),
        ],
        output="screen",
    )

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    tf_tree = Node(
        package="rqt_tf_tree",
        executable="rqt_tf_tree",
        name="rqt_tf_tree",
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("model_name", default_value="my_robot"),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("z", default_value="0.2"),
        DeclareLaunchArgument("yaw", default_value="3.14"),
        gazebo,
        robot_state_publisher,
        rviz,
        spawn_robot,
        joint_state_publisher_gui,
        tf_tree
    ])
