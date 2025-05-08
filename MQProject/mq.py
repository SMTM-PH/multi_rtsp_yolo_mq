import threading
from time import sleep

import pika
from pika.adapters.blocking_connection import BlockingConnection
from pika.connection import ConnectionParameters
import time
from message import Message
from log.unified_log import get_mq_logger  # 导入统一日志模块

from ultralytics import YOLO

# 获取MQ模块的日志记录器
_logger = get_mq_logger()


class RabbitMQ:
    _instance = None
    _lock = threading.Lock()
    _channel_lock = threading.Lock()  # 添加通道操作的锁

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RabbitMQ, cls).__new__(cls)
        return cls._instance

    def __init__(self, host='localhost', port=5672, username='guest', password='guest', hear_time=500):
        if hasattr(self, 'initialized'):
            return
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.initialized = True
        self.heart_time = hear_time
        self.is_connected = False
        self.thread_local = threading.local()  # 为每个线程存储独立的通道
        
        # 创建初始连接
        self.connect()
        _logger.info("RabbitMQ instance initialized")
        self.start_heartbeat()

    def connect(self):
        """创建到RabbitMQ的连接并初始化通道"""
        try:
            with self._lock:
                if self.connection is None or not self.connection.is_open:
                    self.connection = self.create_connection()
                    self.channel = self.connection.channel()
                    self.is_connected = True
                    _logger.info("Successfully connected to RabbitMQ")
                    # 声明常用队列
                    self.channel.queue_declare(queue='predicate')
                    self.channel.queue_declare(queue='heartbeat')
        except Exception as e:
            self.is_connected = False
            _logger.error(f"Failed to connect to RabbitMQ: {e}")
            # 连接失败后等待一段时间再重试
            time.sleep(5)

    def create_connection(self):
        """创建RabbitMQ连接"""
        return BlockingConnection(ConnectionParameters(
            host=self.host, 
            port=self.port,
            credentials=pika.PlainCredentials(self.username, self.password),
            heartbeat=60,  # 添加心跳检测
            blocked_connection_timeout=300  # 添加阻塞连接超时
        ))

    def get_channel(self):
        """获取当前线程的通道，如果不存在则创建"""
        if not hasattr(self.thread_local, 'channel'):
            try:
                with self._lock:
                    if not self.is_connected:
                        self.connect()
                    if self.is_connected:
                        self.thread_local.channel = self.connection.channel()
                        _logger.debug(f"Created new channel for thread {threading.current_thread().name}")
            except Exception as e:
                _logger.error(f"Failed to create channel: {e}")
                self.is_connected = False
                return None
        return self.thread_local.channel

    def create_queue(self, queue_name):
        """创建队列"""
        try:
            with self._channel_lock:
                channel = self.get_channel()
                if channel:
                    channel.queue_declare(queue=queue_name)
                    _logger.info(f"Queue created: {queue_name}")
        except Exception as e:
            _logger.error(f"Failed to create queue {queue_name}: {e}")
            self.is_connected = False

    def send_message(self, queue_name, message):
        """发送消息到指定队列"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                with self._channel_lock:
                    channel = self.get_channel()
                    if not channel:
                        raise Exception("No channel available")
                    
                    # 确保队列存在
                    channel.queue_declare(queue=queue_name, passive=True)
                    
                    # 发送消息
                    channel.basic_publish(exchange='', routing_key=queue_name, body=message)
                    _logger.info(f"Message sent to {queue_name}: {message}")
                    return True
            except pika.exceptions.ChannelClosedByBroker:
                # 通道被代理关闭，重新创建
                _logger.warning("Channel closed by broker, recreating...")
                self.thread_local.channel = None
                retry_count += 1
            except pika.exceptions.ConnectionClosedByBroker:
                # 连接被代理关闭，重新连接
                _logger.warning("Connection closed by broker, reconnecting...")
                self.is_connected = False
                self.connect()
                retry_count += 1
            except pika.exceptions.AMQPConnectionError:
                # AMQP连接错误，重新连接
                _logger.warning("AMQP connection error, reconnecting...")
                self.is_connected = False
                self.connect()
                retry_count += 1
            except Exception as e:
                _logger.error(f"Failed to send message: {e}")
                self.is_connected = False
                self.connect()
                retry_count += 1
            
            # 重试前等待
            time.sleep(1)
        
        _logger.error(f"Failed to send message after {max_retries} retries")
        return False

    def close_connection(self):
        """关闭RabbitMQ连接"""
        with self._lock:
            if hasattr(self, 'connection') and self.connection and self.connection.is_open:
                try:
                    self.connection.close()
                    self.is_connected = False
                    _logger.info("RabbitMQ connection closed")
                except Exception as e:
                    _logger.error(f"Error closing connection: {e}")

    def start_heartbeat(self):
        """启动心跳线程"""
        def heartbeat():
            while True:
                try:
                    time.sleep(self.heart_time)
                    self.send_message('heartbeat', 'Heartbeat message')
                except Exception as e:
                    _logger.error(f"Heartbeat error: {e}")
                    # 心跳失败，尝试重新连接
                    self.is_connected = False
                    self.connect()

        self._heartbeat_thread = threading.Thread(target=heartbeat)
        self._heartbeat_thread.daemon = True
        self._heartbeat_thread.start()

    def __del__(self):
        """析构函数，确保资源正确释放"""
        try:
            if hasattr(self, '_heartbeat_thread') and self._heartbeat_thread.is_alive():
                # 不能直接join，可能会导致死锁
                pass
            self.close_connection()
        except Exception as e:
            _logger.error(f"Error in __del__: {e}")
        _logger.info("RabbitMQ instance destroyed")


# 发送消息
def send_message():
    rabbit_mq = RabbitMQ('localhost', 5672, 'guest', 'guest')
    msg = Message(plane_sliding_status=0, personnel=1, skin=0, plane_number='ABC123', cabin_cover=1, hook_bin=0,
                  cabin_occupied=0, vehicle_type=2, vehicle=0, area_occupied=1, timestamp=int(time.time()),
                  event_type=0, camera_id=1)
    rabbit_mq.send_message('predicate', msg.to_json())


# 处理YOLO结果生成消息并发送到RabbitMQ

def parse_yolo_reslut():
    # Load a model
    model = YOLO("yolo11n.pt")
    results = model("https://ultralytics.com/images/bus.jpg")
    if results[0]:
        # return a list of Results objects
        boxes = results[0].boxes.cpu().numpy()
        # 输出模型中有哪些类别
        print(results[0].names)

        # 访问 boxes 属性，它包含了检测到的边界框，对应的类别得分，及对应的类别
        loc, scores, classes = [], [], []

        # # 遍历每个检测结果
        for box in boxes:
            loc.append(box.xyxy[0].tolist())
            scores.append(float(box.conf))
            classes.append(results[0].names[int(box.cls)])

        print(loc)
        print(scores)
        print(classes)
        results[0].save(filename="result.jpg")


# 使用示例
# if __name__ == "__main__":
#     # parse_yolo_reslut()
#     send_message()
#     sleep(10)
