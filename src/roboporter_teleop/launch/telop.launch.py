# Launch file for teloperatation
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('roboporter_teleop')
    config_file = os.path.join(pkg_share, 'config', 'teleop_config.yaml')

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        output='screen',
        parameters=[config_file],
        remappings=[('/cmd_vel', '/teleop_cmd_vel')],   # Remapping to prevent conflicting topic messages for priortiy hierachy 
    )

    return LaunchDescription([
        teleop_node,
    ])