# 日志模块初始化文件
from .unified_log import get_yolo_rtsp_logger, get_mq_logger, setup_logging

__all__ = ['get_yolo_rtsp_logger', 'get_mq_logger', 'setup_logging']