import re
from typing import List

from core.exceptions import SQLSecurityException
from core.config import config

def normalize_sql(sql: str) -> str:
    """
    标准化SQL：大写、去除多余空格、换行
    :param sql:
    :return:
    """
    # 去除注释（-- 单行注释）
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    # 去除换行/多个空格 → 单个空格
    sql = re.sub(r"\s+", " ", sql.strip())
    # 转大写
    return sql.upper()

def match_operation(sql: str, operation_patterns: List[str]) -> bool:
    """
    匹配SQL是否包含指定操作模式（支持*通配符）
    :param sql: 标准化后的SQL
    :param operation_patterns: 操作模式列表（如 ["CREATE DATABASE *"]）
    """
    for pattern in operation_patterns:
        # 把通配符 * 转为正则匹配（匹配任意字符）
        regex_pattern = pattern.replace("*", ".*?").replace(" ", r"\s+")
        if re.search(regex_pattern, sql, flags=re.IGNORECASE):
            return True
    return False

def validate_safe_sql(sql: str, is_root: bool) -> None:
    """
    权限检查
    :param sql:
    :return:
    """
    normalized_sql = normalize_sql(sql)

    if is_root:
        allowed = config.sql_permissions.root.allowed_operations
        forbidden = config.sql_permissions.root.forbidden_operations
    else:
        allowed = config.sql_permissions.normal.allowed_operations
        forbidden = config.sql_permissions.normal.forbidden_operations

    if match_operation(normalized_sql, forbidden):
        raise SQLSecurityException("Operation is forbidden")

    if not match_operation(normalized_sql, allowed):
        raise SQLSecurityException("Operation is not allowed")