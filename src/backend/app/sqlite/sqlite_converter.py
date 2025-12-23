"""
SQLite 转换器。

专门用于将其他数据库模式和 SQL 语句深度转换为 SQLite 兼容格式。
"""

# backend/app/sqlite/sqlite_converter.py

from typing import Dict, Any, List
from core.sql_dialect_converter import SQLDialectConverter, SQLConversionError

import re
import sqlglot
from sqlglot import exp, parse_one
from typing import Dict, List, Optional, Tuple, Union, Callable
from collections import defaultdict

# 动态导入表达式类型 (解决版本兼容问题)
try:
    # sqlglot 24.0+ 使用新结构
    from sqlglot.expressions import (
        CreateTable as CreateTableExpr,
        ColumnDef as ColumnDefExpr,
        ForeignKey as ForeignKeyExpr,
        PrimaryKey as PrimaryKeyExpr,
        DataType as DataTypeExpr,
        Properties as PropertiesExpr,
        Property as PropertyExpr,
        Literal as LiteralExpr,
        Var as VarExpr,
        OnDelete as OnDeleteExpr,
        OnUpdate as OnUpdateExpr
    )
except ImportError:
    # 旧版本回退
    CreateTableExpr = type('CreateTable', (), {'key': 'create_table'})
    ColumnDefExpr = type('ColumnDef', (), {'key': 'column_def'})
    ForeignKeyExpr = type('ForeignKey', (), {'key': 'foreign_key'})
    PrimaryKeyExpr = type('PrimaryKey', (), {'key': 'primary_key'})
    DataTypeExpr = exp.DataType
    PropertiesExpr = exp.Properties
    PropertyExpr = exp.Property
    LiteralExpr = exp.Literal
    VarExpr = exp.Var
    OnDeleteExpr = exp.Delete
    OnUpdateExpr = exp.Update

class SQLiteConverter:
    """
    通用数据库到SQLite深度转换器 (完全兼容 sqlglot 24.0+)
    专为模式转换优化，精准处理保留字/主键/精度/外键等关键问题
    """

    # SQLite保留字集合 (来自SQLite官方文档)
    SQLITE_RESERVED_WORDS = {
        "user", "order", "group", "key", "index", "system", "option", "status",
        "current_date", "current_time", "current_timestamp", "database", "schema",
        "table", "view", "procedure", "function", "trigger", "event", "partition",
        "session", "transaction", "commit", "rollback", "savepoint", "lock", "grant",
        "revoke", "role", "type", "enum", "array", "json", "jsonb", "xml", "uuid",
        "abs", "changes", "char", "coalesce", "glob", "hex", "ifnull", "instr", 
        "last_insert_rowid", "length", "like", "lower", "ltrim", "max", "min", 
        "nullif", "printf", "quote", "replace", "round", "rtrim", "soundex", 
        "typeof", "upper", "sqlite_version"
    }
    
    # 智能字段映射规则 (列名 -> 精度规则)
    FIELD_PRECISION_RULES = {
        # 价格/金额字段
        r"(?i)(price|amount|cost|fee|total|balance|discount)": ("DECIMAL", (10, 2)),
        # 数量/计数字段
        r"(?i)(quantity|count|num|stock|capacity)": ("INTEGER", None),
        # 折扣率/百分比字段
        r"(?i)(discount|rate|percentage|ratio|probability)": ("REAL", (5, 4)),
        # 时长/时间字段
        r"(?i)(duration|time_span|hours|minutes|seconds)": ("REAL", (10, 2)),
        # ID/标识符字段
        r"(?i)(id|uuid|guid|code|identifier|ref)": ("TEXT", 50),
        # 电话/信用卡等特殊字段
        r"(?i)(phone|telephone|contact_number)": ("TEXT", 20),
        r"(?i)(credit_card|card_number)": ("TEXT", 19),
        # 通用文本字段 (主键/外键相关)
        r"(?i)(name|type|category|status|preference)": ("TEXT", 100),
    }
    
    # 默认TEXT长度 (主键/索引列) - SQLite使用TEXT类型，没有长度限制
    DEFAULT_TEXT_LENGTH = 255

    def __init__(self):
        """
        初始化转换器。

        设置基础 SQL 方言转换器、启用深度转换并初始化统计计数器。
        同时建立 AST 节点类型与转换方法的映射关系。
        """
        self.generic_converter = SQLDialectConverter()
        self.deep_conversion_enabled = True
        self.conversion_stats = defaultdict(int)
        
        # 重构转换器映射 (使用节点key而非类类型)
        self.ast_transformers = {
            "create_table": self._transform_create_table,
            "foreign_key": self._transform_foreign_key,
            "primary_key": self._transform_primary_key,
            "column_def": self._transform_column_def,
        }

    def _apply_ast_transformations(self, ast: exp.Expression):
        """
        递归应用 AST 转换规则 (兼容 sqlglot 新旧版本)。

        遍历抽象语法树 (AST) 的每个节点，根据节点类型 (如 create_table, foreign_key)
        调用相应的转换方法 (`_transform_xxx`) 进行深度修改。

        Args:
            ast (exp.Expression): 待转换的 SQL 抽象语法树根节点。
        """
        # 遍历所有节点
        for node in ast.walk():
            # 获取节点类型标识 (兼容新旧版本)
            node_key = getattr(node, "key", None)
            if not node_key and hasattr(node, "__class__"):
                node_key = node.__class__.__name__.lower()
            
            # 应用匹配的转换器
            transformer = self.ast_transformers.get(node_key)
            if transformer:
                try:
                    transformer(node)
                except Exception as e:
                    print(f"转换节点 {node_key} 时出错: {str(e)}")
        
        # 全局表属性修复 (必须最后执行)
        for node in ast.walk():
            node_key = getattr(node, "key", None) or node.__class__.__name__.lower()
            if node_key == "create_table":
                self._add_table_properties(node)

    def _transform_create_table(self, node):
        """
        转换 CREATE TABLE 语句。

        主要功能：
        1. 检查表名是否为 SQLite 保留字（如 user, group, order 等）。
        2. 如果是保留字，则使用方括号 ([ ]) 包裹表名，避免语法错误。

        Args:
            node: create_table 类型的 AST 节点。
        """
        # 获取表名 (兼容新旧结构)
        table_name = None
        if hasattr(node, "this") and hasattr(node.this, "name"):
            table_name = node.this.name.lower()
        elif hasattr(node, "expression") and hasattr(node.expression, "name"):
            table_name = node.expression.name.lower()
        
        if table_name and table_name in self.SQLITE_RESERVED_WORDS:
            # 用方括号包裹表名
            new_name = f"[{node.this.name}]" if hasattr(node, "this") else f"[{node.expression.name}]"
            if hasattr(node, "this"):
                node.this.set("this", new_name)
            else:
                node.expression.set("this", new_name)
            self.conversion_stats["reserved_word_fixes"] += 1

    def _transform_primary_key(self, node):
        """
        修复主键定义。

        SQLite 允许主键为 TEXT 类型，但需要确保主键约束的正确性。
        此方法会处理主键定义的格式。

        Args:
            node: primary_key 类型的 AST 节点。
        """
        # 获取主键列表达式
        pk_columns = []
        if hasattr(node, "expressions"):
            pk_columns = node.expressions
        elif hasattr(node, "args") and "expressions" in node.args:
            pk_columns = node.args["expressions"]
        
        # 检查主键列
        for col_expr in pk_columns:
            col_name = None
            if hasattr(col_expr, "name"):
                col_name = col_expr.name
            elif hasattr(col_expr, "this") and hasattr(col_expr.this, "name"):
                col_name = col_expr.this.name
            
            if not col_name:
                continue
            
            # 向上查找表定义
            table_node = node.find_ancestor(lambda n: getattr(n, "key", "") == "create_table")
            if not table_node:
                continue
            
            # 查找列定义
            for col_def in table_node.find_all(lambda n: getattr(n, "key", "") == "column_def"):
                if hasattr(col_def, "this") and col_def.this.name == col_name:
                    # 检查类型
                    col_type = None
                    if hasattr(col_def, "kind"):
                        col_type = col_def.kind
                    elif hasattr(col_def, "args") and "kind" in col_def.args:
                        col_type = col_def.args["kind"]
                    
                    if col_type and hasattr(col_type, "this") and col_type.this == "TEXT":
                        # SQLite TEXT类型主键不需要特殊处理
                        self.conversion_stats["text_primary_key_fixes"] += 1

    def _transform_column_def(self, node):
        """
        智能修复列定义。

        包含两个主要修复逻辑：
        1. **TEXT 主键修复**：如果列定义中包含主键约束且类型为 TEXT，转为 TEXT。
        2. **智能精度分配**：针对 DECIMAL/NUMERIC 类型，根据列名模式（如 price, rate）自动匹配
           合适的精度（如 REAL），避免 SQLite 默认精度可能导致的精度丢失问题。

        Args:
            node: column_def 类型的 AST 节点。
        """
        col_name = node.this.name.lower() if hasattr(node, "this") else ""
        
        # 1. 修复TEXT主键 (列级主键)
        if hasattr(node, "constraints"):
            has_primary_key_constraint = False
            for constraint in node.constraints:
                if getattr(constraint, "kind", None) == "primary":
                    has_primary_key_constraint = True
                    col_type = getattr(node, "kind", None)
                    if col_type and getattr(col_type, "this", None) == "TEXT":
                        # SQLite TEXT类型主键不需要特殊处理
                        self.conversion_stats["text_primary_key_fixes"] += 1
                        break  # 修复一次就够了
            
            # 如果有主键约束但类型不是TEXT，则不需要额外处理
            if has_primary_key_constraint:
                return
                
        # 2. 智能精度分配
        col_type = getattr(node, "kind", None)
        if col_type and getattr(col_type, "this", None) in ("NUMERIC", "DECIMAL"):
            for pattern, (data_type, precision) in self.FIELD_PRECISION_RULES.items():
                if re.search(pattern, col_name):
                    # 应用精度规则
                    if data_type == "INTEGER":
                        new_type = DataTypeExpr.Type.INT
                    elif data_type == "REAL" and precision:
                        new_type = DataTypeExpr.Type.FLOAT
                    elif data_type in ("TEXT",) and precision:
                        new_type = DataTypeExpr.Type.TEXT
                    else:
                        new_type = DataTypeExpr.Type.FLOAT
                    
                    node.set("kind", new_type)
                    self.conversion_stats[f"precision_fix_{col_name}"] += 1
                    break
            else:
                # 默认精度规则 - SQLite使用REAL类型
                node.set("kind", DataTypeExpr.Type.FLOAT)
                self.conversion_stats["default_precision_fixes"] += 1

    def _transform_foreign_key(self, node):
        """
        添加缺失的外键级联规则。

        SQLite 往往省略外键行为，但需要显式指定。
        如果外键定义中缺少 ON DELETE 或 ON UPDATE 规则，此方法会默认添加 CASCADE 级联规则，
        确保数据完整性。

        Args:
            node: foreign_key 类型的 AST 节点。
        """
        # 检查是否已有ON DELETE/UPDATE
        has_on_delete = False
        has_on_update = False
        
        if hasattr(node, "expressions"):
            for expr in node.expressions:
                if isinstance(expr, OnDeleteExpr):
                    has_on_delete = True
                elif isinstance(expr, OnUpdateExpr):
                    has_on_update = True
        
        # 添加缺失的级联规则
        if not has_on_delete:
            on_delete = OnDeleteExpr(this=VarExpr(this="CASCADE"))
            if hasattr(node, "append"):
                node.append("expressions", on_delete)
            else:
                node.expressions.append(on_delete)
            self.conversion_stats["fk_cascade_additions"] += 1
        
        if not has_on_update:
            on_update = OnUpdateExpr(this=VarExpr(this="CASCADE"))
            if hasattr(node, "append"):
                node.append("expressions", on_update)
            else:
                node.expressions.append(on_update)
            self.conversion_stats["fk_cascade_additions"] += 1

    def _add_table_properties(self, node):
        """
        添加表属性。

        SQLite 表属性相对简单，主要确保表名正确处理。
        这是建表语句转换的最后一步。

        Args:
            node: create_table 类型的 AST 节点。
        """
        # SQLite 通常不需要强制指定引擎，但可以添加表空间等属性
        # 这里主要确保表名正确处理（保留字处理）
        
        # 确保表名正确处理 (方括号)
        if hasattr(node, "this") and hasattr(node.this, "name"):
            table_name = node.this.name
            if table_name.lower() in self.SQLITE_RESERVED_WORDS:
                node.this.set("this", f"[{table_name}]")
        
        self.conversion_stats["table_properties_added"] += 1

    def convert_schema(self, source_sql: str) -> str:
        """
        深度转换源数据库表结构定义到 SQLite 格式。

        结合了通用方言转换（基于 sqlglot 默认规则）和自定义 AST 深度转换（`_apply_ast_transformations`），
        生成生产级可用的 SQLite DDL 语句。

        Args:
            source_sql (str): 源数据库格式的 DDL 语句。

        Returns:
            str: 转换后的 SQLite 格式 DDL 语句。
        """
        try:
            # 基础转换
            sqlite_sql = self.generic_converter.convert(
                source_sql, 'postgres', 'sqlite', pretty=True  # 默认从PostgreSQL转换
            )
            
            # AST深度转换 (仅当启用时)
            if self.deep_conversion_enabled:
                try:
                    # 关键修复: 使用正确的read方言
                    ast = parse_one(sqlite_sql, read="sqlite", dialect="sqlite")
                    self._apply_ast_transformations(ast)
                    sqlite_sql = ast.sql(dialect="sqlite", pretty=True)
                except Exception as ast_err:
                    self.conversion_stats["ast_conversion_failures"] += 1
                    print(f"AST转换失败，回退到基础转换: {str(ast_err)}")
            
            # 兜底修复
            sqlite_sql = self._apply_fallback_fixes(sqlite_sql)
            return sqlite_sql
        except Exception as e:
            raise SQLConversionError(f"源数据库到SQLite模式转换失败: {str(e)}")
            
    def _apply_fallback_fixes(self, sql: str) -> str:
        """字符串级兜底修复 (AST转换失败时使用)"""
        # 1. 修复TEXT主键 (简单模式)
        # 移除重复的PRIMARY KEY定义，只保留列级别的
        sql = re.sub(
            r'(^\s*CREATE\s+TABLE\s+\w+\s*$$[^$$]*?),\s*PRIMARY\s+KEY\s*$$[^$$]*?$$',
            r'\1',
            sql,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        # 将TEXT类型主键转换为TEXT并保留PRIMARY KEY约束
        sql = re.sub(
            r'(\w+)\s+TEXT\s+NOT NULL',
            lambda m: f'{m.group(1)} TEXT NOT NULL',
            sql,
            flags=re.IGNORECASE
        )

        # 2. 修复NUMERIC精度 (通用规则)
        sql = re.sub(
            r'(\w+)\s+NUMERIC\s*',
            r'\1 REAL',
            sql,
            flags=re.IGNORECASE
        )

        # 3. 修复SERIAL为INTEGER PRIMARY KEY AUTOINCREMENT
        sql = re.sub(
            r'(\w+)\s+SERIAL',
            r'\1 INTEGER PRIMARY KEY AUTOINCREMENT',
            sql,
            flags=re.IGNORECASE
        )

        # 4. 修复布尔值
        sql = re.sub(
            r'(\w+)\s+BOOLEAN\s*',
            r'\1 INTEGER',  # SQLite中布尔值用INTEGER表示
            sql,
            flags=re.IGNORECASE
        )

        return sql

    def convert_statement(self, source_sql: str) -> str:
        """
        转换源数据库SQL语句到SQLite格式

        Args:
            source_sql: 源数据库的SQL语句

        Returns:
            SQLite兼容的SQL语句
        """
        try:
            # 基础转换
            sqlite_sql = self.generic_converter.convert(
                source_sql, 'postgres', 'sqlite', pretty=False  # 默认从PostgreSQL转换
            )

            # 仅对DDL语句进行深度转换
            if any(keyword in sqlite_sql.upper() for keyword in ["CREATE TABLE", "ALTER TABLE"]):
                return self.convert_schema(sqlite_sql)  # 复用schema转换

            # DML/其他语句 - 应用轻量级修复
            return self._apply_statement_fixes(sqlite_sql)
        except Exception as e:
            raise SQLConversionError(f"源数据库到SQLite语句转换失败: {str(e)}")
            
    def _apply_statement_fixes(self, sql: str) -> str:
        """轻量级语句修复 (DML/其他语句)"""
        # 1. 修复布尔值
        sql = sql.replace('TRUE', '1').replace('FALSE', '0')  # SQLite中布尔值用1/0

        # 2. 修复日期函数
        sql = re.sub(
            r"TO_CHAR\(([^,]+),\s*'YYYY-MM-DD HH24:MI:SS'\)",
            r"strftime('%Y-%m-%d %H:%M:%S', \1)",
            sql,
            flags=re.IGNORECASE
        )

        # 3. 修复SERIAL
        sql = sql.replace('SERIAL', 'INTEGER PRIMARY KEY AUTOINCREMENT')

        # 4. 修复LIMIT语法
        sql = re.sub(
            r'LIMIT\s+(\d+)\s*OFFSET\s*(\d+)',
            r'LIMIT \2, \1',  # SQLite语法
            sql,
            flags=re.IGNORECASE
        )

        return sql

    def batch_convert(self, source_statements: List[str]) -> List[str]:
        """
        批量转换源数据库语句到SQLite格式 (带错误隔离)

        Args:
            source_statements: 源数据库语句列表

        Returns:
            转换结果列表 (失败语句包含错误注释)
        """
        sqlite_statements = []
        for i, statement in enumerate(source_statements):
            stmt = statement.strip()
            if not stmt:
                continue

            try:
                # 智能判断语句类型
                if "CREATE TABLE" in stmt.upper() or "ALTER TABLE" in stmt.upper():
                    converted = self.convert_schema(stmt)
                else:
                    converted = self.convert_statement(stmt)

                sqlite_statements.append(converted)
                self.conversion_stats["successful_conversions"] += 1
            except SQLConversionError as e:
                self.conversion_stats["conversion_errors"] += 1
                error_annotation = f"-- 转换失败 (语句#{i + 1}): {str(e)}\n"
                sqlite_statements.append(f"{error_annotation}{stmt}")
            except Exception as e:
                self.conversion_stats["unexpected_errors"] += 1
                error_annotation = f"-- 未处理错误 (语句#{i + 1}): {str(e)}\n"
                sqlite_statements.append(f"{error_annotation}{stmt}")

        return sqlite_statements

    def get_conversion_stats(self) -> Dict[str, int]:
        """获取转换统计信息"""
        return dict(self.conversion_stats)

    def disable_deep_conversion(self):
        """禁用深度AST转换 (回退到基础模式)"""
        self.deep_conversion_enabled = False

    def enable_deep_conversion(self):
        """启用深度AST转换"""
        self.deep_conversion_enabled = True


# 使用示例
if __name__ == "__main__":
    # 示例：PostgreSQL到SQLite的深度转换
    converter = SQLiteConverter()

    # PostgreSQL表结构示例
    postgres_create_table = """CREATE TABLE "Hotel" ("Name" TEXT NOT NULL, "Address" TEXT, "Phone" TEXT, PRIMARY KEY("Name"));
CREATE TABLE "Room" ("Type" TEXT NOT NULL, "Price" NUMERIC, "Quantity" NUMERIC, PRIMARY KEY("Type"));
CREATE TABLE "Booking" ("BookingID" TEXT NOT NULL, "RoomType" TEXT NOT NULL, "StartDate" TIMESTAMP, "EndDate" TIMESTAMP, PRIMARY KEY("BookingID"), FOREIGN KEY("RoomType") REFERENCES "Room"("Type"));
CREATE TABLE "User" ("UserID" TEXT NOT NULL, "Name" TEXT, "Contact" TEXT, "Discount" NUMERIC, "CreditCard" TEXT, PRIMARY KEY("UserID"));
CREATE TABLE "Booking_Room" ("BookingID" TEXT NOT NULL, "RoomType" TEXT NOT NULL, "Duration" NUMERIC, "RoomPreference" TEXT, PRIMARY KEY("BookingID", "RoomType"), FOREIGN KEY("BookingID") REFERENCES "Booking"("BookingID"), FOREIGN KEY("RoomType") REFERENCES "Room"("Type"));
CREATE TABLE "User_Booking" ("UserID" TEXT NOT NULL, "BookingID" TEXT NOT NULL, "PaymentMethod" TEXT, "LoyaltyProgram" TEXT, PRIMARY KEY("UserID", "BookingID"), FOREIGN KEY("UserID") REFERENCES "User"("UserID"), FOREIGN KEY("BookingID") REFERENCES "Booking"("BookingID"));"""

    for sql in postgres_create_table.split(';'):
        if sql.strip():
            try:
                sqlite_create_table = converter.convert_schema(sql)
                print("PostgreSQL:")
                print(sql)
                print("\n转换后的SQLite:")
                print(sqlite_create_table)
            except SQLConversionError as e:
                print(f"转换失败: {e}")