"""
数据库连接模块 - 等待队友完善配置
"""
from typing import Any

# 临时占位，等待队友完善数据库配置
class DatabaseConfig:
    """数据库配置占位类"""
    pass

# 这些会在队友完成数据库配置后实现
async def get_db():
    """数据库会话依赖 - 等待实现"""
    raise NotImplementedError("数据库配置尚未完成，请等待负责数据库的同学完善")

class AsyncSession:
    """模拟数据库会话"""
    def __init__(self):
        self.data = {}
    
    async def execute(self, *args, **kwargs):
        return MockResult()
    
    async def commit(self):
        pass
    
    async def refresh(self, obj):
        pass
    
    def add(self, obj):
        pass

class MockResult:
    """模拟查询结果"""
    def scalars(self):
        return self
    
    def all(self):
        return []
    
    def scalar_one_or_none(self):
        return None

# 临时使用的模拟数据库会话
async def get_mock_db():
    """返回模拟数据库会话用于开发测试"""
    return AsyncSession()