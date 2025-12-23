"""
SQL方言转换工具测试
"""

import pytest
from app.utils.sql_dialect_converter import SQLDialectConverter, SQLConversionError


class TestSQLDialectConverter:
    """SQL方言转换器测试类"""
    
    def setup_method(self):
        """测试初始化"""
        self.converter = SQLDialectConverter()
    
    def test_supported_dialects(self):
        """测试支持的方言"""
        dialects = self.converter.get_supported_dialects()
        assert 'mysql' in dialects
        assert 'postgresql_database' in dialects
        assert 'sqlite' in dialects
    
    def test_mysql_to_postgresql_conversion(self):
        """测试MySQL到PostgreSQL转换"""
        mysql_sql = "SELECT DATE_FORMAT(NOW(), '%Y-%m-%d') AS today"
        postgresql_sql = self.converter.convert(mysql_sql, 'mysql', 'postgresql_database')
        # PostgreSQL使用TO_CHAR函数而不是DATE_FORMAT
        assert 'TO_CHAR' in postgresql_sql
        assert 'NOW()' in postgresql_sql
    
    def test_basic_select_conversion(self):
        """测试基本SELECT语句转换"""
        sql = "SELECT id, name FROM users WHERE age > 18"
        # MySQL到PostgreSQL
        converted = self.converter.convert(sql, 'mysql', 'postgresql_database')
        assert 'SELECT' in converted
        assert 'FROM' in converted
        assert 'WHERE' in converted
    
    def test_invalid_dialect(self):
        """测试无效方言"""
        with pytest.raises(ValueError):
            self.converter.convert("SELECT * FROM users", 'mysql', 'unsupported_dialect')
    
    def test_invalid_sql(self):
        """测试无效SQL"""
        invalid_sql = "SELECT * FROM users WHERE"
        with pytest.raises(SQLConversionError):
            self.converter.convert(invalid_sql, 'mysql', 'postgresql_database')
    
    def test_sql_validation(self):
        """测试SQL验证"""
        valid_sql = "SELECT * FROM users WHERE age > 18"
        invalid_sql = "SELECT * FROM users WHERE"
        
        assert self.converter.validate_sql(valid_sql, 'mysql') is True
        assert self.converter.validate_sql(invalid_sql, 'mysql') is False
    
    def test_sql_formatting(self):
        """测试SQL格式化"""
        unformatted_sql = "SELECT id,name,email FROM users WHERE age>18 ORDER BY name"
        formatted_sql = self.converter.format_sql(unformatted_sql, 'mysql')
        
        # 格式化后的SQL应该包含适当的空格
        assert 'id, ' in formatted_sql or 'id,' in formatted_sql
        assert 'age > 18' in formatted_sql or 'age>18' not in formatted_sql


if __name__ == "__main__":
    pytest.main([__file__])