"""
Knowledge services.

Manage domain knowledge terms per project, including CRUD, import/export, and
pagination. Performs permission checks, validation, and error handling.
"""
import os
import pandas as pd
from typing import List, Optional, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession as Session
from datetime import datetime, timedelta, timezone
import csv
import io

# 隐式绝对导入
from crud.crud_knowledge import crud_knowledge
from crud.crud_project import crud_project  # 用于检查项目权限
from schema import knowledge as schemas
from core.exceptions import ItemNotFoundException, ValidationException, DatabaseOperationFailedException, \
    OperationNotPermittedException
from core.config import config # 用于获取base_url
from schema.knowledge import KnowledgeCreate

# 导出目录（确保存在）
EXPORT_DIR = "static/exports"
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

# ----------------------------------------------------------------------
# 3.4.1 创建术语
# ----------------------------------------------------------------------
async def create_knowledge_service(
        db: Session, project_id: int, user_id: int, data: schemas.KnowledgeCreate
) -> schemas.KnowledgeResponse:
    """
    创建新术语，并检查权限与唯一性。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        data (schemas.KnowledgeCreate): 术语创建数据。

    Returns:
        schemas.KnowledgeResponse: 创建后的术语信息。

    Raises:
        ItemNotFoundException: 项目不存在或无权限。
        ValidationException: 术语已存在。
    """
    # 1. 检查项目权限
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found or access denied.")

    # 2. 检查术语是否已存在
    if await crud_knowledge.check_term_exists(db, project_id, data.term):
        raise ValidationException(f"Term '{data.term}' already exists in this project.")

    # 3. 创建
    new_term = await crud_knowledge.create(db, project_id=project_id, **data.model_dump())
    return schemas.KnowledgeResponse.model_validate(new_term)

# ----------------------------------------------------------------------
# [新增] 更新术语
# ----------------------------------------------------------------------
async def update_knowledge_service(
        db: Session,
        project_id: int,
        knowledge_id: int,
        user_id: int,
        update_data: schemas.KnowledgeUpdate  # 建议使用 Update 模型，而不是 Create
) -> schemas.KnowledgeResponse:
    """
    更新术语内容，验证项目归属与权限。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        knowledge_id (int): 术语 ID。
        user_id (int): 用户 ID。
        update_data (schemas.KnowledgeUpdate): 更新数据。

    Returns:
        schemas.KnowledgeResponse: 更新后的术语信息。

    Raises:
        ItemNotFoundException: 术语不存在或不属于该项目。
        OperationNotPermittedException: 无权限。
    """
    # 1. 查数据
    db_obj = await crud_knowledge.get(db, knowledge_id)
    if not db_obj:
        raise ItemNotFoundException(f"Term {knowledge_id} not found.")

    # 2. 安全校验：确保 URL 里的 project_id 和数据库里记录的一致
    # 防止用户在 URL A 项目下，却试图修改 B 项目的术语
    if db_obj.project_id != project_id:
        raise ItemNotFoundException("Term does not belong to this project.")

    # 3. 查权限 (检查用户是否拥有该项目)
    project = await crud_project.get(db, project_id=project_id)
    if not project or project.user_id != user_id:
        raise OperationNotPermittedException("Access denied.")

    # 4. 更新
    updated_obj = await crud_knowledge.update(db, db_obj, update_data.model_dump(exclude_unset=True))
    return schemas.KnowledgeResponse.model_validate(updated_obj)


# ----------------------------------------------------------------------
# [新增] 批量删除
# ----------------------------------------------------------------------
async def batch_delete_knowledge_service(
        db: Session, project_id: int, user_id: int, knowledge_ids: List[int]
) -> int:
    """
    批量删除术语。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        knowledge_ids (List[int]): 待删除术语 ID 列表。

    Returns:
        int: 删除成功的数量。

    Raises:
        OperationNotPermittedException: 无权限。
    """
    # 1. 权限检查
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise OperationNotPermittedException("Access denied.")

    count = await crud_knowledge.remove_multi(db, project_id, knowledge_ids)
    return count



# ----------------------------------------------------------------------
# 3.4.2 获取术语列表
# ----------------------------------------------------------------------
async def get_knowledge_list_service(
        db: Session, project_id: int, user_id: int, page: int, page_size: int, search: Optional[str]
) -> schemas.PaginatedKnowledgeList:
    """
    获取术语列表（分页）。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        page (int): 页码。
        page_size (int): 每页数量。
        search (Optional[str]): 搜索关键字。

    Returns:
        schemas.PaginatedKnowledgeList: 分页结果。

    Raises:
        ItemNotFoundException: 项目不存在。
    """
    # 1. 检查项目权限
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    skip = (page - 1) * page_size
    total = await crud_knowledge.get_total_count(db, project_id, search)
    items = await crud_knowledge.get_by_project(db, project_id, skip, page_size, search)

    return schemas.PaginatedKnowledgeList(
        total=total, page=page, page_size=page_size, items=items
    )


# ----------------------------------------------------------------------
# 3.4.3 批量导入术语
# ----------------------------------------------------------------------
async def import_knowledge_service(
        db: Session, project_id: int, user_id: int, file: UploadFile
) -> schemas.ImportResponse:
    """
    解析 Excel/CSV 文件并批量导入术语。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。
        file (UploadFile): 上传文件。

    Returns:
        schemas.ImportResponse: 导入结果统计。

    Raises:
        ItemNotFoundException: 项目不存在。
        ValidationException: 文件类型或内容解析失败。
    """
    # 1. 权限检查
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    # 2. 文件读取与解析 ---- 改为支持excel和csv
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise ValidationException("Only .xlsx, .xls, .csv files are supported.")

    # 2. 读取文件
    content = await file.read()
    try:
        if file.filename.endswith('.csv'):
            # [修复] 增加编码自动回退机制
            try:
                # 1. 优先尝试标准 UTF-8
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    # 2. 失败则尝试 GB18030 (包含 GBK 和 GB2312 的超集，兼容性最好)
                    df = pd.read_csv(io.BytesIO(content), encoding='gb18030')
                except UnicodeDecodeError:
                    # 3. 还是不行，尝试 Windows-1252 (西欧常见)
                    df = pd.read_csv(io.BytesIO(content), encoding='cp1252')

        else:
            # Excel 文件是二进制格式，不需要指定 encoding
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise ValidationException(f"Failed to parse file: {str(e)}")

    # 3. 校验表头 (假设模板列名为 term, definition, examples)
    # 支持中文列名，如 "术语", "定义", "示例"
    required_cols = ['term', 'definition']
    # 简单的列名映射，兼容中文
    rename_map = {'术语': 'term', '定义': 'definition', '示例': 'examples', '备注': 'examples'}
    df.rename(columns=rename_map, inplace=True)

    if not all(col in df.columns for col in required_cols):
        raise ValidationException(f"Missing required columns: {required_cols}")

    # 4. 遍历处理
    success_items = []
    failures = []

    # 获取现有术语用于去重
    existing_items = await crud_knowledge.get_all_by_project(db, project_id)
    existing_terms = {item.term for item in existing_items}

    for index, row in df.iterrows():
        row_num = index + 2  # Excel 行号从 1 开始，表头占 1 行
        term = str(row.get('term', '')).strip()
        definition = str(row.get('definition', '')).strip()
        examples = str(row.get('examples', ''))
        if pd.isna(examples): examples = ""

        if not term or not definition:
            failures.append(schemas.ImportFailure(row=row_num, error="Term or Definition is empty"))
            continue

        if term in existing_terms:
            failures.append(schemas.ImportFailure(row=row_num, error="Term already exists"))
            continue

        success_items.append({
            "term": term,
            "definition": definition,
            "examples": examples
        })
        existing_terms.add(term)  # 防止文件内重复

    # 5. 批量写入
    imported_count = 0
    if success_items:
        imported_count = await crud_knowledge.batch_create(db, project_id, success_items)

    return schemas.ImportResponse(
        imported_count=imported_count,
        failed_count=len(failures),
        failures=failures
    )

# ----------------------------------------------------------------------
# 3.4.4 导出术语
# ----------------------------------------------------------------------
async def export_knowledge_service(
        db: Session, project_id: int, user_id: int
) -> schemas.ExportResponse:
    """
    导出术语为 Excel 文件并返回下载 URL。

    Args:
        db (Session): 数据库会话。
        project_id (int): 项目 ID。
        user_id (int): 用户 ID。

    Returns:
        schemas.ExportResponse: 包含下载链接与过期时间。

    Raises:
        ItemNotFoundException: 项目不存在。
    """
    # 1. 权限检查
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    # 2. 获取数据
    all_terms = await crud_knowledge.get_all_by_project(db, project_id)

    # 3. 转 DataFrame 并写入 Excel
    data = []
    for term in all_terms:
        data.append({
            "术语": term.term,
            "定义": term.definition,
            "示例": term.examples,
            "创建时间": term.created_at.strftime("%Y-%m-%d")
        })

    df = pd.DataFrame(data)
    filename = f"knowledge_proj_{project_id}_{int(datetime.now().timestamp())}.xlsx"
    filepath = os.path.join(EXPORT_DIR, filename)
    df.to_excel(filepath, index=False)

    # 4. 生成 URL
    # 这里假设您有 config.app.base_url，或者您可以硬编码本地测试地址
    # 确保在 main.py 中 mount 了 static 目录
    base_url = getattr(config.app, "base_url", "http://localhost:8000")
    download_url = f"{base_url}/static/exports/{filename}"

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # 文件保留24小时

    return schemas.ExportResponse(download_url=download_url, expires_at=expires_at)
