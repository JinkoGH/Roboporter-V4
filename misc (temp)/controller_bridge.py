# Node name: controller_bridge.py
# Description: The bridge receives JSON data from Windows PowerShell and publishes it to the ROS 2 /joy topic.
# Author: Nurul 

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import rclpy
from sensor_msgs.msg import Joy

rclpy.init()
node = rclpy.create_node('windows_controller_bridge')
publisher = node.create_publisher(Joy, '/joy', 10)

class ControllerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/joy':
            self.send_error(404)
            return

        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 4096:
                self.send_error(400)
                return

            data = json.loads(self.rfile.read(length))

            msg = Joy()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.axes = [float(x) for x in data['axes']]
            msg.buttons = [int(x) for x in data['buttons']]

            publisher.publish(msg)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except (ValueError, KeyError, TypeError):
            self.send_error(400)

print('Controller bridge listening on port 8765', flush=True)

try:
    HTTPServer(('127.0.0.1', 8765), ControllerHandler).serve_forever()
except KeyboardInterrupt:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
