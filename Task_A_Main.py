import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose
from nav_msgs.msg import Odometry
import math

class Task_A_Controller(Node):
    def __init__(self):
        super().__init__('Task_A_Controller')
        self.create_subscription(Pose, 'target_3d', self.task_a, 10)
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.drive_timer = self.create_timer(0.05, self.drive_callback)

        # Odom state
        self.current_x = 0.0
        self.current_y = 0.0
        self.start_x = 0.0
        self.start_y = 0.0
        self.distance_to_travel = 0.0

        # State machine: 'idle', 'rotating', 'driving'
        self.state = 'idle'
        self.rotation_start_time = None
        self.rotation_duration = 0.0
        self.rotation_cmd = 0.0

        # Parameters
        self.target_x_offset = 0.10
        self.target_z_stop = 0.07
        self.x_threshold = 0.02
        self.lin_speed = 0.04
        self.ang_speed = 0.2

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        if self.state == 'driving':
            dist_traveled = math.sqrt(
                (self.current_x - self.start_x)**2 +
                (self.current_y - self.start_y)**2
            )
            if dist_traveled >= self.distance_to_travel:
                self.stop_robot()
                self.state = 'idle'
                self.get_logger().info("Ready to Fire!!")

    def drive_callback(self):
        now = self.get_clock().now().nanoseconds / 1e9  # seconds

        if self.state == 'rotating':
            elapsed = now - self.rotation_start_time
            if elapsed < self.rotation_duration:
                cmd = Twist()
                cmd.angular.z = self.rotation_cmd
                self.cmd_pub.publish(cmd)
            else:
                # Rotation done — transition to driving
                self.stop_robot()
                self.get_logger().info("Rotation done. Driving forward.")
                self.state = 'driving'
                self.start_x = self.current_x
                self.start_y = self.current_y

        elif self.state == 'driving':
            cmd = Twist()
            cmd.linear.x = self.lin_speed
            self.cmd_pub.publish(cmd)

    def task_a(self, msg):
        if self.state != 'idle':
            return

        marker_id = int(msg.orientation.w)
        if marker_id != 1:
            return

        marker_x = msg.position.x
        marker_z = msg.position.z
        err_x = marker_x - self.target_x_offset

        if abs(err_x) > self.x_threshold:
            # Begin timed rotation (non-blocking)
            angle_to_turn = math.atan2(err_x, marker_z)
            self.rotation_duration = abs(angle_to_turn) / self.ang_speed
            self.rotation_cmd = -self.ang_speed if angle_to_turn > 0 else self.ang_speed
            self.rotation_start_time = self.get_clock().now().nanoseconds / 1e9
            self.state = 'rotating'
            self.get_logger().info(f"Rotating {math.degrees(angle_to_turn):.1f} deg...")

        else:
            # Already aligned — drive straight
            self.state = 'driving'
            self.start_x = self.current_x
            self.start_y = self.current_y
            self.distance_to_travel = marker_z - self.target_z_stop
            self.get_logger().info("Already aligned. Driving forward.")

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = Task_A_Controller()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()