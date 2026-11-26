"""
Velocity Command Multiplexer Node for Roboporter V4.

Acts as the single gatekeeper writing to `/cmd_vel`, arbitrating between
 multiple velocity command sources based on strict priority and message freshness:
    1. `/failsafe_cmd_vel` (Priority 1 - Highest: Watchdog zero-velocity halt)
    2. `/teleop_cmd_vel`   (Priority 2 - Manual operator gamepad commands)
    3. `/nav_cmd_vel`      (Priority 3 - Autonomous Nav2 commands, Phase 2)

If all sources are stale (older than `source_timeout_sec`) or manual mode is
 disabled via `/set_operation_mode`, the multiplexer outputs a safe zero-velocity
 `Twist` so the motors never coast on an outdated command.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool


class CmdVelMux(Node):
    """Arbitrates multiple Twist command streams into a single safe `/cmd_vel` output."""
    def __init__(self):
        super().__init__('cmd_vel_mux')

        # 1. Declare & Load ROS 2 Parameters (overridable via cmd_vel_mux.yaml)
        self.declare_parameter('publish_rate_hz', 25.0)         # Output loop rate to /cmd_vel (25 Hz = 40 ms)
        self.declare_parameter('source_timeout_sec', 0.25)      # Max age before an input channel expires (250 ms)

        self.rate_hz = self.get_parameter('publish_rate_hz').value
        self.timeout = self.get_parameter('source_timeout_sec').value

        # 2. Internal State & Channel Cache
        self.manual_enabled = True      # False forces a software failsafe lockout via /set_operation_mode
        self.active_channel = 'NONE'    # Tracks currently selected source to log transitions 
        self.channels = {               # Store timestamps 
            'failsafe': {'msg': Twist(), 'stamp': None},
            'teleop': {'msg': Twist(), 'stamp': None},
            'nav': {'msg': Twist(), 'stamp': None},
        }

        # 3. Subscribers (Command Input Channels)
        #    Inline `lambda` wrappers route all three topics into the single
        #    `_update(channel_name, msg)` helper method to avoid duplicate code
        self.create_subscription(Twist, '/failsafe_cmd_vel', lambda m: self._update('failsafe', m), 10)
        self.create_subscription(Twist, '/teleop_cmd_vel', lambda m: self._update('teleop', m), 10)
        self.create_subscription(Twist, '/nav_cmd_vel', lambda m: self._update('nav', m), 10)

        # 4. Publishers & Services
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_service(SetBool, '/set_operation_mode', self._mode_cb)

        # 5. Periodic Arbitration Timer
        #    Evaluates channel priorities and publishes `/cmd_vel` every 40 ms (25 Hz).
        self.create_timer(1.0 / self.rate_hz, self._timer_cb)
        self.get_logger().info('cmd_vel_mux ready (Priority: failsafe > teleop > nav)')

    def _update(self, name: str, msg: Twist):
        """
        Shared topic callback that caches the latest `Twist` message and arrival
         timestamp for the given input channel ('failsafe', 'teleop', or 'nav').
        """
        self.channels[name]['msg'] = msg
        self.channels[name]['stamp'] = self.get_clock().now()

    def _is_fresh(self, name: str, now) -> bool:
        """
        Returns True if the named channel has received at least one message and
         its age (`now - stamp`) is within `source_timeout_sec`
        """
        stamp = self.channels[name]['stamp']
        if stamp is None:
            return False
        return ((now - stamp).nanoseconds * 1e-9) <= self.timeout   # Convert ROS 2 Duration nanoseconds to seconds

    def _mode_cb(self, request, response):
        self.manual_enabled = bool(request.data)
        mode_str = 'Manual Teleop Enabled' if self.manual_enabled else 'Failsafe Lockout'
        response.success = True
        response.message = mode_str
        self.get_logger().info(f'Operation mode changed: {mode_str}')
        return response

    def _timer_cb(self):
        now = self.get_clock().now()

        # Force zero twist when any of the conditions are triggered
        if not self.manual_enabled or self._is_fresh('failsafe', now):      # Priority 1: Watchdog failsafe active OR operator lockout engaged 
            selected = 'failsafe'
            out_twist = Twist()
        elif self._is_fresh('teleop', now):                                 # Priority 2: Fresh manual gamepad velocity command
            selected = 'teleop'
            out_twist = self.channels['teleop']['msg']
        elif self._is_fresh('nav', now):                                    # Priority 3: Fresh autonomous navigation command (reserved for Phase 2 Nav2)
            selected = 'nav'
            out_twist = self.channels['nav']['msg']
        else:                                                               # Fallback: All channels stale/silent -> publish safe zero Twistsd
            selected = 'idle_zero'
            out_twist = Twist()

        if selected != self.active_channel:                                 # Log only on state transitions so the console is not flooded 
            self.active_channel = selected
            self.get_logger().info(f'Mux active source -> {self.active_channel}')

        self.cmd_pub.publish(out_twist)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelMux()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()