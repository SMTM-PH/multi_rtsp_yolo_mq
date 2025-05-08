from common import yolo_logger
import numpy as np
import time

'''模型class name
    'cabin_cover_on'    机舱盖打开
    'cabin_cover_off'  机舱盖关闭
    'air_crew'         机组人员
    'red_on'           红色蒙皮安装
    'red_off'          红色蒙皮移除
    'aviator'          飞行员
'''

# 定义事件检测基类
class EventDetector:
    """基础事件检测类，提供通用的事件检测功能"""
    def __init__(self):
        # 存储前一帧的检测框
        self.previous_boxes = {
            'cabin_cover_on': None,
            'cabin_cover_off': None,
            'red_off': None,
            'red_on': None,
            'aviator': None
        }
        # 存储当前帧的检测框
        self.current_boxes = {
            'cabin_cover_on': None,
            'cabin_cover_off': None,
            'red_off': None,
            'red_on': None,
            'aviator': None
        }

        # 状态标志
        self.last_pilot_in_cockpit = 0  # 飞行员是否在座舱 0 无效 1在 2不在
        self.last_plane_in_hangar = False  # 飞机是否在机库
        self.last_cockpit_status = 0  # 座舱盖状态 0 无效 1打开 2关闭
        self.plane_is_moving = False  # 飞机是否在移动
        self.static_frame_count = 0  # 飞机静止帧数
        self.moving_frame_count = 0  # 飞机移动帧数
        self.movement_threshold = 50  # 移动阈值
        self.last_event_time = {}  # 记录每个事件的最后一次检测时间
        self.last_aviator_detected = False  # 记录上一帧是否检测到飞行员

    def calculate_iou(self, box1, box2):
        """计算两个框的交并比（IoU）"""
        if box1 is None or box2 is None:
            return 0
            
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # 计算交集的坐标
        x1_inter = max(x1_1, x1_2)
        y1_inter = max(y1_1, y1_2)
        x2_inter = min(x2_1, x2_2)
        y2_inter = min(y2_1, y2_2)

        # 计算交集的面积
        if x2_inter > x1_inter and y2_inter > y1_inter:
            area_inter = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        else:
            area_inter = 0

        # 计算两个框的面积
        area_box1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area_box2 = (x2_2 - x1_2) * (y2_2 - y1_2)

        # 计算并集的面积
        area_union = area_box1 + area_box2 - area_inter

        # 计算交并比
        if area_union == 0:
            return 0
        return area_inter / area_union

    def is_box_moving(self, current_box, previous_box):
        """检测边界框是否在移动"""
        if current_box is None or previous_box is None:
            return False
        # 计算y坐标的变化，判断是否有垂直移动
        y_movement = abs(current_box[1] - previous_box[1])
        return y_movement > self.movement_threshold

    def has_plane_parts(self, boxes_dict):
        """检查是否存在飞机部件
        飞机是否在机库"""
        return any(boxes_dict[part] is not None for part in ['cabin_cover_on', 'cabin_cover_off', 'red_off', 'red_on'])

    def is_aviator_outside_cockpit(self, aviator_box, cabin_box):
        """判断飞行员是否完全在座舱外"""
        if aviator_box is None or cabin_box is None:
            return False
        
        # 判断飞行员边界框是否完全在座舱边界框外
        # 情况1：飞行员在座舱左侧
        if aviator_box[2] < cabin_box[0]:
            return True
        # 情况2：飞行员在座舱右侧
        if aviator_box[0] > cabin_box[2]:
            return True
        # 情况3：飞行员在座舱上方
        if aviator_box[3] < cabin_box[1]:
            return True
        # 情况4：飞行员在座舱下方
        if aviator_box[1] > cabin_box[3]:
            return True
        # 如果不满足以上任何条件，说明飞行员边界框与座舱边界框有重叠
        return False

    def is_aviator_in_cockpit(self, aviator_box, cabin_box):
        """判断飞行员是否在座舱内"""
        if aviator_box is None or cabin_box is None:
            return False
        # 判断飞行员边界框是否完全在座舱边界框内
        return (aviator_box[0] >= cabin_box[0] and 
                aviator_box[2] <= cabin_box[2] and 
                aviator_box[1] >= cabin_box[1] and 
                aviator_box[3] <= cabin_box[3])

    def calculate_box_distance(self, box1, box2):
        """两个边界框中心点之间的欧氏距离"""
        if box1 is None or box2 is None:
            return float('inf')  # 如果任一框为空，返回无穷大距离
        
        # 计算第一个框的中心点
        center1_x = (box1[0] + box1[2]) / 2
        center1_y = (box1[1] + box1[3]) / 2
        
        # 计算第二个框的中心点
        center2_x = (box2[0] + box2[2]) / 2
        center2_y = (box2[1] + box2[3]) / 2
        
        # 计算两个中心点之间的欧氏距离
        distance = np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
        
        return distance

    def get_cockpit_state(self):
        """判断座舱盖状态"""
        if self.current_boxes['cabin_cover_on'] is not None:
            return 1  # 座舱盖打开
        elif self.current_boxes['cabin_cover_off'] is not None:
            return 2  # 座舱盖关闭
        return 0  # 无效状态

    def detect_events(self, results, is_first_detect, message=None):
        """基类的事件检测方法，子类应该重写此方法"""
        raise NotImplementedError("子类必须实现detect_events方法")


class LeftEventDetector(EventDetector):
    """左机库事件检测器"""
    def detect_events(self, results, is_first_detect, message=None):
        """检测所有事件并更新消息对象"""
        # 更新当前帧的检测框
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0].item())
                label = result.names[class_id]
                if label in self.current_boxes:
                    self.current_boxes[label] = box.xyxy[0].cpu().numpy().astype(int)
        
        current_time = time.time()

        # 初始化事件状态字典
        event_status = {
            'plane_sliding_status': 0,  # 0=无效, 1=入库, 2=出库, 3=静止
            'pilot_boarding_status': 0,  # 0=无效, 1=登机, 2=下机
            'pilot_in_hangar': 0,        # 0=不在机库, 1=在机库
            'cabin_cover_state': 0,       # 0=无效, 1=打开, 2=关闭
            'skin': 0,                   # 0=无效, 1=有, 2=无
            'cabin_occupied': 0,         
        }
        
        # 获取飞行员和座舱数据
        aviator_box = self.current_boxes['aviator']
        cabin_box = None
        if self.current_boxes['cabin_cover_on'] is not None:
            cabin_box = self.current_boxes['cabin_cover_on']
        elif self.current_boxes['cabin_cover_off'] is not None:
            cabin_box = self.current_boxes['cabin_cover_off']
        
        if self.current_boxes['red_on'] is not None:
            event_status['skin'] = 1
        elif self.current_boxes['red_off'] is not None:
            event_status['skin'] = 2

        # 检测飞行员进入机库
        current_aviator_detected = self.current_boxes['aviator'] is not None
        if current_aviator_detected:
            event_status['pilot_in_hangar'] = 1
            if not self.last_aviator_detected:
                last_time = self.last_event_time.get('aviator', 0)
                if current_time - last_time > 1200:  # 20分钟 = 1200秒
                    yolo_logger.info("检测到飞行员进入机库")
                    self.last_event_time['aviator'] = current_time
        else:
            event_status['pilot_in_hangar'] = 0
        self.last_aviator_detected = current_aviator_detected

        if is_first_detect:
            has_plane_now = self.has_plane_parts(self.current_boxes)
            self.last_plane_in_hangar = has_plane_now
            self.last_pilot_in_cockpit = self.is_aviator_in_cockpit(aviator_box, cabin_box)
            self.last_cockpit_status = self.get_cockpit_state()
        else:
            has_plane_now = self.has_plane_parts(self.current_boxes)
            
            # 飞机入库检测
            if not self.last_plane_in_hangar and has_plane_now:
                yolo_logger.info("检测到飞机入库")
                self.last_plane_in_hangar = True
                event_status['plane_sliding_status'] = 1
                # 检查是否存在plane_entering事件的上次时间记录
                if 'plane_entering' not in self.last_event_time:
                    self.last_event_time['plane_entering'] = current_time
                else:
                    # 如果存在记录则更新时间
                    self.last_event_time['plane_entering'] = current_time
            elif self.last_plane_in_hangar and not has_plane_now:
                yolo_logger.info("检测到飞机出库")
                self.last_plane_in_hangar = False
                event_status['plane_sliding_status'] = 2
                self.last_event_time['plane_exiting'] = current_time

            # 飞机座舱盖状态检测
            current_cockpit_status = self.get_cockpit_state()
            if self.last_cockpit_status == 2 and current_cockpit_status == 1:
                yolo_logger.info("检测到座舱开启")
                event_status['cabin_cover_state'] = 1
            if self.last_cockpit_status == 1 and current_cockpit_status == 2:
                yolo_logger.info("检测到座舱关闭")
                event_status['cabin_cover_state'] = 2
            self.last_cockpit_status = current_cockpit_status

            # 检测飞机是否在移动
            if self.last_plane_in_hangar and has_plane_now:
                is_moving = False
                for part in ['cabin_cover_on', 'cabin_cover_off', 'red_off', 'red_on']:
                    if (self.current_boxes[part] is not None and self.previous_boxes[part] is not None and
                            self.is_box_moving(self.current_boxes[part], self.previous_boxes[part])):
                        is_moving = True
                        break
                if not is_moving:
                    self.static_frame_count += 1
                    self.moving_frame_count = 0
                    if self.static_frame_count > 5:
                        if self.plane_is_moving:
                            self.plane_is_moving = False
                        yolo_logger.info("检测到飞机静止")
                        event_status['plane_sliding_status'] = 3
                else:
                    self.moving_frame_count += 1
                    self.static_frame_count = 0
                    if self.moving_frame_count > 5:
                        if not self.plane_is_moving:
                            self.plane_is_moving = True
                        yolo_logger.info("检测到飞机移动")
                        
            # 飞行员登机下机检测
            if aviator_box is not None and cabin_box is not None:
                if self.last_pilot_in_cockpit == 0:
                    self.last_pilot_in_cockpit = self.is_aviator_in_cockpit(aviator_box, cabin_box)
                else:
                    if self.last_pilot_in_cockpit == 1:
                        if self.is_aviator_outside_cockpit(aviator_box, cabin_box):
                            self.last_pilot_in_cockpit = 0
                            yolo_logger.info("检测到飞行员下机")
                            event_status['pilot_boarding_status'] = 2
                    elif self.last_pilot_in_cockpit == 2:
                        ret = self.is_aviator_in_cockpit(aviator_box, cabin_box)
                        if ret == 1:
                            yolo_logger.info("检测到飞行员登机")
                            event_status['pilot_boarding_status'] = 1
                            self.last_pilot_in_cockpit = 1

        # 更新消息对象
        if message:
            if isinstance(message, AircraftMessage):
                message.plane_sliding_status = event_status['plane_sliding_status']
                message.Pilot_boarding_status = event_status['pilot_boarding_status']
                message.pilot_in_the_hangar = event_status['pilot_in_hangar']
                message.cabin_cover = event_status['cabin_cover_state']
                message.skin = event_status['skin']
                message.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                message.event_type = 1  # 1=飞机事件
            elif isinstance(message, PersonnelMessage):
                message.personnel = 2 if self.current_boxes['aviator'] is not None else 0
                message.area_occupied = 1 if self.current_boxes['aviator'] is not None else 2
                message.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                message.event_type = 2  # 2=人员事件
            elif isinstance(message, VehicleMessage):
                message.vehicle = 0  # 当前没有车辆检测
                message.vehicle_type = 0  # 当前没有车辆类型检测
                message.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                message.event_type = 3  # 3=车辆事件
            elif isinstance(message, SafetyMessage):
                message.area_on_fire = 0  # 当前没有火灾检测
                message.timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                message.event_type = 4  # 4=安全事件
        
        # 更新前一帧的检测框
        self.previous_boxes = self.current_boxes.copy()
        self.current_boxes = {key: None for key in self.current_boxes}
        
        return event_status