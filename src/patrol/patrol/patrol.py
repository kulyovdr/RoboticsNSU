from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


def choose_cmd(pose):
    cmd = Twist()
    if pose is not None:
        cmd.linear.x = 0.5
        cmd.angular.z = 0.3
    return cmd


class PatrolNode(Node):

    def __init__(self):
        super().__init__('patrol')
        self.pose = None
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_timer(0.1, self.timer_callback)

    def pose_callback(self, msg):
        self.pose = msg

    def timer_callback(self):
        self.cmd_pub.publish(choose_cmd(self.pose))


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
