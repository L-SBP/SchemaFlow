from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class AnalysisReport(Base):
    """
    报表配置表：用于持久化保存用户对某个查询结果的展示配置
    """
    __tablename__ = "analysis_report"

    report_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False)
    # 关联的数据源（查询结果）
    result_id = Column(Integer, ForeignKey("query_result.result_id", ondelete="CASCADE"), nullable=False)
    
    # 用户自定义的配置
    name = Column(String(100), nullable=False) # 报表名称
    description = Column(Text, nullable=True)
    chart_type = Column(String(50), default="table") # bar, line, pie, etc.
    chart_config = Column(JSON, nullable=True) # 存储 {xAxisKey: "...", yAxisKey: "..."}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    # project = relationship("Project", back_populates="reports") # 需在Project model中添加对应关系
    # query_result = relationship("QueryResult") # 需在QueryResult model中添加对应关系