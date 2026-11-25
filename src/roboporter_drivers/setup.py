from setuptools import find_packages, setup

package_name = 'roboporter_drivers'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='JinkoGH',
    maintainer_email='Ivangao64@gmail.com',
    description='Hardware serial bridge and sensor drivers for Roboporter V4',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'arduino_bridge_node = roboporter_drivers.arduino_bridge_node:main',
        ],
    },
)
