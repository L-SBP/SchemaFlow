# backend/app/schema/report.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict

# 图表配置
class ChartConfig(BaseModel):
    xAxisKey: str
    yAxisKey: str

# 创建报表
class ReportCreate(BaseModel):
    report_name: str
    query_id: int
    chart_type: str = "table"
    description: Optional[str] = None
    chartConfig: Optional[ChartConfig] = None   # ← 新增


# 单个报表响应
class Report(BaseModel):
    id: str
    projectId: str
    name: str
    type: str
    description: Optional[str]
    data: List[Dict[str, Any]]
    chartConfig: ChartConfig | None  # ← 必须加回
    sourceQueryText: Optional[str]
    updatedAt: str

# 历史查询
class HistoryQuery(BaseModel):
    id: str
    projectId: str
    queryText: str
    timestamp: str
    result: Optional[Any] = None

class UpdateChartType(BaseModel):
    chart_type: str
    model_config = ConfigDict(from_attributes=True)
