"""
Launch file for the Roboporter V4 Safety & Velocity Arbitration Layer.

Starts both `watchdog_node` and `cmd_vel_mux` together as a single subsystem,
loading shared timeout and priority parameters from `config/cmd_vel_mux.yaml`.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('roboporter_safety')
    config_file = os.path.join(pkg_share, 'config', 'cmd_vel_mux.yaml')

    watchdog = Node(
        package='roboporter_safety',
        executable='watchdog_node',
        name='watchdog_node',
        output='screen',
        parameters=[config_file],
    )

    mux = Node(
        package='roboporter_safety',
        executable='cmd_vel_mux',
        name='cmd_vel_mux',
        output='screen',
        parameters=[config_file],
    )

    return LaunchDescription([
        watchdog,
        mux,
    ])