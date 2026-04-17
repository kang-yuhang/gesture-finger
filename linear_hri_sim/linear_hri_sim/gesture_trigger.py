import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped, TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
import threading

class GestureTrigger(Node):
    def __init__(self):
        super().__init__('gesture_trigger')
        # 订阅算法节点计算出的交点
        self.subscription = self.create_subscription(PointStamped, '/target_intersection', self.target_callback, 10)
        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self.latest_target = None
        
        # 开启一个后台线程监听键盘输入，模拟"大拇指"触发
        self.input_thread = threading.Thread(target=self.wait_for_gesture)
        self.input_thread.daemon = True
        self.input_thread.start()
        
        self.get_logger().info("🔫 指令手势节点已就绪！\n在当前终端按下回车键 (Enter) 模拟'伸出大拇指'的触发动作...")

    def target_callback(self, msg):
        self.latest_target = msg

    def wait_for_gesture(self):
        while rclpy.ok():
            input()  # 阻塞等待用户按回车
            if self.latest_target is not None:
                self.trigger_execution()
            else:
                self.get_logger().warn("还未捕捉到手指射线的交点！")

    def trigger_execution(self):
        x = self.latest_target.point.x
        y = self.latest_target.point.y
        z = self.latest_target.point.z
        
        self.get_logger().info(f"\n🎯 触发指令手势！锁定目标坐标: X={x:.3f}, Y={y:.3f}")
        
        # 发布一个静态 TF 坐标系，作为机器人的目标位姿
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.latest_target.header.frame_id
        t.child_frame_id = 'gesture_target'
        
        # 将目标位置设定在红点正上方 15 厘米处，防止机械臂撞击桌面
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = z + 0.15 
        
        # 设定机械臂末端垂直向下朝向桌面 (沿 Y 轴旋转 90 度的四元数)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.707
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 0.707
        
        self.tf_broadcaster.sendTransform(t)
        self.get_logger().info("✅ 已生成目标位姿 'gesture_target'，请在 RViz 中让机械臂执行移动！\n继续拖动手指，再次按回车可刷新目标...")

def main(args=None):
    rclpy.init(args=args)
    node = GestureTrigger()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
