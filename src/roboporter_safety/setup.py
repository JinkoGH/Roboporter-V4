import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'roboporter_safety'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), ['../../config/cmd_vel_mux.yaml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='JinkoGH',
    maintainer_email='Ivangao64@gmail.com',
    description='Safety watchdog and velocity command multiplexer for Roboporter V4',
    license='MIT',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'watchdog_node = roboporter_safety.watchdog_node:main',
            'cmd_vel_mux = roboporter_safety.cmd_vel_mux:main',
        ],
    },
)
