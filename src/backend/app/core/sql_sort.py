import sqlglot
import sqlglot.expressions as exp
from collections import deque
from typing import List, Set, Dict, Tuple, Optional


def sort_ddl_by_dependency(ddl_text: str, dialect: str = "mysql") -> List[str]:
    """
    自动化排序 DDL 语句，支持 MySQL、PostgreSQL、SQLite
    适配 sqlglot 24.0.0 版本
    :param ddl_text: 原始 DDL 字符串
    :param dialect: 数据库方言，可选：mysql/postgresql/sqlite
    :return: 排序后的语句列表
    :raises ValueError: 当检测到循环依赖或重复创建实体时
    """
    if not ddl_text.strip():
        return []

    try:
        parsed = sqlglot.parse(ddl_text, read=dialect)
    except Exception as e:
        raise ValueError(f"SQL parsing failed with dialect '{dialect}': {str(e)}") from e

    statements_ast = [stmt for stmt in parsed if stmt is not None]
    if not statements_ast:
        return []

    # 辅助函数：获取外键引用的表名
    def get_foreign_key_ref_table(constraint: exp.ForeignKey) -> Optional[str]:
        reference = constraint.args.get("reference")
        if not (reference and isinstance(reference, exp.Reference)):
            return None

        table_expr = reference.args.get("this")
        if not (table_expr and isinstance(table_expr, exp.Table)):
            return None

        return table_expr.name

    # 收集每个语句的元数据
    statements_info = []
    for stmt_ast in statements_ast:
        info = {
            "ast": stmt_ast,
            "text": stmt_ast.sql(dialect=dialect, pretty=False),
            "created": set(),  # 本语句创建的实体名
            "depends": set(),  # 本语句依赖的外部实体名
        }

        # 处理 CREATE 语句
        if isinstance(stmt_ast, exp.Create):
            kind = stmt_ast.args.get("kind", "").upper()

            if kind == "TABLE":
                if isinstance(stmt_ast.this, exp.Table):
                    table_name = stmt_ast.this.name
                    info["created"].add(table_name)

                # 检查外键约束
                if isinstance(stmt_ast.expression, exp.Schema):
                    for constraint in stmt_ast.expression.constraints:
                        if isinstance(constraint, exp.ForeignKey):
                            ref_table = get_foreign_key_ref_table(constraint)
                            if ref_table:
                                info["depends"].add(ref_table)

            elif kind == "VIEW":
                if isinstance(stmt_ast.this, exp.Table):
                    view_name = stmt_ast.this.name
                    info["created"].add(view_name)

                # 提取视图依赖的表
                query = stmt_ast.expression
                if query:
                    for table_node in query.find_all(exp.Table):
                        info["depends"].add(table_node.name)

            elif kind == "INDEX":
                # 索引依赖所在表
                if isinstance(stmt_ast.this, exp.Table):
                    info["depends"].add(stmt_ast.this.name)

        # 处理 ALTER TABLE 语句
        elif isinstance(stmt_ast, exp.Alter) and stmt_ast.args.get("kind") == "TABLE":
            if isinstance(stmt_ast.this, exp.Table):
                table_name = stmt_ast.this.name
                info["depends"].add(table_name)

            # 检查添加外键的操作
            for action in stmt_ast.args.get("actions", []):
                if isinstance(action, exp.AddConstraint):
                    constraint = action.args.get("constraint")
                    if isinstance(constraint, exp.ForeignKey):
                        ref_table = get_foreign_key_ref_table(constraint)
                        if ref_table:
                            info["depends"].add(ref_table)

        statements_info.append(info)

    # 构建实体创建映射: 实体名 -> 语句索引
    created_entities: Dict[str, int] = {}
    for idx, info in enumerate(statements_info):
        for entity in info["created"]:
            if entity in created_entities:
                prev_idx = created_entities[entity]
                raise ValueError(
                    f"Entity '{entity}' is created by multiple statements "
                    f"(statement {prev_idx + 1} and {idx + 1})"
                )
            created_entities[entity] = idx

    # 构建依赖图
    n = len(statements_info)
    graph: List[List[int]] = [[] for _ in range(n)]
    indegree = [0] * n

    for idx, info in enumerate(statements_info):
        for dep_entity in info["depends"]:
            creator_idx = created_entities.get(dep_entity)
            if creator_idx is not None and creator_idx != idx:
                graph[creator_idx].append(idx)
                indegree[idx] += 1

    # 拓扑排序 (Kahn's algorithm)
    queue = deque([i for i in range(n) if indegree[i] == 0])
    queue = deque(sorted(queue))  # 保持原始顺序
    sorted_indices = []

    while queue:
        node = queue.popleft()
        sorted_indices.append(node)

        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

        # 保持队列顺序
        queue = deque(sorted(queue))

    # 检测循环依赖
    if len(sorted_indices) != n:
        raise ValueError("Circular dependency detected in DDL statements")

    # 生成排序后的 DDL 语句列表
    return [statements_info[i]["text"] for i in sorted_indices]