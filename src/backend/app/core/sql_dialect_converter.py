"""
SQL方言转换工具类。

支持多种数据库方言之间的SQL语句转换。
"""

# backend/app/core/sql_dialect_converter.py

from typing import Optional, Dict, Any
try:
    import sqlglot
    from sqlglot import errors as sqlglot_errors
    SQLGLOT_AVAILABLE = True
except ImportError:
    SQLGLOT_AVAILABLE = False
    sqlglot = None
    sqlglot_errors = None

class SQLDialectConverter:
    """
    SQL方言转换器。

    支持在不同数据库方言之间转换SQL语句。

    Attributes:
        SUPPORTED_DIALECTS (Dict[str, str]): 支持的数据库方言映射表。
    """
    
    # 支持的数据库方言映射
    SUPPORTED_DIALECTS = {
        'mysql': 'mysql',
        'postgresql': 'postgres',
        'postgres': 'postgres',
        'sqlite': 'sqlite',
        'sqlserver': 'tsql',
        'tsql': 'tsql',
        'oracle': 'oracle',
        'bigquery': 'bigquery',
        'snowflake': 'snowflake',
        'redshift': 'redshift',
        'presto': 'presto',
        'trino': 'trino',
        'hive': 'hive',
        'spark': 'spark',
        'duckdb': 'duckdb'
    } if SQLGLOT_AVAILABLE else {}
    
    def __init__(self):
        """
        初始化 SQL 方言转换器。

        Raises:
            ImportError: 如果 sqlglot 库未安装。
        """
        if not SQLGLOT_AVAILABLE:
            raise ImportError(
                "sqlglot库未安装。请运行 'pip install sqlglot' 安装后再使用此功能。"
            )
    
    def convert(self, sql: str, source_dialect: str, target_dialect: str, 
                pretty: bool = False) -> str:
        """
        将SQL语句从源方言转换为目标方言。
        
        Args:
            sql (str): 要转换的SQL语句。
            source_dialect (str): 源数据库方言。
            target_dialect (str): 目标数据库方言。
            pretty (bool): 是否美化输出。
            
        Returns:
            str: 转换后的SQL语句。
            
        Raises:
            ValueError: 当指定的方言不支持时。
            SQLConversionError: 当SQL转换失败时。
        """
        # 验证方言是否支持
        if source_dialect not in self.SUPPORTED_DIALECTS:
            raise ValueError(f"不支持的源方言: {source_dialect}")
            
        if target_dialect not in self.SUPPORTED_DIALECTS:
            raise ValueError(f"不支持的目标方言: {target_dialect}")
            
        try:
            # 执行转换
            result = sqlglot.transpile(
                sql,
                read=self.SUPPORTED_DIALECTS[source_dialect],
                write=self.SUPPORTED_DIALECTS[target_dialect],
                pretty=pretty
            )
            return result[0] if result else sql
        except sqlglot_errors.ParseError as e:
            raise SQLConversionError(f"SQL解析错误: {str(e)}")
        except Exception as e:
            raise SQLConversionError(f"转换过程中发生错误: {str(e)}")
    
    def validate_sql(self, sql: str, dialect: str = 'mysql') -> bool:
        """
        验证SQL语法是否正确。
        
        Args:
            sql (str): 要验证的SQL语句。
            dialect (str): SQL方言，默认为MySQL。
            
        Returns:
            bool: 如果SQL语法正确返回True，否则返回False。
            
        Raises:
            ValueError: 当指定的方言不支持时。
        """
        if dialect not in self.SUPPORTED_DIALECTS:
            raise ValueError(f"不支持的方言: {dialect}")
            
        try:
            sqlglot.parse(sql, read=self.SUPPORTED_DIALECTS[dialect])
            return True
        except sqlglot_errors.ParseError:
            return False
        except Exception:
            return False
    
    def format_sql(self, sql: str, dialect: str = 'mysql', pretty: bool = True) -> str:
        """
        格式化SQL语句。
        
        Args:
            sql (str): 要格式化的SQL语句。
            dialect (str): SQL方言，默认为MySQL。
            pretty (bool): 是否美化输出。
            
        Returns:
            str: 格式化后的SQL语句。
            
        Raises:
            ValueError: 当指定的方言不支持时。
            SQLConversionError: 当格式化失败时。
        """
        if dialect not in self.SUPPORTED_DIALECTS:
            raise ValueError(f"不支持的方言: {dialect}")
            
        try:
            result = sqlglot.transpile(
                sql,
                read=self.SUPPORTED_DIALECTS[dialect],
                write=self.SUPPORTED_DIALECTS[dialect],
                pretty=pretty
            )
            return result[0] if result else sql
        except sqlglot_errors.ParseError as e:
            raise SQLConversionError(f"SQL解析错误: {str(e)}")
        except Exception as e:
            raise SQLConversionError(f"格式化过程中发生错误: {str(e)}")
    
    def get_supported_dialects(self) -> Dict[str, str]:
        """
        获取支持的方言列表。
        
        Returns:
            Dict[str, str]: 支持的方言字典。
        """
        return self.SUPPORTED_DIALECTS.copy()


class SQLConversionError(Exception):
    """SQL转换异常"""
    pass


# 使用示例
if __name__ == "__main__":
    # 示例：在不同数据库之间转换SQL
    converter = SQLDialectConverter()
    
    # # MySQL到PostgreSQL的转换示例
    # mysql_sql = "SELECT DATE_FORMAT(NOW(), '%Y-%m-%d') AS today"
    # try:
    #     postgresql_sql = converter.convert(mysql_sql, 'mysql', 'postgresql')
    #     print(f"MySQL: {mysql_sql}")
    #     print(f"PostgreSQL: {postgresql_sql}")
    # except SQLConversionError as e:
    #     print(f"转换失败: {e}")

    # PostgreSQL到MySQL的转换示例
    postgresql_sqls = """CREATE TABLE Hotel (Name TEXT NOT NULL, Address TEXT, Phone TEXT, PRIMARY KEY(Name));
CREATE TABLE Room (Type TEXT NOT NULL, Price NUMERIC, Quantity NUMERIC, PRIMARY KEY(Type));
CREATE TABLE Booking (BookingID TEXT NOT NULL, RoomType TEXT NOT NULL, StartDate DATETIME, EndDate DATETIME, PRIMARY KEY(BookingID), FOREIGN KEY(RoomType) REFERENCES Room(Type));
CREATE TABLE User (UserID TEXT NOT NULL, Name TEXT, Contact TEXT, Discount NUMERIC, CreditCard TEXT, PRIMARY KEY(UserID));
CREATE TABLE Booking_Room (BookingID TEXT NOT NULL, RoomType TEXT NOT NULL, Duration NUMERIC, RoomPreference TEXT, PRIMARY KEY(BookingID, RoomType), FOREIGN KEY(BookingID) REFERENCES Booking(BookingID), FOREIGN KEY(RoomType) REFERENCES Room(Type));
CREATE TABLE User_Booking (UserID TEXT NOT NULL, BookingID TEXT NOT NULL, PaymentMethod TEXT, LoyaltyProgram TEXT, PRIMARY KEY(UserID, BookingID), FOREIGN KEY(UserID) REFERENCES User(UserID), FOREIGN KEY(BookingID) REFERENCES Booking(BookingID));"""
    try:
        for sql in postgresql_sqls.split(';'):
            mysql = converter.convert(sql, 'sqlite', 'mysql')
            print(f"PostgreSQL: {sql}")
            print(f"MySQL: {mysql}")
    except SQLConversionError as e:
        print(f"转换失败: {e}")
    
    # # SQL验证示例
    # invalid_sql = "SELECT * FROM users WHERE"
    # is_valid = converter.validate_sql(invalid_sql, 'mysql')
    # print(f"SQL '{invalid_sql}' 有效性: {is_valid}")
    #
    # # SQL格式化示例
    # unformatted_sql = "SELECT id,name,email FROM users WHERE age>18 ORDER BY name"
    # formatted_sql = converter.format_sql(unformatted_sql, 'mysql')
    # print(f"格式化后: {formatted_sql}")
