"""
PostgreSQL 安全模块。

提供 SQL 语句的安全校验、标准化及权限检查功能，防止 SQL 注入和越权操作。
"""

# backend/app/postgresql/postgres_secure.py

import re
from typing import List

from core.exceptions import SQLSecurityException
from core.config import config

def normalize_sql(sql: str) -> str:
    """
    标准化 SQL 语句。

    将 SQL 语句统一转换为大写，并去除多余的空格、换行符和注释，
    以便于后续的安全规则匹配。

    Args:
        sql (str): 原始 SQL 语句。

    Returns:
        str: 标准化后的 SQL 字符串。
    """
    # 去除注释（-- 单行注释）
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    # 去除换行/多个空格 → 单个空格
    sql = re.sub(r"\s+", " ", sql.strip())
    # 转大写
    return sql.upper()

def match_operation(sql: str, operation_patterns: List[str]) -> bool:
    """
    匹配 SQL 是否包含指定操作模式（支持 * 通配符）。

    Args:
        sql (str): 标准化后的 SQL 字符串。
        operation_patterns (List[str]): 操作模式列表（如 ["CREATE DATABASE *", "DROP *"]）。

    Returns:
        bool: 如果匹配到任意模式则返回 True，否则返回 False。
    """
    for pattern in operation_patterns:
        # 把通配符 * 转为正则匹配（匹配任意字符）
        regex_pattern = pattern.replace("*", ".*?").replace(" ", r"\s+")
        if re.search(regex_pattern, sql, flags=re.IGNORECASE):
            return True
    return False

def validate_safe_sql(sql: str, is_root: bool) -> None:
    """
    执行 SQL 安全权限检查。

    根据用户角色（Root 或普通用户）检查 SQL 语句是否包含被禁止的操作，
    或者是否在允许的操作列表中。

    Args:
        sql (str): 待检查的 SQL 语句。
        is_root (bool): 是否为 Root 用户权限。

    Raises:
        SQLSecurityException: 当操作被禁止或未在允许列表中时抛出。
    """
    normalized_sql = normalize_sql(sql)

    if is_root:
        allowed = config.sql_permissions.root.allowed_operations
        forbidden = config.sql_permissions.root.forbidden_operations
    else:
        allowed = config.sql_permissions.normal.allowed_operations
        forbidden = config.sql_permissions.normal.forbidden_operations

    if match_operation(normalized_sql, forbidden):
        raise SQLSecurityException("操作被禁止")

    if not match_operation(normalized_sql, allowed):
        raise SQLSecurityException("操作不被允许")
