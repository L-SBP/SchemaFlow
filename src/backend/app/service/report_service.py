"""
报表服务。

基于缓存查询结果与 AI 语句提供报表的创建、读取、更新、删除与导出；并提供
历史查询数据以构建图表。
"""

# backend/app/service/report_service.py

from typing import List, Any, Dict, Optional
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy import select
from fastapi import HTTPException

from schema import report as schemas
# 导入核心模型
from models.report import AnalysisReport
from models.query_result import QueryResult
from models.ai_generated_statement import AIGeneratedStatement
from models.project import Project
# 注意：Message 和 Session 我们将在函数内部导入，或者你可以尝试在这里导入
# 如果报错循环依赖，请保持函数内导入


def _looks_like_iso_date(value: str) -> bool:
    # 支持 YYYY-MM-DD 或 YYYY-MM-DDThh:mm:ss(含可选时区)
    if not isinstance(value, str):
        return False
    if not re.match(r"^\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?$", value):
        return False
    try:
        # 兼容 'Z'
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except Exception:
        return False


def _infer_field_type(values: List[Any]) -> str:
    non_null = [v for v in values if v is not None]
    if not non_null:
        return 'string'

    # object 优先级最高
    if any(isinstance(v, (dict, list)) for v in non_null):
        return 'object'
    if any(isinstance(v, bool) for v in non_null):
        return 'bool'
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
        return 'number'
    if all(isinstance(v, str) for v in non_null) and all(_looks_like_iso_date(v) for v in non_null):
        return 'date'
    # 混合或不确定：保守降级为 string
    return 'string'


def _extract_columns(data: List[Dict[str, Any]]) -> List[str]:
    if not data:
        return []
    # 尽量保持首行字段顺序
    first = data[0]
    cols = list(first.keys())
    # 补齐后续行新增字段
    for row in data[1:]:
        for k in row.keys():
            if k not in cols:
                cols.append(k)
    return cols


def _infer_fields(
    data: List[Dict[str, Any]],
    columns: List[str],
    sample_size: int = 50,
) -> List[schemas.HistoryQueryField]:
    sample = data[:sample_size]
    fields: List[schemas.HistoryQueryField] = []
    for col in columns:
        col_values = [r.get(col) for r in sample if isinstance(r, dict)]
        fields.append(schemas.HistoryQueryField(name=col, type=_infer_field_type(col_values)))
    return fields


def _reportability_from_fields(
    columns: List[str],
    fields: List[schemas.HistoryQueryField],
) -> tuple[bool, Optional[str]]:
    if len(columns) < 2:
        return False, '该查询结果只有一列，无法生成报表。'

    has_number = any(f.type == 'number' for f in fields)
    if not has_number:
        return False, '该查询结果缺少数值字段，无法作为 Y 轴绘图。'

    has_dimension = any(f.type in ('string', 'date') for f in fields)
    if not has_dimension:
        return False, '该查询结果缺少维度字段（文本/日期），无法作为 X 轴绘图。'

    return True, None
async def _verify_project_ownership(
    db: Session,
    project_id: int,
    user_id: int,
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="权限拒绝")

    return project

async def _verify_report_ownership(
    db: Session,
    report_id: int,
    user_id: int,
) -> AnalysisReport:
    report = await db.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报表未找到")

    project = await db.get(Project, report.project_id)
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="权限被拒绝")

    return report

# --------------------------
# 报表列表
# --------------------------


async def get_report_list(
    db: Session,
    project_id: int,
    user_id: int,
)-> List[schemas.Report]:
    await _verify_project_ownership(db, project_id, user_id)
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
        raise HTTPException(status_code=404, detail=f"ID 为 {project_id} 的项目未找到")

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
            if config_dict.get('x_axis_key') and config_dict.get('y_axis_key'):
                c_config = schemas.ChartConfig(**config_dict)

        reports.append(schemas.Report(
            id=str(report_obj.report_id),
            project_id=str(project_id),
            name=report_obj.name,
            type=report_obj.chart_type,
            description=report_obj.description,
            data=result_obj.result_data if isinstance(result_obj.result_data, list) else [],
            chart_config=c_config,
            source_query_id=str(report_obj.result_id),
            source_query_text=stmt_obj.sql_text,
            updated_at=report_obj.updated_at.isoformat() if report_obj.updated_at else report_obj.created_at.isoformat()
        ))

    return reports


# --------------------------
# 历史查询记录
# --------------------------
async def get_history_queries_service(
    db: Session,
    project_id: int,
    user_id: int,
) -> List[schemas.HistoryQuery]:
    await _verify_project_ownership(db, project_id, user_id)

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
        raise HTTPException(status_code=404, detail=f"ID 为 {project_id} 的项目未找到")

    # [修复问题2]：局部导入以避免 UnboundLocalError 和循环依赖
    from models.message import Message
    from models.session import Session as SessionModel

    # 构造查询：Query Result -> Statement -> Message(assistant) -> Session
    # 说明：AIGeneratedStatement.message_id 绑定的是 assistant 消息。
    # 为了展示“用户的提问”，我们会再回查同会话中该 assistant 消息之前最近的一条 user 消息。
    stmt = (
        select(QueryResult, Message)
        .join(AIGeneratedStatement, QueryResult.statement_id == AIGeneratedStatement.statement_id)
        .join(Message, AIGeneratedStatement.message_id == Message.message_id)
        .join(SessionModel, Message.session_id == SessionModel.session_id)
        .where(SessionModel.project_id == project_id)
        .where(Message.message_type == 'assistant')
        .order_by(QueryResult.cached_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    history: List[schemas.HistoryQuery] = []
    for query_res, msg_obj in rows:
        data = query_res.result_data if isinstance(query_res.result_data, list) else []
        # 确保是 [{...}] 的结构，否则前端无法选轴
        normalized: List[Dict[str, Any]] = [r for r in data if isinstance(r, dict)]
        columns = _extract_columns(normalized)
        fields = _infer_fields(normalized, columns)
        reportable, reason = _reportability_from_fields(columns, fields)

        # 回查用户提问：同 session 内，assistant 消息之前最近的一条 user 消息
        query_text = msg_obj.content
        try:
            stmt_user = (
                select(Message)
                .where(Message.session_id == msg_obj.session_id)
                .where(Message.message_type == 'user')
                .where(Message.created_at <= msg_obj.created_at)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_res = await db.execute(stmt_user)
            user_msg = user_res.scalar_one_or_none()
            if user_msg and user_msg.content:
                query_text = user_msg.content
        except Exception:
            # 兜底：保持 assistant 内容（不影响 rows 返回）
            pass

        history.append(schemas.HistoryQuery(
            id=str(query_res.result_id),
            project_id=str(project_id),
            query_text=query_text,
            timestamp=query_res.cached_at.isoformat() if query_res.cached_at else 'N/A',
            result=schemas.HistoryQueryResult(columns=columns, fields=fields, data=normalized),
            reportable=reportable,
            unreportable_reason=reason,
        ))

    return history


# --------------------------
# 创建报表
# --------------------------
async def create_report_service(
    db: Session,
    project_id: int,
    user_id: int,
    payload: schemas.ReportCreate,
) -> schemas.Report:
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
    project = await _verify_project_ownership(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")
    
    # 2. 校验数据源 (Query Result) 是否存在
    result_exists = await db.get(QueryResult, payload.query_id)
    if not result_exists:
        raise HTTPException(status_code=404, detail="查询结果（数据源）未找到")

    data = result_exists.result_data if isinstance(result_exists.result_data, list) else []
    normalized = [r for r in data if isinstance(r, dict)]
    columns = _extract_columns(normalized)
    fields = _infer_fields(normalized, columns)
    reportable, reason = _reportability_from_fields(columns, fields)
    if not reportable:
        raise HTTPException(status_code=400, detail=reason or '该查询结果不适合生成报表。')

    # 3. 创建 AnalysisReport 对象
    new_report = AnalysisReport(
        project_id=project_id,
        result_id=payload.query_id,
        name=payload.report_name,
        chart_type=payload.chart_type,
        description=payload.description,
        chart_config=payload.chart_config.model_dump() if payload.chart_config else None
    )

    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    # 4. 获取关联 SQL 文本用于返回
    stmt_obj = await db.get(AIGeneratedStatement, result_exists.statement_id)

    return schemas.Report(
        id=str(new_report.report_id),
        project_id=str(project_id),
        name=new_report.name,
        type=new_report.chart_type,
        description=new_report.description,
        data=normalized,
        chart_config=payload.chart_config,
        source_query_id=str(new_report.result_id),
        source_query_text=stmt_obj.sql_text if stmt_obj else "",
        updated_at=new_report.created_at.isoformat()
    )


# --------------------------
# 删除报表
# --------------------------
async def delete_report_service(db: Session, report_id: int, user_id: int) -> bool:
    """
    删除指定报表。

    Args:
        db (Session): 数据库会话。
        report_id (int): 报表 ID。

    Returns:
        bool: 是否删除成功。
    """
    report = await _verify_report_ownership(db, report_id, user_id)

    await db.delete(report)
    await db.commit()
    return True


# --------------------------
# 更新报表
# --------------------------
async def update_report_service(
    db: Session,
    report_id: int,
    user_id: int,
    payload: schemas.ReportUpdate,
) -> schemas.Report:
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
    report_obj = await _verify_report_ownership(db, report_id, user_id)

    if not report_obj:
        raise HTTPException(status_code=404, detail="报表未找到")

    # 2. 更新字段
    if payload.report_name is not None:
        report_obj.name = payload.report_name
    if payload.chart_type is not None:
        report_obj.chart_type = payload.chart_type
    if payload.description is not None:
        report_obj.description = payload.description
    if payload.chart_config is not None:
        report_obj.chart_config = payload.chart_config.model_dump()

    await db.commit()
    await db.refresh(report_obj)

    # 3. 组装返回数据
    result_obj = await db.get(QueryResult, report_obj.result_id)
    stmt_obj = await db.get(AIGeneratedStatement, result_obj.statement_id)

    c_config = None
    if report_obj.chart_config:
        config_dict = report_obj.chart_config if isinstance(report_obj.chart_config, dict) else {}
        if config_dict.get('x_axis_key') and config_dict.get('y_axis_key'):
            c_config = schemas.ChartConfig(**config_dict)

    data = result_obj.result_data if isinstance(result_obj.result_data, list) else []
    normalized = [r for r in data if isinstance(r, dict)]

    return schemas.Report(
        id=str(report_obj.report_id),
        project_id=str(report_obj.project_id),
        name=report_obj.name,
        type=report_obj.chart_type,
        description=report_obj.description,
        data=normalized,
        chart_config=c_config,
        source_query_id=str(report_obj.result_id),
        source_query_text=stmt_obj.sql_text,
        updated_at=report_obj.updated_at.isoformat() if report_obj.updated_at else ""
    )


# --------------------------
# 导出报表
# --------------------------
async def export_report_service(
    db: Session,
    report_id: int,
    format: str,
    user_id: int,
) -> dict:
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
    # 权限检查（避免路由传参不匹配导致运行时错误）
    await _verify_report_ownership(db, report_id, user_id)

    return {
        "download_url": f"https://fake-cdn.example.com/reports/{report_id}.{format}",
        "expires_at": "2025-12-01T15:00:00Z"
    }
