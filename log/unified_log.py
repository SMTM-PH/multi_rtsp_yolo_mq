import logging
import logging.config
import os
import time

# 默认日志配置
DEFAULT_LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
        },
        'mq_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'mq.log',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        'yolo_rtsp_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'rtsp_detection.log',
            'mode': 'a',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'mq': {
            'level': 'INFO',
            'handlers': ['console', 'mq_file'],
        },
        'yolo_rtsp': {
            'level': 'INFO',
            'handlers': ['console', 'yolo_rtsp_file'],
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}


def setup_logging(module_name='root', log_dir=None, log_file=None):
    """
    设置日志配置
    
    Args:
        module_name: 模块名称，用于选择对应的logger配置
        log_dir: 日志目录，如果提供，将覆盖默认配置中的日志路径
        log_file: 日志文件名，如果提供，将覆盖默认配置中的日志文件名
    
    Returns:
        logger: 配置好的日志记录器
    """
    config = DEFAULT_LOG_CONFIG.copy()
    
    # 如果提供了日志目录，确保目录存在
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # 根据模块名称选择对应的logger配置
    if module_name == 'mq':
        # 如果提供了日志目录和文件名，更新mq_file处理器的文件路径
        if log_dir and log_file:
            config['handlers']['mq_file']['filename'] = os.path.join(log_dir, log_file)
        elif log_dir:
            config['handlers']['mq_file']['filename'] = os.path.join(log_dir, 'mq.log')
        logger_name = 'mq'
    elif module_name == 'yolo_rtsp':
        # 如果没有提供日志文件名，使用带时间戳的默认文件名
        if not log_file:
            log_file = f'rtsp_detection_{time.strftime("%Y%m%d_%H%M%S")}.log'
        
        # 如果提供了日志目录和文件名，更新yolo_rtsp_file处理器的文件路径
        if log_dir:
            config['handlers']['yolo_rtsp_file']['filename'] = os.path.join(log_dir, log_file)
        logger_name = 'yolo_rtsp'
    else:
        # 使用root logger
        logger_name = ''
    
    # 应用日志配置
    logging.config.dictConfig(config)
    
    # 获取对应的logger
    return logging.getLogger(logger_name)


def get_mq_logger(log_dir=None, log_file='mq.log'):
    """
    获取MQ模块的日志记录器
    
    Args:
        log_dir: 日志目录，如果提供，将覆盖默认配置中的日志路径
        log_file: 日志文件名，如果提供，将覆盖默认配置中的日志文件名
    
    Returns:
        logger: 配置好的MQ模块日志记录器
    """
    return setup_logging('mq', log_dir, log_file)


# 用于存储已创建的logger实例
_loggers = {}

def get_yolo_rtsp_logger(log_dir=None, log_file=None):
    """
    获取YOLO RTSP模块的日志记录器
    
    Args:
        log_dir: 日志目录，如果提供，将覆盖默认配置中的日志路径
        log_file: 日志文件名，如果提供，将覆盖默认配置中的日志文件名
                 如果不提供，将使用带时间戳的默认文件名
    
    Returns:
        logger: 配置好的YOLO RTSP模块日志记录器
    """
    # 使用log_dir和log_file作为缓存键
    cache_key = f'yolo_rtsp_{log_dir}_{log_file}'
    
    # 如果logger已存在，直接返回缓存的实例
    if cache_key in _loggers:
        return _loggers[cache_key]
    
    # 创建新的logger实例
    logger = setup_logging('yolo_rtsp', log_dir, log_file)
    _loggers[cache_key] = logger
    return logger


def get_logger(name=None):
    """
    获取通用日志记录器，兼容MQProject/log/log.py中的get_logger函数
    
    Args:
        name: 日志记录器名称，如果不提供，将使用调用者的模块名
    
    Returns:
        logger: 配置好的日志记录器
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__')
    
    # 应用日志配置
    logging.config.dictConfig(DEFAULT_LOG_CONFIG)
    
    # 获取对应的logger
    return logging.getLogger(name)
