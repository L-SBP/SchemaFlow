"""
MySQL 用户配置服务单元测试。

测试拆分后的各个函数的功能。
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import URL

from service.mysql_service import (
    create_mysql_user_with_plugin,
    grant_user_privileges,
    flush_privileges,
    alter_user_plugin,
    build_mysql_url,
    init_user_engine_with_plugin,
    create_mysql_user,
    _escape_sql_string
)


class TestMySQLUserService:
    """MySQL 用户服务测试类"""

    @pytest.fixture
    def mock_execute_sql_root(self):
        """模拟 execute_sql_root 函数"""
        with patch('service.mysql_service._execute_raw_sql') as mock:
            yield mock

    @pytest.fixture
    def mock_mysql_helper(self):
        """模拟 MysqlHelper 类"""
        with patch('service.mysql_service.MysqlHelper') as mock:
            yield mock

    @pytest.fixture
    def mock_config(self):
        """模拟 config 对象"""
        with patch('service.mysql_service.config') as mock:
            yield mock

    @pytest.fixture
    def mock_log(self):
        """模拟 log 对象"""
        with patch('service.mysql_service.log') as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_create_mysql_user_with_plugin_default(self, mock_execute_sql_root, mock_log):
        """测试使用默认插件创建用户"""
        db_username = "test_user"
        db_password = "password123"
        plugin = "sha256_password"
        
        await create_mysql_user_with_plugin(db_username, db_password)
        
        # 验证调用了两次 _execute_raw_sql（% 和 localhost）
        assert mock_execute_sql_root.call_count == 2
        
        # 验证 SQL 语句
        escaped_username = _escape_sql_string(db_username)
        escaped_host1 = _escape_sql_string("%")
        escaped_host2 = _escape_sql_string("localhost")
        escaped_password = _escape_sql_string(db_password)
        
        expected_calls = [
            f"CREATE USER '{escaped_username[1:-1]}'@'{escaped_host1[1:-1]}' IDENTIFIED WITH {plugin} BY {escaped_password}",
            f"CREATE USER '{escaped_username[1:-1]}'@'{escaped_host2[1:-1]}' IDENTIFIED WITH {plugin} BY {escaped_password}"
        ]
        
        actual_calls = [call.args[0] for call in mock_execute_sql_root.call_args_list]
        assert actual_calls == expected_calls
        
        # 验证日志调用
        assert mock_log.info.call_count == 4  # 2次执行日志 + 2次创建日志

    @pytest.mark.asyncio
    async def test_create_mysql_user_with_plugin_custom(self, mock_execute_sql_root, mock_log):
        """测试使用自定义插件创建用户"""
        db_username = "test_user"
        db_password = "password123"
        plugin = "mysql_native_password"
        
        await create_mysql_user_with_plugin(db_username, db_password, plugin)
        
        # 验证 SQL 语句包含正确的插件
        actual_calls = [call.args[0] for call in mock_execute_sql_root.call_args_list]
        for sql in actual_calls:
            assert plugin in sql

    @pytest.mark.asyncio
    async def test_grant_user_privileges(self, mock_execute_sql_root, mock_log):
        """测试授予用户权限"""
        db_name = "test_db"
        db_username = "test_user"
        
        await grant_user_privileges(db_name, db_username)
        
        # 验证调用了两次 _execute_raw_sql
        assert mock_execute_sql_root.call_count == 2
        
        # 验证 SQL 语句
        escaped_username = _escape_sql_string(db_username)
        escaped_host1 = _escape_sql_string("%")
        escaped_host2 = _escape_sql_string("localhost")
        
        expected_calls = [
            f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{escaped_username[1:-1]}'@'{escaped_host1[1:-1]}'",
            f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{escaped_username[1:-1]}'@'{escaped_host2[1:-1]}'"
        ]
        
        actual_calls = [call.args[0] for call in mock_execute_sql_root.call_args_list]
        assert actual_calls == expected_calls

    @pytest.mark.asyncio
    async def test_flush_privileges_success(self, mock_execute_sql_root, mock_log):
        """测试刷新权限成功"""
        with patch('service.mysql_service.execute_sql_root') as mock_exec_root:
            await flush_privileges()
            
            mock_exec_root.assert_called_once_with("FLUSH PRIVILEGES")
            mock_log.info.assert_called_once_with("[MySQL] Privileges flushed successfully")

    @pytest.mark.asyncio
    async def test_flush_privileges_failure(self, mock_log):
        """测试刷新权限失败"""
        with patch('service.mysql_service.execute_sql_root', side_effect=Exception("Flush failed")) as mock_exec_root:
            await flush_privileges()
            
            mock_log.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_alter_user_plugin(self, mock_execute_sql_root, mock_log):
        """测试修改用户插件"""
        db_username = "test_user"
        db_password = "password123"
        plugin = "mysql_native_password"
        
        await alter_user_plugin(db_username, db_password, plugin)
        
        # 验证调用了两次 _execute_raw_sql
        assert mock_execute_sql_root.call_count == 2
        
        # 验证 SQL 语句
        escaped_username = _escape_sql_string(db_username)
        escaped_host1 = _escape_sql_string("%")
        escaped_host2 = _escape_sql_string("localhost")
        escaped_password = _escape_sql_string(db_password)
        
        expected_calls = [
            f"ALTER USER '{escaped_username[1:-1]}'@'{escaped_host1[1:-1]}' IDENTIFIED WITH {plugin} BY {escaped_password}",
            f"ALTER USER '{escaped_username[1:-1]}'@'{escaped_host2[1:-1]}' IDENTIFIED WITH {plugin} BY {escaped_password}"
        ]
        
        actual_calls = [call.args[0] for call in mock_execute_sql_root.call_args_list]
        assert actual_calls == expected_calls

    def test_build_mysql_url_default(self):
        """测试构建默认 MySQL URL"""
        db_username = "test_user"
        db_password = "password123"
        db_name = "test_db"
        plugin = "sha256_password"
        
        url = build_mysql_url(db_username, db_password, db_name)
        
        assert url.username == db_username
        assert url.password == db_password
        assert url.database == db_name
        assert url.host == "localhost"
        assert url.port == 3306
        assert url.query["auth_plugin"] == plugin
        assert url.query["charset"] == "utf8mb4"

    def test_build_mysql_url_custom(self):
        """测试构建自定义 MySQL URL"""
        db_username = "test_user"
        db_password = "password123"
        db_name = "test_db"
        plugin = "mysql_native_password"
        host = "192.168.1.100"
        port = 3307
        
        url = build_mysql_url(db_username, db_password, db_name, plugin, host, port)
        
        assert url.username == db_username
        assert url.password == db_password
        assert url.database == db_name
        assert url.host == host
        assert url.port == port
        assert url.query["auth_plugin"] == plugin

    @pytest.mark.asyncio
    async def test_init_user_engine_with_plugin_success(self, mock_mysql_helper, mock_config, mock_log):
        """测试初始化用户引擎成功"""
        db_username = "test_user"
        db_password = "password123"
        db_name = "test_db"
        instance_id = 1
        plugin = "sha256_password"
        
        # 模拟 init_user_engine 成功
        mock_mysql_helper.init_user_engine = AsyncMock()
        
        result = await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, plugin)
        
        assert result is True
        mock_mysql_helper.init_user_engine.assert_called_once()
        mock_log.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_user_engine_with_plugin_failure(self, mock_mysql_helper, mock_config, mock_log):
        """测试初始化用户引擎失败"""
        db_username = "test_user"
        db_password = "password123"
        db_name = "test_db"
        instance_id = 1
        plugin = "sha256_password"
        
        # 模拟 init_user_engine 失败
        mock_mysql_helper.init_user_engine = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await init_user_engine_with_plugin(db_username, db_password, db_name, instance_id, plugin)
        
        assert result is False
        mock_log.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_mysql_user_success(self, mock_execute_sql_root, mock_mysql_helper, mock_config, mock_log):
        """测试创建 MySQL 用户成功（完整流程）"""
        db_name = "test_db"
        db_username = "test_user"
        db_password = "password123"
        instance_id = 1
        
        # 模拟 init_user_engine 成功
        mock_mysql_helper.init_user_engine = AsyncMock()
        
        await create_mysql_user(db_name, db_username, db_password, instance_id)
        
        # 验证调用顺序和次数
        assert mock_execute_sql_root.call_count >= 5  # 创建用户2次 + 授予权限2次 + 其他调用
        mock_mysql_helper.init_user_engine.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_mysql_user_fallback(self, mock_execute_sql_root, mock_mysql_helper, mock_config, mock_log):
        """测试创建 MySQL 用户时的插件回退机制"""
        db_name = "test_db"
        db_username = "test_user"
        db_password = "password123"
        instance_id = 1
        
        # 模拟第一次 init_user_engine 失败，第二次成功
        mock_mysql_helper.init_user_engine = AsyncMock(side_effect=[Exception("First try failed"), None])
        
        await create_mysql_user(db_name, db_username, db_password, instance_id)
        
        # 验证调用了修改插件的 SQL
        alter_calls = [call for call in mock_execute_sql_root.call_args_list 
                      if "ALTER USER" in call.args[0]]
        assert len(alter_calls) == 2  # % 和 localhost 各一次