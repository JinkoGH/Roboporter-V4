import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'roboporter_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), ['../../config/teleop_config.yaml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='JinkoGH',
    maintainer_email='ivangao64@gmail.com',
    description='8BitDo Ultimate gamepad teleoperation configuration and launch files for Roboporter V4',
    license='MIT',
    extras_require={'test': ['pytest']},
    entry_points={'console_scripts': [],
    },
)
