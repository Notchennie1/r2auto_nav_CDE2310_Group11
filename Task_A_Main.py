import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist,Pose

class Task_A_Controller(Node):
        def __init__(self):
            super().__init__('main')

            self.subscription = self.create_subscription(Pose, 'target_3d', self.task_a, 10)
            self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)

            self.target_x = 0.10       # X offset of target from marker(for yaw)
            self.target_z = 0.07       #This is linear x in world system

            self.z_threshold = 0.02    # 2cm lateral tolerance
            self.x_threshold = 0.05    # ~5 degree tolerance

            self.lin_speed = 0.04      # 4cm/s
            self.ang_speed = 0.15      # rad/s

        def task_a(self,msg):
            marker_x = msg.position.x
            err_x = marker_x + self.target_x

            cmd = Twist()

            if abs(err_x) > self.x_threshold:
                cmd.linear.x = 0.0
                cmd.angular.z = -self.ang_speed if err_x > 0 else self.ang_speed
                print(err_x)

            elif (self.target_z > (self.target_z + self.z_thresold)):
                cmd.linear.x = self.lin_speed
                cmd.angular.z = 0.0

            else:
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                print("Ready to shoot")

            self.cmd_pub.publish(cmd)

def main(args=None):
        rclpy.init(args=args)
        node = Task_A_Controller()
        try:
            rclpy.spin(node)
            
        except KeyboardInterrupt:
            node.get_logger().info("Manual Shutdown")

        finally:
            node.cmd_pub.publish(Twist())
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
        main()






