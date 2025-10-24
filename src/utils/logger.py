"""
日志工具模块
用于为各个进程和线程提供统一的日志记录功能
日志文件按日期命名，保存在项目根目录的log文件夹下
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_level=logging.INFO):
    """
    配置并返回一个logger实例
    
    Args:
        name: logger的名称（建议使用进程/线程名称）
        log_level: 日志级别，默认为INFO
    
    Returns:
        logger实例
    """
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # 创建log目录
    log_dir = os.path.join(project_root, 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 使用日期作为日志文件名
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.log')
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建文件处理器（支持日志轮转，单个文件最大50MB，保留5个备份）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(processName)s-%(process)d] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name):
    """
    获取已存在的logger或创建新的logger
    
    Args:
        name: logger的名称
    
    Returns:
        logger实例
    """
    return logging.getLogger(name) if logging.getLogger(name).handlers else setup_logger(name)
