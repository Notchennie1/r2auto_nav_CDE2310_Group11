# import cv2


# cam = cv2.VideoCapture(0)


# aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
# parameters = cv2.aruco.DetectorParameters()
# detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

# try:

#     while True:
#         ret, frame = cam.read()
#         if not ret: 
#             break

#         corners, ids, _ = detector.detectMarkers(frame)
#         if ids is not None:
#             filename = "capture.jpg"
#             cv2.aruco.drawDetectedMarkers(frame, corners, ids)
#             cv2.imwrite(filename, frame)
#             print("Image Saved")
#             print(f"Found IDs: {ids.flatten()}")

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
# finally:
#     cam.release()
#     cv2.destroyAllWindows()



import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
import cv2
import time

class ArucoSimplePub(Node):
    def __init__(self):
        super().__init__('aruco_simple_pub')
        self.publisher_ = self.create_publisher(Point, 'target_pixels', 10)

        self.cap = cv2.VideoCapture(0)

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        self.timer = self.create_timer(0.033, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret: return

        corners, ids, _ = self.detector.detectMarkers(frame)
        
        if ids is not None:
            for i in range(len(ids)):
                c = corners[i][0]
                center_x = (c[0][0] + c[2][0]) / 2
                center_y = (c[0][1] + c[2][1]) / 2
                
                msg = Point()
                msg.x = float(center_x)
                msg.y = float(center_y)
                msg.z = float(ids[i][0])
                self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ArucoSimplePub()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()