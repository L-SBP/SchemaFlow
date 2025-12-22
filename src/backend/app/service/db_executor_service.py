# backend/app/service/db_executor_service.py

from core.sql_sort import sort_ddl_by_dependency
from core.exceptions import ValidationException
from mysql.mysql_execute import deploy_mysql_ddl
from core.log import log
from postgresql.postgres_execute import deploy_postgres_ddl


class DBExecutorService:
    """
    数据库部署调度服务。
    支持未来扩展 PostgreSQL, SQLite 等。
    """

    @classmethod
    async def deploy(cls, db_type: str, db_name: str, ddl: str, use_smart_parse: bool):
        # 1. 预处理：清洗 DDL（去除注释）
        cleaned_ddl = "\n".join([l for l in ddl.splitlines() if not l.strip().startswith('--')])

        # 2. 获取执行语句序列
        if use_smart_parse:
            try:
                # 拓扑排序并处理依赖（目前该函数已集成方言转换）
                execution_statements = sort_ddl_by_dependency(cleaned_ddl, dialect=db_type)
            except Exception as e:
                raise ValidationException(f"SQL 解析或排序失败: {str(e)}")
        else:
            execution_statements = [s.strip() for s in cleaned_ddl.split(';') if s.strip()]

        # 3. 根据类型分发执行 (策略模式雏形)
        if db_type == 'mysql':
            await deploy_mysql_ddl(db_name, execution_statements)
        elif db_type == 'postgresql':
            await deploy_postgres_ddl(db_name, execution_statements)
            raise NotImplementedError("PostgreSQL support coming soon")
        elif db_type == 'sqlite':
            # await deploy_sqlite_ddl(db_name, execution_statements)
            raise NotImplementedError("SQLite support coming soon")
        else:
            raise ValidationException(f"Unsupported database type: {db_type}")