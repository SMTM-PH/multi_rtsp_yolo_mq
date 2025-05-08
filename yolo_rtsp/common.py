import os
import sys

# 获取当前文件所在目录的父目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将父目录添加到Python路径中
sys.path.append(parent_dir)

from log.unified_log import get_yolo_rtsp_logger
yolo_logger=get_yolo_rtsp_logger()

def get_rtsp_url(user_name, password, ip, port, channel_num):
    return f"rtsp://{user_name}:{password}@{ip}:{port}//Streaming/Chanels/{channel_num}"