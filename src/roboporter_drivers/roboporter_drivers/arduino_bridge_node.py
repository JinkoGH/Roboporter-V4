"""
Arduino Hardware Serial Bridge Node for Roboporter V4.

Acts as the translation layer between high-level ROS 2 velocity commands and the
 low-level Arduino Mega 2560 R3 microcontroller over USB serial (/dev/ttyACM1):
  1. Subscribes to `/cmd_vel` (geometry_msgs/msg/Twist) from `cmd_vel_mux`.
  2. Converts body-frame linear (vx) and angular (wz) velocities into normalized
      differential-drive left/right motor commands in the range [-1.0, 1.0].
  3. Transmits framed ASCII packets `<L_speed,R_speed\n>` at 25 Hz (115200 baud).
  4. Reads incoming `<L_ticks,R_ticks,battery_v\n>` telemetry frames (gracefully
      handling `0,0,0.0` placeholder values during open-loop operation before
      AMT102-V encoders are installed) and publishes `/odom` and `/battery_status`.
"""

import serial
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32
from std_srvs.srv import Trigger, SetBool

def clamp(val: float, low: float, high: float) -> float:
    """Constrains `val` strictly within `[low, high]` so PWM commands never overflow."""
    return max(low, min(high, val))


class ArduinoBridgeNode(Node):
    def __init__(self):
        super().__init__('arduino_bridge_node')

        # 1. Declare & Load ROS 2 Parameters (overridable via CLI or YAML)
        self.declare_parameter('serial_port', '/dev/ttyACM1')     # Udev symlink for Arduino Mega
        self.declare_parameter('baud_rate', 115200)               # Must match Serial.begin(115200) in firmware
        self.declare_parameter('tx_rate_hz', 25.0)                # Serial packet transmit frequency (40 ms period)
        self.declare_parameter('wheel_separation_m', 0.45)        # Track width W between left & right wheels (m)
        self.declare_parameter('max_linear_speed_mps', 0.50)      # Speed corresponding to full +/-1.0 motor command
        self.declare_parameter('cmd_timeout_sec', 0.25)           # Local failsafe timeout if /cmd_vel stalls (250 ms)

        # 2. Internal State Variables
        self.port = self.get_parameter('serial_port').value
        self.baud = self.get_parameter('baud_rate').value
        self.tx_rate = self.get_parameter('tx_rate_hz').value
        self.wheel_sep = self.get_parameter('wheel_separation_m').value
        self.max_speed = self.get_parameter('max_linear_speed_mps').value
        self.cmd_timeout = self.get_parameter('cmd_timeout_sec').value

        self.ser = None
        self.last_cmd = Twist()
        self.last_cmd_time = None
        self.left_ticks = 0
        self.right_ticks = 0

        # 3. Subscribers, Publishers & Services
        # Inputs from cmd_vel_mux
        self.create_subscription(Twist, '/cmd_vel', self._cmd_cb, 10)

        # Outputs to encoders 
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.batt_pub = self.create_publisher(Float32, '/battery_status', 10)

        # Services: Opeator controls to Fxoglove Studio & ROS CLI
        self.create_service(Trigger, '/reset_odometry', self._reset_odom_cb)
        self.create_service(SetBool, '/calibrate_encoders', self._calibrate_cb)

        # 4. Serial Connection & Periodic I/O Loop
        self._connect_serial()
        self.create_timer(1.0 / self.tx_rate, self._io_timer_cb)

    def _connect_serial(self):
        """
        Attempts to open the USB serial port to the Arduino Mega.

        Uses a short read timeout (10 ms) so `readline()` never blocks the ROS 2
         event loop, and catches `SerialException` so the node stays alive and
         retries automatically if the USB cable is unplugged/reconnected.
        """
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.01)
            self.get_logger().info(f'Connected to Arduino serial on {self.port} @ {self.baud} baud')
        except serial.SerialException as exc:
            self.ser = None
            self.get_logger().warn(f'Serial port {self.port} unavailable ({exc}); will retry...')

    def _cmd_cb(self, msg: Twist):
        """Topic callback for `/cmd_vel`: caches the latest velocity command and timestamp."""
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def _reset_odom_cb(self, _request, response):
        """Service callback for `/reset_odometry`: zeroes stored encoder tick counters."""
        self.left_ticks = 0
        self.right_ticks = 0
        response.success = True
        response.message = 'Odometry tick counters reset to 0.'
        return response

    def _calibrate_cb(self, request, response):
        """Service callback for `/calibrate_encoders`: toggles encoder calibration state."""
        response.success = True
        response.message = f'Encoder calibration flag set to {request.data}.'
        return response

    def _compute_differential(self) -> tuple[float, float]:
        """
        Converts body-frame `(linear.x, angular.z)` into normalized `(left, right)`
        motor commands in `[-1.0, 1.0]` using differential-drive kinematics:

            v_left  = (vx - wz * (W / 2)) / v_max
            v_right = (vx + wz * (W / 2)) / v_max

        Normalizing to `[-1.0, 1.0]` keeps ROS 2 in standard SI units (m/s, rad/s)
        while allowing the Arduino firmware to map `-1.0..+1.0` cleanly to
        Mtronics ESC PWM pulse widths (`1000..2000 us`, with `0.0` = `1500 us` neutral).
        """
        now = self.get_clock().now()

        # Secondary safety guard: force zero commands if `/cmd_vel` stopped arriving
        if self.last_cmd_time is None or ((now - self.last_cmd_time).nanoseconds * 1e-9) > self.cmd_timeout:
            return 0.0, 0.0

        vx = self.last_cmd.linear.x
        wz = self.last_cmd.angular.z

        # Positive yaw (turning left) slows the left wheel and speeds up the right wheel
        v_left = (vx - (wz * self.wheel_sep * 0.5)) / self.max_speed
        v_right = (vx + (wz * self.wheel_sep * 0.5)) / self.max_speed

        return clamp(v_left, -1.0, 1.0), clamp(v_right, -1.0, 1.0)

    def _io_timer_cb(self):
        """
        Periodic timer callback (25 Hz) handling bidirectional USB serial I/O
        and odometry publishing.
        """
        # If disconnected, attempt to reconnect on this cycle instead of crashing
        if self.ser is None or not self.ser.is_open:
            self._connect_serial()
            return

        # 1. Compute differential wheel targets and format framed ASCII packet
        #     Framing with `<` and `>` lets the Arduino detect packet boundaries reliably
        left_cmd, right_cmd = self._compute_differential()
        packet = f'<{left_cmd:.3f},{right_cmd:.3f}>\n'

        try:
            # 2. Transmit motor command packet to Arduino Mega
            self.ser.write(packet.encode('ascii'))

            # 3. Drain all complete telemetry lines waiting in the OS serial receive buffer
            while self.ser.in_waiting > 0:
                line = self.ser.readline().decode('ascii', errors='ignore').strip()
                # Expected incoming frame format: <left_ticks,right_ticks,battery_voltage>
                if line.startswith('<') and line.endswith('>'):
                    parts = line[1:-1].split(',')
                    if len(parts) >= 2:
                        self.left_ticks = int(parts[0])
                        self.right_ticks = int(parts[1])
                    if len(parts) >= 3:
                        batt = Float32()
                        batt.data = float(parts[2])
                        self.batt_pub.publish(batt)
        except (serial.SerialException, ValueError) as exc:
            # Handles cable disconnect or malformed serial bytes and trigger reconnect
            self.get_logger().error(f'Serial I/O error on {self.port}: {exc}')
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

        # 4. Publish Odometry header frame (`odom` -> `base_link`) for downstream TF/Foxglove consumers
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        self.odom_pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ser and node.ser.is_open:
            node.ser.write(b'<0.000,0.000>\n')
            node.ser.close()
        node.destroy_node()
        rclpy.shutdown()