from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base

class Report(Base):
    __tablename__ = "report"

    report_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.project_id"), nullable=False)

    report_name = Column(String(255), nullable=False)
    query_id = Column(Integer, ForeignKey("query_history.query_id"), nullable=False)
    chart_type = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
