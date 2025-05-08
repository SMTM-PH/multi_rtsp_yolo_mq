from MQProject.message import Message
from MQProject.mq import RabbitMQ


class RtspConfig:
    def __init__(self,user_name,password,ip,port,channel_num):
        self.user_name=user_name
        self.password=password
        self.ip=ip
        self.port=port
        self.channel_num=channel_num
    def get_rtsp_url(self):
        return f"rtsp://{self.user_name}:{self.password}@{self.ip}:{self.port}//Streaming/Chanels/{self.channel_num}"

class RtspYoloConfig:
    def __init__(self,user_name,password,ip,port,channel_num,model_path,camera_id):
        self.rtsp_config=RtspConfig(user_name,password,ip,port,channel_num)
        self.rtsp_url=self.rtsp_config.get_rtsp_url()
        self.model_path=model_path
        self.camera_id=camera_id
        self.rabbit_mq = RabbitMQ('localhost', 5672, 'guest', 'guest')
        self.message = Message(camera_id=self.camera_id)

    def send_message(self):

        self.message.plane_sliding_status=0
        self.message.personnel = 1
        self.message.skin = 0
        self.message.plane_number = 'ABC123'
        self.message.cabin_cover = 0
        self.message.hook_bin = 0
        self.message.cabin_occupied = 0
        self.message.vehicle_type = 0
        self.message.vehicle = 0
        self.message.area_occupied = 0
        self.message.timestamp = ''
        self.message.event_type = 0

        self.rabbit_mq.send_message('predicate', self.msg.to_json())