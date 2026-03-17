import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

class TurtlebotMover(Node):
    def __init__(self):
        # Initialize the node with the name 'turtlebot_mover'
        super().__init__('turtlebot_mover')
        
        # Create a publisher that sends 'Twist' messages on the 'cmd_vel' topic
        # The '10' is the queue size (buffer)
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        
    def move_robot(self, linear_speed, angular_speed, duration):
        """
        Commands the robot to move at a specific velocity for a set time.
        """
        msg = Twist()
        msg.linear.x = linear_speed   # Forward/Backward (m/s)
        msg.angular.z = angular_speed # Turning (rad/s)
        
        self.get_logger().info(f'Publishing: Linear={linear_speed}, Angular={angular_speed} for {duration}s')
        
        # We must loop the publish command because the TurtleBot has a 
        # safety timeout (watchdog) that stops the motors if no command 
        # is received for ~0.5 seconds.
        end_time = time.time() + duration
        while time.time() < end_time:
            self.publisher_.publish(msg)
            time.sleep(0.1) # Send command at 10Hz (every 100ms)

    def creep_left(self, cycles=5):
        """
        Simulates creepwalking by waddling forward-left and backward-right.
        """
        self.get_logger().info(f"Starting creepwalk for {cycles} cycles...")
    
        for i in range(cycles):
            # STEP 1: Fast Forward-Left (The 'Reach')
            # We turn sharply left while moving forward
            self.move_robot(linear_speed=0.08, angular_speed=0.5, duration=0.6)
            
            # STEP 2: Slow Backward-Right (The 'Slide')
            # We back up slower and with less turn. 
            # This 'drags' the wheels and prevents them from returning to the start point.
            self.move_robot(linear_speed=-0.05, angular_speed=0.5, duration=0.8)
            
        self.stop_robot()
        self.get_logger().info("Creepwalk finished.")

    def stop_robot(self):
        """
        Sends a zero-velocity message to ensure the robot stops.
        """
        stop_msg = Twist()
        self.publisher_.publish(stop_msg)
        self.get_logger().info('Stopping robot...')

    def test_single_motor(self):
            self.get_logger().info("Spinning only the RIGHT wheel...")
            # On a Burger, 0.08 linear and 1.0 angular 
            # usually keeps the left wheel pinned to the floor.
            self.move_robot(linear_speed=0.08, angular_speed=1.0, duration=2.0)
            
            time.sleep(1.0)
            
            self.get_logger().info("Spinning only the LEFT wheel...")
            self.move_robot(linear_speed=0.08, angular_speed=-1.0, duration=2.0)
            
            self.stop_robot()

    def walk_left(self, cycles=5):
        self.get_logger().info(f"Starting walking creep for {cycles} cycles...")
        
        for i in range(cycles):
            # 1. Pivot on LEFT wheel (Right wheel forward)
            # Turning LEFT (Positive Angular)
            self.move_robot(linear_speed=0.08, angular_speed=1.0, duration=0.6)
            
            # 2. Pivot on RIGHT wheel (Left wheel backward)
            # Turning RIGHT (Negative Angular) to reset the nose
            self.move_robot(linear_speed=-0.08, angular_speed=-1.0, duration=0.6)
            
        self.stop_robot()

    def walk_left_modified(self, cycles=5):
        self.get_logger().info(f"Starting walking creep for {cycles} cycles...")
        
        for i in range(cycles):
            # 1. Pivot on LEFT wheel (Right wheel forward)
            # Turning LEFT (Positive Angular)
            self.move_robot(linear_speed=0.08, angular_speed=-1.0, duration=0.3)
            
            # 2. Pivot on RIGHT wheel (Left wheel backward)
            # Turning RIGHT (Negative Angular) to reset the nose
            self.move_robot(linear_speed=-0.08, angular_speed=1.0, duration=0.1)
            
        self.stop_robot()

    def waddle_fire(self, cycles=3):
        """
        Modified 4-phase waddle logic for the ping pong mission.
        Shifts the robot laterally while maintaining target heading.
        """
        # Constants adjusted for TurtleBot3 Burger limits
        LIN = 0.05  # Slow forward/back speed
        ANG = 0.6   # Rotation speed
        PHASE_DUR = 0.5 # Duration of each of the 4 phases
        
        self.get_logger().info(f"Initiating Waddle-Fire sequence for {cycles} cycles...")

        for i in range(cycles):
            self.get_logger().info(f"Waddle Cycle {i+1}")
            
            # Phase 0: Arc Left (Forward + Left Turn)
            self.move_robot(linear_speed=LIN, angular_speed=ANG, duration=PHASE_DUR)
            
            # Phase 1: Re-centre (Backward + Right Turn)
            # This 'undoes' the rotation but leaves the robot shifted
            self.move_robot(linear_speed=-LIN, angular_speed=-ANG, duration=PHASE_DUR)
            
            # Phase 2: Arc Right (Forward + Right Turn)
            self.move_robot(linear_speed=LIN, angular_speed=-ANG, duration=PHASE_DUR)
            
            # Phase 3: Re-centre (Backward + Left Turn)
            self.move_robot(linear_speed=-LIN, angular_speed=ANG, duration=PHASE_DUR)

        # After waddling, stop and trigger the launcher
        self.stop_robot()
        self.get_logger().info("Waddle complete. READY TO FIRE!")
    
    def sideways_shimmy_left(self, cycles=5):
        # Higher angular speed relative to linear speed creates a tighter "pivot"
        LIN = 0.05  
        ANG = 1.2   # Increased for a more "snappy" lateral shift
        DUR = 0.4   

        for i in range(cycles):
            # 1. Arc Forward-Left
            self.move_robot(linear_speed=LIN, angular_speed=ANG, duration=DUR)
            # 2. Arc Backward-Right (The Reset)
            # By reversing both, you theoretically return to the original heading 
            # but displaced laterally.
            self.move_robot(linear_speed=-LIN, angular_speed=-ANG, duration=DUR)
            
        self.stop_robot()

    def sideways_asymmetric_left(self, cycles=5):
        # PHASE 1: The Wide Swing (The "Reach")
        # We want a very wide arc to maximize Y-axis gain.
        FWD_LIN = 0.18   # Faster forward to create a wide arc
        FWD_ANG = 0.7    # Moderate turn
        FWD_DUR = 0.5    

        # PHASE 2: The Stationary Pivot (The "Snap")
        # We want to spin the nose back without moving the body backward.
        BWD_LIN = -0.01  # ALMOST ZERO. Just enough to let the wheels spin.
        BWD_ANG = -1.4   # Very fast rotation
        BWD_DUR = 0.3    # Short burst to correct heading

        for i in range(cycles):
            # 1. Swing out to the left
            self.move_robot(FWD_LIN, FWD_ANG, FWD_DUR)
            
            # Short pause to let physics settle
            time.sleep(0.1) 
            
            # 2. Pivot back to straight heading
            # This phase should look like the robot is spinning in place
            self.move_robot(BWD_LIN, BWD_ANG, BWD_DUR)
            
            time.sleep(0.1)
            
        self.stop_robot()

    def sideways_swing_left(self, cycles=5):
        # PHASE 1: The Wide Swing (The "Reach")
        # We need a large radius arc.
        # Linear must be high enough to force the robot to move forward while turning.
        SWING_LIN = 0.5   # Near max speed (0.22) to force a wide arc
        SWING_ANG = 0.5    # Low rotation so it doesn't just spin in place
        SWING_DUR = 0.5    

        # PHASE 2: The Tight Pivot (The "Reset")
        # Here, we WANT it to rotate without moving much.
        # We use very low linear and high angular.
        PIVOT_LIN = -0.1  
        PIVOT_ANG = -0.6   
        PIVOT_DUR = 0.2    

        for i in range(cycles):
            self.get_logger().info(f"Cycle {i+1}: Swinging Left...")
            self.move_robot(SWING_LIN, SWING_ANG, SWING_DUR)
            
            time.sleep(SWING_DUR) # Stabilization pause
            
            self.get_logger().info(f"Cycle {i+1}: Resetting Heading...")
            self.move_robot(PIVOT_LIN, PIVOT_ANG, PIVOT_DUR)
            
            time.sleep(PIVOT_DUR)
            
        self.stop_robot()

    def s_curve(self, cycles = 5):
        CURVE1_LIN = 0.5
        CURVE1_ANG = -0.5
        CURVE1_DUR = 0.5

        CURVE2_LIN = 0.5
        CURVE2_ANG = 0.5
        CURVE2_DUR = 0.5

        self.move_robot(CURVE1_LIN, CURVE1_ANG, CURVE1_DUR)
        time.sleep(0.1)

        self.move_robot(CURVE2_LIN, CURVE2_ANG, CURVE2_DUR)
        time.sleep(0.1)

        self.stop_robot()

    def left_turn(self):
        self.get_logger().info("Turn Left")
        self.move_robot(linear_speed=0.15, angular_speed=0.8, duration=1.6)

    def right_turn(self):
        self.get_logger().info("Turn Right")
        self.move_robot(linear_speed=0.15, angular_speed=-0.8, duration=1.6)

    




def main(args=None):
    # Initialize the ROS 2 Python communication
    rclpy.init(args=args)
    
    # Create the node instance
    mover = TurtlebotMover()
    
    try:
        # # Action 1: Move forward at 0.15 m/s for 2 seconds
        # mover.move_robot(0.15, 0.0, 2.0)
        
        # # Action 2: Spin in place (0.5 rad/s) for 1 second
        # mover.move_robot(0.0, 0.5, 1.0)
        
        # # Action 3: Stop
        # mover.stop_robot()

        # #creeo check - LEFT
        # mover.creep_left()

        # mover.test_single_motor()

        mover.left_turn()
        time.sleep(0.1)

        mover.right_turn()
        time.sleep(0.1)

        mover.stop_robot()
        
    except KeyboardInterrupt:
        # If you press Ctrl+C, try to stop the robot before exiting
        mover.stop_robot()
    finally:
        # Clean up and shutdown the node
        mover.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
