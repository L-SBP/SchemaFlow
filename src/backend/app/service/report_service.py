"""
Report services.

Create, read, update, delete, and export analytical reports backed by cached
query results and AI-generated statements. Provides history retrieval utilities
for building charts.
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy import select, delete, update
from fastapi import HTTPException

from schema import report as schemas
# 导入核心模型
from models.report import AnalysisReport
from models.query_result import QueryResult
from models.ai_generated_statement import AIGeneratedStatement
from models.project import Project
# 注意：Message 和 Session 我们将在函数内部导入，或者你可以尝试在这里导入
# 如果报错循环依赖，请保持函数内导入

# --------------------------
# 1. 获取报表列表 (Read)
# --------------------------
async def get_report_list(db: Session, project_id: int) -> List[schemas.Report]:
    """
    获取项目的报表列表并关联数据源与语句。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。

    Returns:
        List[schemas.Report]: 报表列表。

    Raises:
        HTTPException: 项目不存在时返回 404。
    """
    # [修复问题1]：先检查项目是否存在
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    stmt = (
        select(AnalysisReport, QueryResult, AIGeneratedStatement)
        .join(QueryResult, AnalysisReport.result_id == QueryResult.result_id)
        .join(AIGeneratedStatement, QueryResult.statement_id == AIGeneratedStatement.statement_id)
        .where(AnalysisReport.project_id == project_id)
        .order_by(AnalysisReport.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    reports = []
    for report_obj, result_obj, stmt_obj in rows:
        # 处理 chart_config (从数据库JSON转为Pydantic对象)
        c_config = None
        if report_obj.chart_config:
            # 兼容处理：确保 chart_config 是字典
            config_dict = report_obj.chart_config if isinstance(report_obj.chart_config, dict) else {}
            # 只有当字典不为空且包含必要的键时才转换
            if config_dict.get('xAxisKey') and config_dict.get('yAxisKey'):
                c_config = schemas.ChartConfig(**config_dict)

        reports.append(schemas.Report(
            id=str(report_obj.report_id),
            projectId=str(project_id),
            name=report_obj.name,
            type=report_obj.chart_type,
            description=report_obj.description,
            data=result_obj.result_data if isinstance(result_obj.result_data, list) else [],
            chartConfig=c_config,
            sourceQueryText=stmt_obj.sql_text,
            updatedAt=report_obj.updated_at.isoformat() if report_obj.updated_at else report_obj.created_at.isoformat()
        ))

    return reports


# --------------------------
# 2. 获取历史查询记录 (Source for creating reports)
# --------------------------
async def get_history_queries_service(db: Session, project_id: int) -> List[schemas.HistoryQuery]:
    """
    获取项目历史查询记录，返回用户原始提问与结果。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。

    Returns:
        List[schemas.HistoryQuery]: 历史查询记录列表。

    Raises:
        HTTPException: 项目不存在时返回 404。
    """
    # [修复问题1]：先检查项目是否存在
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    # [修复问题2]：局部导入以避免 UnboundLocalError 和循环依赖
    from models.message import Message
    from models.session import Session as SessionModel

    # 构造查询：Query Result -> Statement -> Message -> Session
    # 我们需要 Message.content (用户问题) 和 QueryResult (数据)
    stmt = (
        select(QueryResult, Message)
        .join(AIGeneratedStatement, QueryResult.statement_id == AIGeneratedStatement.statement_id)
        .join(Message, AIGeneratedStatement.message_id == Message.message_id)
        .join(SessionModel, Message.session_id == SessionModel.session_id)
        .where(SessionModel.project_id == project_id)
        .where(Message.message_type == 'assistant') # 确保我们取的是用户发的消息（提问）
        .order_by(QueryResult.cached_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    history = []
    for query_res, msg_obj in rows:
        history.append(schemas.HistoryQuery(
            id=str(query_res.result_id),
            projectId=str(project_id),
            # 这里取的是 message.content，即用户的原始提问
            queryText=msg_obj.content, 
            timestamp=query_res.cached_at.isoformat() if query_res.cached_at else 'N/A',
            result=query_res.result_data
        ))

    return history


# --------------------------
# 3. 创建报表 (Create - 真正入库)
# --------------------------
async def create_report_service(db: Session, project_id: int, payload: schemas.ReportCreate):
    """
    创建报表记录并返回标准响应。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        payload (schemas.ReportCreate): 报表创建参数。

    Returns:
        schemas.Report: 创建后的报表。

    Raises:
        HTTPException: 项目或数据源不存在。
    """
    # 1. 校验项目
    project_exists = await db.get(Project, project_id)
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 2. 校验数据源 (Query Result) 是否存在
    result_exists = await db.get(QueryResult, payload.query_id)
    if not result_exists:
        raise HTTPException(status_code=404, detail="Query result (Data Source) not found")

    # 3. 创建 AnalysisReport 对象
    new_report = AnalysisReport(
        project_id=project_id,
        result_id=payload.query_id,
        name=payload.report_name,
        chart_type=payload.chart_type,
        description=payload.description,
        chart_config=payload.chartConfig.model_dump() if payload.chartConfig else None
    )

    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    # 4. 获取关联 SQL 文本用于返回
    stmt_obj = await db.get(AIGeneratedStatement, result_exists.statement_id)

    return schemas.Report(
        id=str(new_report.report_id),
        projectId=str(project_id),
        name=new_report.name,
        type=new_report.chart_type,
        description=new_report.description,
        data=result_exists.result_data,
        chartConfig=payload.chartConfig,
        sourceQueryText=stmt_obj.sql_text if stmt_obj else "",
        updatedAt=new_report.created_at.isoformat()
    )


# --------------------------
# 4. 删除报表 (Delete)
# --------------------------
async def delete_report_service(db: Session, report_id: int) -> bool:
    """
    删除指定报表。

    Args:
        db (Session): 数据库会话。
        report_id (int): 报表 ID。

    Returns:
        bool: 是否删除成功。
    """
    stmt = delete(AnalysisReport).where(AnalysisReport.report_id == report_id)
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        return False
    return True


# --------------------------
# 5. 修改报表 (Update)
# --------------------------
async def update_report_service(db: Session, report_id: int, payload: schemas.ReportUpdate):
    """
    更新报表基础属性与图表配置。

    Args:
        db (Session): 数据库会话。
        report_id (int): 报表 ID。
        payload (schemas.ReportUpdate): 更新参数。

    Returns:
        schemas.Report: 更新后的报表。

    Raises:
        HTTPException: 报表不存在。
    """
    # 1. 检查是否存在
    report_obj = await db.get(AnalysisReport, report_id)
    if not report_obj:
        raise HTTPException(status_code=404, detail="Report not found")

    # 2. 更新字段
    if payload.report_name is not None:
        report_obj.name = payload.report_name
    if payload.chart_type is not None:
        report_obj.chart_type = payload.chart_type
    if payload.description is not None:
        report_obj.description = payload.description
    if payload.chartConfig is not None:
        report_obj.chart_config = payload.chartConfig.model_dump()

    await db.commit()
    await db.refresh(report_obj)

    # 3. 组装返回数据
    result_obj = await db.get(QueryResult, report_obj.result_id)
    stmt_obj = await db.get(AIGeneratedStatement, result_obj.statement_id)

    c_config = None
    if report_obj.chart_config:
        config_dict = report_obj.chart_config if isinstance(report_obj.chart_config, dict) else {}
        if config_dict.get('xAxisKey') and config_dict.get('yAxisKey'):
            c_config = schemas.ChartConfig(**config_dict)

    return schemas.Report(
        id=str(report_obj.report_id),
        projectId=str(report_obj.project_id),
        name=report_obj.name,
        type=report_obj.chart_type,
        description=report_obj.description,
        data=result_obj.result_data,
        chartConfig=c_config,
        sourceQueryText=stmt_obj.sql_text,
        updatedAt=report_obj.updated_at.isoformat() if report_obj.updated_at else ""
    )


# --------------------------
# 6. 导出报表 (Export)
# --------------------------
async def export_report_service(db: Session, report_id: int, format: str):
    """
    导出报表，返回下载链接与过期时间。

    Args:
        db (Session): 数据库会话。
        report_id (int): 报表 ID。
        format (str): 导出格式，如 `png` 或 `csv`。

    Returns:
        dict: 包含 `download_url` 和 `expires_at` 的字典。

    Raises:
        HTTPException: 报表不存在。
    """
    # 检查 report 是否存在
    report_obj = await db.get(AnalysisReport, report_id)
    if not report_obj:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "download_url": f"https://fake-cdn.example.com/reports/{report_id}.{format}",
        "expires_at": "2025-12-01T15:00:00Z"
    }
