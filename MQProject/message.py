# coding=utf-8
import json
from datetime import time
import time


class Message:
    def __init__(self, timestamp=0, camera_id=0, event_type=0):
        self.timestamp = timestamp  # 时间
        self.message_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.camera_id = camera_id  # 摄像头编号
        self.event_type = event_type  # 事件类型：0 无效 ，1飞机，2人员，3车辆，4安全事件

    def to_json(self):
        message_dict = {
            'timestamp': self.timestamp,
            'message_time': self.message_time,
            'camera_id': self.camera_id,
            'event_type': self.event_type
        }
        return json.dumps(message_dict, ensure_ascii=False)


class AircraftMessage(Message):
    def __init__(self, timestamp=0, camera_id=0, event_type=1,
                 plane_sliding_status=0, Pilot_boarding_status=0, pilot_in_the_hangar=0,
                 skin=0, plane_number="", cabin_cover=0, hook_bin=0, cabin_occupied=0,
                 engine_status=0):
        super().__init__(timestamp, camera_id, event_type)
        self.plane_sliding_status = plane_sliding_status  # 飞机滑行状态：0无效，1入库，2出库 3 静止
        self.Pilot_boarding_status = Pilot_boarding_status  # 飞行员登机状态：0无效，1登机，2下机
        self.pilot_in_the_hangar = pilot_in_the_hangar  # 飞行员在机库：0无效，1在，2不在
        self.skin = skin  # 蒙皮：0：无效，1有，2无
        self.plane_number = plane_number  # 飞机编号 ""无效
        self.cabin_cover = cabin_cover  # 机舱盖：0无效，1打开，2关闭
        self.hook_bin = hook_bin  # 挂单仓：0 无效，1打开，2关闭
        self.cabin_occupied = cabin_occupied  # 机舱是否有人：0无效，1有人，2无人
        self.engine_status = engine_status  # 飞机引擎状态：0 无效，1关闭，2开启

    def to_json(self):
        message_dict = super().to_json()
        message_dict = json.loads(message_dict)
        message_dict.update({
            'plane_sliding_status': self.plane_sliding_status,
            'Pilot_boarding_status': self.Pilot_boarding_status,
            'pilot_in_the_hangar': self.pilot_in_the_hangar,
            'skin': self.skin,
            'plane_number': self.plane_number,
            'cabin_cover': self.cabin_cover,
            'hook_bin': self.hook_bin,
            'cabin_occupied': self.cabin_occupied,
            'engine_status': self.engine_status
        })
        return json.dumps(message_dict, ensure_ascii=False)


class PersonnelMessage(Message):
    def __init__(self, timestamp=0, camera_id=0, event_type=2,
                 personnel=0, area_occupied=0):
        super().__init__(timestamp, camera_id, event_type)
        self.personnel = personnel  # 人员：0 无效 ，1 机务人员 ，2飞行员
        self.area_occupied = area_occupied  # 指定区域检测，有无人员：0无效，1有，2无

    def to_json(self):
        message_dict = super().to_json()
        message_dict = json.loads(message_dict)
        message_dict.update({
            'personnel': self.personnel,
            'area_occupied': self.area_occupied
        })
        return json.dumps(message_dict, ensure_ascii=False)


class VehicleMessage(Message):
    def __init__(self, timestamp=0, camera_id=0, event_type=3,
                 vehicle_type=0, vehicle=0):
        super().__init__(timestamp, camera_id, event_type)
        self.vehicle_type = vehicle_type  # 车辆种类：0无效，1 加油车，2，3，4
        self.vehicle = vehicle  # 车辆：0无效，1有，2无

    def to_json(self):
        message_dict = super().to_json()
        message_dict = json.loads(message_dict)
        message_dict.update({
            'vehicle_type': self.vehicle_type,
            'vehicle': self.vehicle
        })
        return json.dumps(message_dict, ensure_ascii=False)


class SafetyMessage(Message):
    def __init__(self, timestamp=0, camera_id=0, event_type=4,
                 area_on_fire=0):
        super().__init__(timestamp, camera_id, event_type)
        self.area_on_fire = area_on_fire  # 区域是否着火：0无效，1否，2是

    def to_json(self):
        message_dict = super().to_json()
        message_dict = json.loads(message_dict)
        message_dict.update({
            'area_on_fire': self.area_on_fire
        })
        return json.dumps(message_dict, ensure_ascii=False)
