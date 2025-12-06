# backend/app/schema/report.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# 图表配置
class ChartConfig(BaseModel):
    xAxisKey: str
    yAxisKey: str

# 1. 创建报表请求
class ReportCreate(BaseModel):
    report_name: str
    query_id: int          # 关联的 result_id
    chart_type: str = "table"
    description: Optional[str] = None
    chartConfig: Optional[ChartConfig] = None

# 2. 修改报表请求 (新增)
class ReportUpdate(BaseModel):
    report_name: Optional[str] = None
    chart_type: Optional[str] = None
    description: Optional[str] = None
    chartConfig: Optional[ChartConfig] = None

# 3. 报表响应 (调整为从 AnalysisReport 获取元数据，从 QueryResult 获取 Data)
class Report(BaseModel):
    id: str             # report_id
    projectId: str
    name: str           # 用户自定义的名称
    type: str           # 用户保存的 chart_type
    description: Optional[str]
    
    # 以下数据来自关联的 QueryResult
    data: List[Dict[str, Any]] 
    sourceQueryText: Optional[str]
    
    chartConfig: Optional[ChartConfig]
    updatedAt: str
    
    model_config = ConfigDict(from_attributes=True)

# 4. 历史查询 (保持不变)
class HistoryQuery(BaseModel):
    id: str
    projectId: str
    queryText: str
    timestamp: str
    result: Optional[Any] = None