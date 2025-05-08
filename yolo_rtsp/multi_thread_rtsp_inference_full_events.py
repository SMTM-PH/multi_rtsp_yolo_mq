import cv2
import threading
import time
import os
import configparser

import sys

import sys
import os

# 获取当前文件所在目录的父目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将父目录添加到Python路径中
sys.path.append(parent_dir)

from ultralytics import YOLO
# 导入消息队列相关模块
from MQProject.message import Message
from MQProject.mq import RabbitMQ
from common import yolo_logger # 使用Python内置的logging模块替代无法导入的统一日志模块
from yolo_rtsp.EventDetector import EventDetector
from yolo_rtsp.RtspYoloConfig import RtspYoloConfig



# 模型训练的标签
labels=['cabin_cover_on','cabin_cover_off','air_crew','red_on','red_off','aviator']



# 定义处理单个摄像头 RTSP 流的函数
def process_rtsp_stream(rtsp_yolo_config):

        
    try:
        # 每个线程单独加载模型
        model = YOLO(rtsp_yolo_config.model_path)
        cap = cv2.VideoCapture(rtsp_yolo_config.rtsp_url)
        event_detector = EventDetector()
        frame_interval = 1  # 每秒处理一帧
        last_process_time = time.time()
        
        # 创建保存图片的目录
        output_dir = os.path.join(parent_dir, 'video', 'output', rtsp_yolo_config.camera_id)
        os.makedirs(output_dir, exist_ok=True)
        yolo_logger.info(f"创建输出目录: {output_dir}")
        
        # 帧计数器
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                current_time = time.time()
                if current_time - last_process_time >= frame_interval:
                    start_time = time.time()  # 记录开始处理的时间
                    # 在 GPU 上进行推理，device=0 表示使用第一个 GPU
                    results = model(frame, device=0)
                    # 获取检测结果中的飞行员和座舱的框坐标
                    current_pilot_box = None
                    current_cockpit_box = None
                    current_plane_detected = False
                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            class_id = int(box.cls[0])
                            label = model.names[class_id]
                    # 进行事件检测
                    event_status = event_detector.detect_events(results, rtsp_yolo_config.message)
                    
                    # 发送消息
                    if event_status and any(value != 0 for value in event_status.values()):
                        rtsp_yolo_config.message.message_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        rtsp_yolo_config.rabbit_mq.send_message('predicate', rtsp_yolo_config.message.to_json())
                        yolo_logger.info(f"已发送消息: {rtsp_yolo_config.message.to_json()}")
                    
                    
                    # 可视化检测结果
                    annotated_frame = results[0].plot()
                    cv2.imshow(rtsp_yolo_config.rtsp_url, annotated_frame)
                    
                    # 保存检测结果图片
                    frame_count += 1
                    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                    save_path = os.path.join(output_dir, f"{frame_count}_{timestamp}.jpg")
                    # 调整图片大小为宽度800像素，保持宽高比
                    height, width = annotated_frame.shape[:2]
                    new_width = 800
                    new_height = int(height * (new_width / width))
                    resized_frame = cv2.resize(annotated_frame, (new_width, new_height))
                    cv2.imwrite(save_path, resized_frame)
                    yolo_logger.info(f"保存检测结果图片: {save_path}")

                    end_time = time.time()  # 记录处理结束的时间
                    processing_time = end_time - start_time  # 计算处理时间
                    yolo_logger.info(f"处理 {rtsp_yolo_config.rtsp_url} 的一帧图像用时: {processing_time:.4f} 秒")

                    last_process_time = current_time

                # 按 'q' 键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        yolo_logger.error(f"处理 {rtsp_yolo_config.rtsp_url} 时出现错误: {e}")




if __name__=='__main__':
    yolo_logger.info("启动RTSP视频流处理")
    
    # 创建两个RTSP配置
    rtsp_config1 = RtspYoloConfig('admin', '123456','192.168.1.64', '554',
                                '1',r'E:\project\multi_rtsp_yolo_mq\yolo_rtsp\yolo11n.pt','1')
    
    rtsp_config2 = RtspYoloConfig('admin', '123456','192.168.1.65', '554',  # 第二个摄像头使用不同的IP
                                '2',r'E:\project\multi_rtsp_yolo_mq\yolo_rtsp\yolo11n.pt','2')
    
    # 创建两个线程处理不同的RTSP流
    thread1 = threading.Thread(target=process_rtsp_stream, args=(rtsp_config1,))
    thread2 = threading.Thread(target=process_rtsp_stream, args=(rtsp_config2,))
    
    # 启动线程
    thread1.start()
    thread2.start()
    
    # 等待线程结束
    thread1.join()
    thread2.join()
    