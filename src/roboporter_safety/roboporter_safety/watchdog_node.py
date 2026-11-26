"""
Safety Watchdog Node for Roboporter V4.
- Monitors incoming teleoperation heartbeat timing (/teleop_cmd_vel) and battery voltage (/battery_status).
- If no teleop command arrives within `comms_timeout_sec`(default 250 ms) or a low-voltage fault occurs,
    this node publishes a zero-velocity
- Twist command to /failsafe_cmd_vel so `cmd_vel_mux` immediately halts the robot.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool, Float32
from std_srvs.srv import Trigger


class WatchdogNode(Node):
    """Supervises communication health and asserts high-priority stop commands."""
    def __init__(self):
        super().__init__('watchdog_node')

        # 1. Declare & Load ROS 2 Parameters (overridable via cmd_vel_mux.yaml)
        self.declare_parameter('comms_timeout_sec', 0.25)           # Max allowed gap between teleop msgs (250 ms)
        self.declare_parameter('publish_rate_hz', 25.0)             # Watchdog check loop frequency (25 Hz = 40 ms)
        self.declare_parameter('min_battery_voltage', 10.5)         # Minimum safe 12V battery threshold (V)
        self.declare_parameter('enable_battery_check', False)       # Disabled until voltage divider hardware is wired
        self.declare_parameter('auto_clear_comms_timeout', True)    # Automatically resume when valid teleop resumes

        self.comms_timeout = self.get_parameter('comms_timeout_sec').value
        self.rate_hz = self.get_parameter('publish_rate_hz').value
        self.min_batt = self.get_parameter('min_battery_voltage').value
        self.check_batt = self.get_parameter('enable_battery_check').value
        self.auto_clear = self.get_parameter('auto_clear_comms_timeout').value

        # 2. Internal State Variables
        self.last_teleop_time = None    # ROS Time object storing when the last /teleop_cmd_vel arrived
        self.battery_fault = False      # True if battery voltage drops below `min_batt`
        self.latched_fault = False      # Remains True until cleared by /reset_failsafe or auto-clear
        self.failsafe_active = True     # Start in safe/halted state until the first valid teleop frame arrives

        # 3. Subscribers (Inputs)
        #    Note: `_teleop_cb` and `_battery_cb` are passed as function references
        #    so ROS 2 invokes them automatically whenever new messages arrive
        self.create_subscription(Twist, '/teleop_cmd_vel', self._teleop_cb, 10)
        self.create_subscription(Float32, '/battery_status', self._battery_cb, 10)

        # 4. Publishers & Services (Outputs & Operator Controls)
        self.failsafe_pub = self.create_publisher(Twist, '/failsafe_cmd_vel', 10)
        self.health_pub = self.create_publisher(Bool, '/sys_health', 10)
        self.create_service(Trigger, '/reset_failsafe', self._reset_cb)

        # 5. Periodic Execution Timer
        #    Calls `_timer_cb` every (1 / 25.0) = 0.04 seconds (40 ms).
        self.create_timer(1.0 / self.rate_hz, self._timer_cb)
        self.get_logger().info(
            f'Watchdog active (timeout={self.comms_timeout * 1000:.0f} ms, rate={self.rate_hz:.0f} Hz)'
        )

    def _teleop_cb(self, _msg: Twist):
        """
        Topic callback for /teleop_cmd_vel.
        - Updates the heartbeat timestamp whenever a teleoperation command is received.
        - Note: `_msg` is prefixed with `_` because we only care that a message arrived
            (proving the link is alive), not its velocity values.
        - If auto-clear is enabled and there is no hardware battery fault,
            clear any previous timeout latch so driving can resume smoothly.
        """
        self.last_teleop_time = self.get_clock().now()
        if self.auto_clear and not self.battery_fault:
            self.latched_fault = False

    def _battery_cb(self, msg: Float32):
        """
        Topic callback for /battery_status.
        - Latches a failsafe fault if battery monitoring is enabled and voltage
            drops below `min_battery_voltage` (ignoring 0.0 V unconnected readings).
        """
        if self.check_batt and msg.data > 0.1 and msg.data < self.min_batt:
            if not self.battery_fault:
                self.get_logger().error(f'Low battery fault: {msg.data:.2f} V < {self.min_batt:.2f} V')
            self.battery_fault = True
            self.latched_fault = True

    def _reset_cb(self, _request, response):
        """
        Service callback for /reset_failsafe (std_srvs/srv/Trigger).
        - Clears active battery/latched faults when requested via CLI or Foxglove UI.
        """
        self.battery_fault = False
        self.latched_fault = False
        response.success = True
        response.message = 'Failsafe state cleared.'
        self.get_logger().info('Manual /reset_failsafe service triggered.')
        return response

    def _timer_cb(self):
        """
        Periodic timer callback running at `publish_rate_hz` (25 Hz).
        - Evaluates elapsed time since the last teleop message, publishes /sys_health,
            and continuously broadcasts zero-velocity Twist messages whenever a failsafe
            condition is active.
        """
        now = self.get_clock().now()

        comms_timed_out = True                                                              # Default until one telop msg is recieved       
        if self.last_teleop_time is not None:
            elapsed = (now - self.last_teleop_time).nanoseconds * 1e-9                      # ROS 2 Time in nanoseconds; convert to seconds
            comms_timed_out = elapsed > self.comms_timeout
        
        new_failsafe = comms_timed_out or self.battery_fault or self.latched_fault          # Engage failsafe if any of the conditions are triggered
        if new_failsafe != self.failsafe_active:
            state = 'ENGAGED (0 m/s halt)' if new_failsafe else 'CLEARED (teleop active)'
            self.get_logger().info(f'Watchdog state -> {state}')
        self.failsafe_active = new_failsafe

        health_msg = Bool()                                                                 # Log only on state transitions so the console is not flooded 
        health_msg.data = not self.failsafe_active
        self.health_pub.publish(health_msg)

        if self.failsafe_active:                                                            # While failsafe is active, publish a default all-zero Twist() (linear=0, angular=0)
            self.failsafe_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = WatchdogNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass                    
    finally:
        node.destroy_node()
        rclpy.shutdown()