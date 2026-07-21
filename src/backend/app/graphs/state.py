from typing import Optional, Annotated, TypedDict

from operator import add


class ProjectState(TypedDict, total= False):
    """
    langgraph 全局状态
    """
    # 输入参数
    project_id: int     # 项目ID
    db_type: str        # 数据库类型
    db_name: str        # 数据库名称
    requirements: str   # 用户描述的需求
    ai_model: str       # AI模型

    # 各阶段的产出
    schema_text: Optional[str]
    er_diagram_code: Optional[str]
    ddl_statements: Optional[str]

    # 流程控制
    current_stage: Optional[str]    # 当前阶段
    error_message: Optional[str]    # 错误信息
    regenerate_er: bool             # 是否重新生成ER图

    # 时间戳
    started_at: Optional[str]
    completed_at: Optional[str]

    # 累计信息
    node_history: Annotated[list[str], add]