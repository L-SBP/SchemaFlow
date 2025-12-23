"""
SQLite 用户隔离测试脚本。

用于验证不同用户ID的数据库文件隔离功能。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.base import SQLiteConfig
from sqlite.sqlite_database import SQLiteHelper
from sqlite.sqlite_execute import deploy_sqlite_ddl, execute_dql_user, execute_dml_user
from core.config import config


async def test_user_isolation():
    """测试用户隔离功能"""
    try:
        # 使用配置文件中的SQLite配置
        sqlite_config = config.sqlite

        # 测试用的DDL语句
        test_statements = [
            "CREATE TABLE user_data (id INTEGER PRIMARY KEY, user_id INTEGER, data TEXT)"
        ]

        print("开始测试用户隔离功能...")

        # 为用户10086创建数据库
        print("为用户10086创建数据库...")
        await deploy_sqlite_ddl("user_isolation_test", test_statements, sqlite_config, user_id=10086)
        
        # 为用户10087创建数据库
        print("为用户10087创建数据库...")
        await deploy_sqlite_ddl("user_isolation_test", test_statements, sqlite_config, user_id=10087)

        # 初始化用户10086的引擎
        print("初始化用户10086引擎...")
        await SQLiteHelper.init_user_engine(sqlite_config, 10086, "user_isolation_test", user_id=10086)
        
        # 初始化用户10087的引擎
        print("初始化用户10087引擎...")
        await SQLiteHelper.init_user_engine(sqlite_config, 10087, "user_isolation_test", user_id=10087)

        # 为用户10086插入数据
        print("为用户10086插入数据...")
        from models.database_instance import DatabaseInstance
        instance_10086 = DatabaseInstance()
        instance_10086.instance_id = 10086
        insert_sql_10086 = "INSERT INTO user_data (user_id, data) VALUES (10086, 'Data for user 10086')"
        await execute_dml_user(insert_sql_10086, instance_10086)

        # 为用户10087插入数据
        print("为用户10087插入数据...")
        instance_10087 = DatabaseInstance()
        instance_10087.instance_id = 10087
        insert_sql_10087 = "INSERT INTO user_data (user_id, data) VALUES (10087, 'Data for user 10087')"
        await execute_dml_user(insert_sql_10087, instance_10087)

        # 查询用户10086的数据
        print("查询用户10086的数据...")
        query_result_10086 = await execute_dql_user("SELECT * FROM user_data", instance_10086)
        print(f"用户10086看到的数据: {query_result_10086}")

        # 查询用户10087的数据
        print("查询用户10087的数据...")
        query_result_10087 = await execute_dql_user("SELECT * FROM user_data", instance_10087)
        print(f"用户10087看到的数据: {query_result_10087}")

        # 验证隔离 - 每个用户只能看到自己的数据
        if len(query_result_10086) == 1 and query_result_10086[0]['user_id'] == 10086:
            print("✓ 用户10086隔离验证成功")
        else:
            print(f"✗ 用户10086隔离验证失败: {query_result_10086}")
            
        if len(query_result_10087) == 1 and query_result_10087[0]['user_id'] == 10087:
            print("✓ 用户10087隔离验证成功")
        else:
            print(f"✗ 用户10087隔离验证失败: {query_result_10087}")

        # 清理资源
        await SQLiteHelper.close_user_engine(instance_10086)
        await SQLiteHelper.close_user_engine(instance_10087)
        
        print("用户隔离测试完成!")

    except Exception as e:
        print(f"用户隔离测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_user_isolation())