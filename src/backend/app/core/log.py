# backend/app/core/log.py

import sys
from functools import lru_cache
from loguru import logger

from .profile import Profile

class LogHelper:
    """
    日志系统辅助类。

    用于配置和管理应用的日志记录器，支持控制台和文件输出。
    """

    def __init__(self, log_file_name: str = "log"):
        """
        初始化日志配置。

        配置日志记录器，移除默认处理器，添加控制台和文件处理器，设置日志格式和轮转策略。

        Args:
            log_file_name (str): 日志文件名前缀，默认为 "log"。
        """
        # 初始化日志记录器
        self.logger = logger
        # 移除所有已有的日志处理器，情况日志设置
        self.logger.remove()

        # 使用Profile获取项目根目录
        # 确保日志目录存在,如果不存在就创建
        log_file_path = Profile.get_project_root() / "logs"
        log_file_path.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_path / f"{log_file_name}.log"
        
        # 定义日志输出的基本格式
        formatter = (
            "<green>{time:YYYYMMDD HH:mm:ss}</green> | "
            "{process.name} | "
            "{thread.name} | "
            "<cyan>{module}</cyan>.<cyan>{function}</cyan> | "
            "<level>{level}</level> | "
            "{message}"
        )
        
        # 添加控制台输出 (default levels until config is loaded)
        self.logger.add(
            sink=sys.stdout,
            format=formatter,
            level="INFO",
        )
        
        # 添加文件输出 (default levels until config is loaded)
        self.logger.add(
            sink=log_file_path,
            format=formatter,
            level="DEBUG",
            rotation="500 MB",
            retention="10 days",
            encoding="utf-8"
        )

    @lru_cache()
    def get_logger(self):
        """
        获取日志记录器实例。

        使用 LRU 缓存以确保单例模式。

        Returns:
            logger: loguru 日志记录器实例。
        """
        return self.logger

# 创建LogHelper 实例
log_helper = LogHelper()
# 获取日志记录器
log = log_helper.get_logger()
