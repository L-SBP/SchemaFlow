from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict


class ChartConfig(BaseModel):
    xAxisKey: str
    yAxisKey: str


class ReportBase(BaseModel):
    projectId: str
    name: str
    type: str
    description: Optional[str] = None
    data: List[Dict[str, Any]]
    chartConfig: ChartConfig
    sourceQueryText: Optional[str] = None


class ReportCreate(ReportBase):
    sourceQueryId: Optional[str] = None


class Report(ReportBase):
    id: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# 👇 新增：补充缺失的 HistoryQuery 类
# ----------------------------------------------------
class HistoryQuery(BaseModel):
    id: str
    projectId: str
    queryText: str
    timestamp: str
    result: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)