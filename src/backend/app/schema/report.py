"""
报表配置 Schema。

本模块定义了分析报表的保存、更新和展示配置模型。
"""

# backend/app/schema/report.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# 图表配置
class ChartConfig(BaseModel):
    """
    图表配置 Schema。

    Attributes:
        xAxisKey (str): X轴对应的键名。
        yAxisKey (str): Y轴对应的键名。
    """
    xAxisKey: str
    yAxisKey: str

# 1. 创建报表请求
class ReportCreate(BaseModel):
    """
    创建报表请求 Schema。

    Attributes:
        report_name (str): 报表名称。
        query_id (int): 关联的查询结果 ID。
        chart_type (str): 图表类型 (默认 "table")。
        description (Optional[str]): 报表描述。
        chartConfig (Optional[ChartConfig]): 图表配置。
    """
    report_name: str
    query_id: int          # 关联的 result_id
    chart_type: str = "table"
    description: Optional[str] = None
    chartConfig: Optional[ChartConfig] = None

# 2. 修改报表请求 
class ReportUpdate(BaseModel):
    """
    更新报表请求 Schema。

    Attributes:
        report_name (Optional[str]): 报表名称。
        chart_type (Optional[str]): 图表类型。
        description (Optional[str]): 报表描述。
        chartConfig (Optional[ChartConfig]): 图表配置。
    """
    report_name: Optional[str] = None
    chart_type: Optional[str] = None
    description: Optional[str] = None
    chartConfig: Optional[ChartConfig] = None

# 3. 报表响应 (调整为从 AnalysisReport 获取元数据，从 QueryResult 获取 Data)
class Report(BaseModel):
    """
    报表响应 Schema。

    Attributes:
        id (str): 报表 ID。
        projectId (str): 项目 ID。
        name (str): 报表名称。
        type (str): 图表类型。
        description (Optional[str]): 报表描述。
        data (List[Dict[str, Any]]): 报表数据 (来自 QueryResult)。
        sourceQueryText (Optional[str]): 来源 SQL 语句。
        chartConfig (Optional[ChartConfig]): 图表配置。
        updatedAt (str): 更新时间。
    """
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
    """
    历史查询记录 Schema。

    Attributes:
        id (str): 记录 ID。
        projectId (str): 项目 ID。
        queryText (str): 查询文本。
        timestamp (str): 时间戳。
        result (Optional[Any]): 查询结果。
    """
    id: str
    projectId: str
    queryText: str
    timestamp: str
    result: Optional[Any] = None