import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped, PoseStamped
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from shape_msgs.msg import SolidPrimitive
import threading

class AutoCommander(Node):
    def __init__(self):
        super().__init__('auto_commander')
        self.sub = self.create_subscription(PointStamped, '/target_intersection', self.point_callback, 10)
        self.latest_target = None
        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        self.get_logger().info("🤖 自动执行节点已就绪！按【回车】让 UR5 飞向红点...")
        threading.Thread(target=self.wait_for_trigger, daemon=True).start()

    def point_callback(self, msg):
        self.latest_target = msg.point

    def wait_for_trigger(self):
        while rclpy.ok():
            input()
            if self.latest_target:
                self.send_goal()
            else:
                self.get_logger().warn("尚未检测到红点坐标！")

    def send_goal(self):
        self.get_logger().info(f"✨ 触发！目标坐标: x={self.latest_target.x:.2f}, y={self.latest_target.y:.2f}")
        
        goal_msg = MoveGroup.Goal()
        goal_msg.request.group_name = "ur_manipulator"
        goal_msg.request.num_planning_attempts = 10
        goal_msg.request.allowed_planning_time = 5.0

        # 1. 位置约束 (Position Constraint)
        pos_con = PositionConstraint()
        pos_con.header.frame_id = "world"
        pos_con.link_name = "tool0"
        
        # 定义一个以红点为中心的小方块（1cm精度）作为目标区域
        point_pose = PoseStamped()
        point_pose.pose.position.x = self.latest_target.x
        point_pose.pose.position.y = self.latest_target.y
        point_pose.pose.position.z = 0.2  # 悬停高度
        
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.01, 0.01, 0.01]
        
        pos_con.constraint_region.primitives.append(box)
        pos_con.constraint_region.primitive_poses.append(point_pose.pose)
        pos_con.weight = 1.0

        # 2. 姿态约束 (Orientation Constraint - 末端垂直向下)
        ori_con = OrientationConstraint()
        ori_con.header.frame_id = "world"
        ori_con.link_name = "tool0"
        ori_con.orientation.x = 0.0
        ori_con.orientation.y = 0.707
        ori_con.orientation.z = 0.0
        ori_con.orientation.w = 0.707
        ori_con.absolute_x_axis_tolerance = 0.1
        ori_con.absolute_y_axis_tolerance = 0.1
        ori_con.absolute_z_axis_tolerance = 0.1
        ori_con.weight = 1.0

        # 封装约束
        constraints = Constraints()
        constraints.position_constraints.append(pos_con)
        constraints.orientation_constraints.append(ori_con)
        goal_msg.request.goal_constraints.append(constraints)

        # 发送请求
        self._action_client.wait_for_server()
        self._action_client.send_goal_async(goal_msg)

def main():
    rclpy.init()
    rclpy.spin(AutoCommander())
    rclpy.shutdown()