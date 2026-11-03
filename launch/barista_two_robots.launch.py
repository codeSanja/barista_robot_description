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

    def robot(name, color):
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

        return [robot_state_publisher]



    return LaunchDescription([
        gazebo,
        *robot("rick", "1 0 0 1"),
        *robot("morty", "0 0 1 1"),
    ])