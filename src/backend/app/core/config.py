"""
配置管理模块。

负责加载和管理应用程序的配置，支持不同环境（dev/prod）的 YAML 配置文件加载。
支持环境变量覆盖 YAML 配置（格式：SECTION__KEY，如 DB__HOST）
"""

# backend/app/core/config.py

import os
import yaml
from functools import lru_cache

from config.base import BaseConfig
from core.profile import Profile
from core.log import log


def _override_with_env(config_dict: dict) -> dict:
    """
    使用环境变量覆盖配置字典中的值。
    
    环境变量格式：SECTION__KEY（双下划线分隔）
    例如：DB__HOST=postgres-meta 会覆盖 config_dict['db']['host']
    """
    # 定义需要检查的配置段及其环境变量前缀
    env_mappings = {
        'db': 'DB__',
        'redis': 'REDIS__',
        'chroma': 'CHROMA__',
        'mysql': 'MYSQL__',
        'postgresql': 'POSTGRESQL__',
    }
    
    for section, prefix in env_mappings.items():
        if section not in config_dict:
            continue
        
        for key in config_dict[section].keys():
            env_key = f"{prefix}{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 尝试转换类型
                original_value = config_dict[section][key]
                if isinstance(original_value, bool):
                    config_dict[section][key] = env_value.lower() in ('true', '1', 'yes')
                elif isinstance(original_value, int):
                    config_dict[section][key] = int(env_value)
                elif isinstance(original_value, float):
                    config_dict[section][key] = float(env_value)
                else:
                    config_dict[section][key] = env_value
                log.info("Override config {}.{} with env {}", section, key, env_key)
    
    return config_dict


@lru_cache()
def get_config(config_file="config.yaml", env=None) -> BaseConfig:
    """
    获取对应的环境变量配置。

    Args:
        config_file (str): 配置文件名称，默认为 "config.yaml"。
        env (str, optional): 指定环境（如 "dev", "prod"）。如果未提供，将尝试从配置文件中读取。

    Returns:
        BaseConfig: 对应环境的配置对象实例。
    """
    # 获取项目根目录
    project_root = Profile.get_project_root()
    # 获取config文件路径
    config_path = project_root.joinpath(config_file)
    # 读取 yaml 配置文件
    with open(config_path, "r", encoding="utf-8") as f:
        log.info("Load config from {}", config_path)
        yaml_config = yaml.safe_load(f)

    # 获取环境是dev还是prod
    if env:
        yaml_config["env"] = env
        log.info("Use env {}", env)
    else:
        env = yaml_config.get("env", "dev")
        log.info("Use env {}", env)

    # 根据环境获取对应的配置
    env_config = yaml_config.get(env, {})

    # 使用环境变量覆盖配置
    env_config = _override_with_env(env_config)

    # 返回对应的配置类实例
    return BaseConfig(**env_config)

settings = get_config()
config = settings  # 保留 config 别名，防止其他旧代码报错
