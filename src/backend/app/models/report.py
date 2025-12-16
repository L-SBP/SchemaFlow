"""
报表模型。

本模块定义了用于存储分析报表配置的 ORM 模型。
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class AnalysisReport(Base):
    """
    报表配置表 ORM 模型。

    用于持久化保存用户对某个查询结果的展示配置。

    Attributes:
        report_id (int): 报表ID。
        project_id (int): 所属项目ID。
        result_id (int): 关联的数据源（查询结果）ID。
        name (str): 报表名称。
        description (str): 报表描述。
        chart_type (str): 图表类型 (bar, line, pie, etc.)。
        chart_config (dict): 图表配置。
        created_at (datetime): 创建时间。
        updated_at (datetime): 更新时间。
    """
    __tablename__ = "analysis_report"

    __table_args__ = (
        Index('idx_reports_project_id', 'project_id'),
        {'comment': '报表配置表，用于持久化保存用户对某个查询结果的展示配置'}
    )

    report_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment='报表ID'
    )
    project_id = Column(
        Integer,
        ForeignKey("project.project_id", ondelete="CASCADE"),
        nullable=False,
        comment='所属项目ID'
    )
    result_id = Column(
        Integer,
        ForeignKey("query_result.result_id", ondelete="CASCADE"),
        nullable=False,
        comment='关联的数据源（查询结果）ID'
    )
    
    name = Column(
        String(100),
        nullable=False,
        comment='报表名称'
    )
    description = Column(
        Text,
        nullable=True,
        comment='报表描述'
    )
    chart_type = Column(
        String(50),
        default="table",
        comment='图表类型 (bar, line, pie, etc.)'
    )
    chart_config = Column(
        JSON,
        nullable=True,
        comment='图表配置'
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment='更新时间'
    )

    # 关联关系
    # project = relationship("Project", back_populates="reports") # 需在Project model中添加对应关系
    # query_result = relationship("QueryResult") # 需在QueryResult model中添加对应关系