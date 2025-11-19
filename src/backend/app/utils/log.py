import sys
from functools import lru_cache
from loguru import logger

from app.utils.profile import Profile
from app.server import config

class LogHelper:
    """
    日志系统
    """

    def __init__(self, log_file_name: str = "log"):
        """
        初始化日志
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
        )
        
        # 添加控制台输出
        self.logger.add(
            sink=sys.stdout,
            format=formatter,
            level=config.log.console_level,
        )
        
        # 添加文件输出
        self.logger.add(
            sink=log_file_path,
            format=formatter,
            level=config.log.file_level,
            rotation=config.log.rotation,
            retention=config.log.retention,
            encoding="utf-8"
        )

    @lru_cache()
    def get_logger(self):
        """
        获取日志记录器
        """
        return self.logger

# 创建LogHelper 实例
log_helper = LogHelper()
# 获取日志记录器
log = log_helper.get_logger()