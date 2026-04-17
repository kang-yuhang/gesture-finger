import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PointStamped
from visualization_msgs.msg import Marker
import math
import numpy as np

# 四元数转旋转矩阵的辅助函数
def quaternion_matrix(q):
    w, x, y, z = q.w, q.x, q.y, q.z
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
        [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
    ])

class IntersectionCalc(Node):
    def __init__(self):
        super().__init__('intersection_calc')
        
        # 1. 订阅虚拟手指的位姿
        self.subscription = self.create_subscription(
            PoseStamped,
            '/virtual_finger_pose',
            self.pose_callback,
            10)
            
        # 2. 发布交点（给机器人导航用）
        self.target_pub = self.create_publisher(PointStamped, '/target_intersection', 10)
        
        # 3. 发布视觉反馈（在 RViz 里画一个小红球，对应论文里的 Visual Feedback）
        self.marker_pub = self.create_publisher(Marker, '/intersection_marker', 10)
        
        self.get_logger().info("核心算法节点已启动：正在实时计算指尖射线与桌面的交点...")

    def pose_callback(self, msg):
        # 点 A：手指的当前坐标 (x0, y0, z0)
        p = msg.pose.position
        x0, y0, z0 = p.x, p.y, p.z
        
        # 获取方向向量：RViz 的箭头默认指向局部的 X 轴正方向 (1, 0, 0)
        # 我们用四元数把它旋转到全局坐标系，得到射线方向向量 v = (v1, v2, v3)
        rot_mat = quaternion_matrix(msg.pose.orientation)
        v = rot_mat.dot(np.array([1.0, 0.0, 0.0]))
        v1, v2, v3 = v[0], v[1], v[2]
        
        # 论文公式 (6): 计算参数 t = -z0 / v3
        # 如果 v3 >= 0，说明手指指向上方或平行于桌面，没有交点
        if v3 >= -0.01:
            return 

        t = -z0 / v3
        
        # 如果 t < 0，交点在手指后方，不合理
        if t < 0:
            return

        # 论文公式 (7): 计算交点 I(X, Y)
        Ix = x0 + v1 * t
        Iy = y0 + v2 * t
        Iz = 0.0  # 桌面高度
        
        # --- 发布逻辑 ---
        
        # 1. 发布给机器人的目标点
        target_msg = PointStamped()
        target_msg.header = msg.header
        target_msg.point.x, target_msg.point.y, target_msg.point.z = Ix, Iy, Iz
        self.target_pub.publish(target_msg)
        
        # 2. 发布给 RViz 的视觉反馈（红色的光标球）
        marker = Marker()
        marker.header = msg.header
        marker.ns = "intersection"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = Ix
        marker.pose.position.y = Iy
        marker.pose.position.z = Iz
        marker.scale.x = 0.05
        marker.scale.y = 0.05
        marker.scale.z = 0.01 # 扁平的圆盘
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 0.8
        self.marker_pub.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = IntersectionCalc()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
