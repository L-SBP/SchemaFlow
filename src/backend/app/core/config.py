import yaml
from functools import lru_cache

from config.base import BaseConfig
from core.profile import Profile
from core.log import log

@lru_cache()
def get_config(config_file="config.yaml", env=None) -> BaseConfig:
    """
    获取对应的环境变量

    :param config_file: 环境配置文件
    :param env: 获取的环境
    :return: 不同环境对应的配置类对象
    """
    # 获取项目根目录
    project_root = Profile.get_project_root()
    # 获取config文件路径
    config_path = project_root.joinpath(config_file)
    # 读取 yaml 配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        log.info(f"Load config from {config_path}")
        yaml_config = yaml.safe_load(f)

    # 获取环境是dev还是prod
    if env:
        yaml_config["env"] = env
        log.info(f"Use env {env}")
    else:
        env = yaml_config.get("env", "dev")
        log.info(f"Use env {env}")

    # 根据环境获取对应的配置
    env_config = yaml_config.get(env, {})

    # 返回对应的配置类实例
    return BaseConfig(**env_config)

config = get_config()