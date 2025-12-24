"""
通用工具函数模块。

包含从业务代码中抽离的通用工具函数，遵循单一职责原则。
"""

import re
import random
import string
from pypinyin import lazy_pinyin, Style


def generate_meaningful_db_name(project_name: str, user_id: int) -> str:
    """
    根据项目名称和用户 ID 生成符合数据库命名规范的唯一数据库名。

    将项目名称转换为符合数据库命名规范的字符串 (拼音/英文 + 下划线)
    例如: "电商管理平台" -> "dianshang_guanli_pingtai_1_x82a"

    Args:
        project_name (str): 项目名称。
        user_id (int): 用户 ID。

    Returns:
        str: 生成的数据库名称。
    """
    # 1. 中文转拼音，英文单词保持不变
    pinyin_list = lazy_pinyin(project_name, style=Style.NORMAL)

    # 2. 拼接成字符串
    full_str = "_".join(pinyin_list)

    # 3. 清洗：只保留字母、数字和下划线，且转为小写
    clean_str = re.sub(r'[^a-zA-Z0-9_]', '_', full_str).lower()

    # 4. 去除连续的下划线
    clean_str = re.sub(r'_+', '_', clean_str).strip('_')

    # 5. 截断过长的前缀 (防止数据库名过长，保留前 40 字符)
    if len(clean_str) > 40:
        clean_str = clean_str[:40].rstrip('_')

    # 6. 加上 user_id 和短随机码 (确保全局唯一性)
    short_random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    return f"{clean_str}_{user_id}_{short_random}"


def generate_random_string(length: int = 8, include_digits: bool = True) -> str:
    """
    生成随机字符串。
    
    Args:
        length: 字符串长度
        include_digits: 是否包含数字
        
    Returns:
        str: 随机字符串
    """
    chars = string.ascii_lowercase
    if include_digits:
        chars += string.digits
    return ''.join(random.choices(chars, k=length))
