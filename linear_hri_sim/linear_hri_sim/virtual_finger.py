import rclpy
from rclpy.node import Node
from interactive_markers.interactive_marker_server import InteractiveMarkerServer
from visualization_msgs.msg import InteractiveMarker, InteractiveMarkerControl, Marker
from geometry_msgs.msg import PoseStamped

class VirtualFinger(Node):
    def __init__(self):
        super().__init__('virtual_finger')
        # 创建交互式标记服务器
        self.server = InteractiveMarkerServer(self, 'virtual_finger_server')
        # 创建位姿发布者，用来模拟 Leap Motion 输出手指位置
        self.pose_pub = self.create_publisher(PoseStamped, '/virtual_finger_pose', 10)

        self.create_finger()

    def create_finger(self):
        int_marker = InteractiveMarker()
        int_marker.header.frame_id = 'world'  # UR5 仿真的基准坐标系
        int_marker.name = 'index_finger'
        int_marker.description = 'Virtual Index Finger\n(Drag to point)'
        int_marker.scale = 0.3

        # 创建一个绿色的箭头来代表手指
        arrow = Marker()
        arrow.type = Marker.ARROW
        arrow.scale.x = 0.25  # 手指的长度 (点A到点B的距离)
        arrow.scale.y = 0.02
        arrow.scale.z = 0.02
        arrow.color.r = 0.0
        arrow.color.g = 1.0
        arrow.color.b = 0.0
        arrow.color.a = 1.0

        # 将箭头添加到控制组件中
        control = InteractiveMarkerControl()
        control.always_visible = True
        control.markers.append(arrow)
        int_marker.controls.append(control)

        # 添加 6 自由度的操作手柄 (平移和旋转)
        for axis, x, y, z in [('x', 1.0, 0.0, 0.0), ('y', 0.0, 1.0, 0.0), ('z', 0.0, 0.0, 1.0)]:
            # 旋转环
            rot_ctrl = InteractiveMarkerControl()
            rot_ctrl.name = f"rotate_{axis}"
            rot_ctrl.orientation.w = 1.0
            rot_ctrl.orientation.x, rot_ctrl.orientation.y, rot_ctrl.orientation.z = x, y, z
            rot_ctrl.interaction_mode = InteractiveMarkerControl.ROTATE_AXIS
            int_marker.controls.append(rot_ctrl)

            # 平移轴
            move_ctrl = InteractiveMarkerControl()
            move_ctrl.name = f"move_{axis}"
            move_ctrl.orientation.w = 1.0
            move_ctrl.orientation.x, move_ctrl.orientation.y, move_ctrl.orientation.z = x, y, z
            move_ctrl.interaction_mode = InteractiveMarkerControl.MOVE_AXIS
            int_marker.controls.append(move_ctrl)

        # 初始位置稍微抬高一点，模拟手悬在空中
        int_marker.pose.position.z = 0.4
        int_marker.pose.position.x = 0.5

        # 启动并绑定回调函数
        self.server.insert(int_marker, feedback_callback=self.feedback_callback)
        self.server.applyChanges()
        self.get_logger().info("虚拟手指已就绪！请在 RViz 中添加 'InteractiveMarkers' 显示项。")

    def feedback_callback(self, feedback):
        # 当你用鼠标拖动箭头时，实时发布它的位姿
        msg = PoseStamped()
        msg.header = feedback.header
        msg.pose = feedback.pose
        self.pose_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = VirtualFinger()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
