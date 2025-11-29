# backend/app/service/knowledge_service.py

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
from core.exceptions import ItemNotFoundException, ValidationException, DatabaseOperationFailedException


# ----------------------------------------------------------------------
# 3.4.1 创建术语
# ----------------------------------------------------------------------
async def create_knowledge_service(
        db: Session, project_id: int, user_id: int, data: schemas.KnowledgeCreate
) -> schemas.KnowledgeResponse:
    """创建新术语，需检查项目权限和术语唯一性"""
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
# 3.4.2 获取术语列表
# ----------------------------------------------------------------------
async def get_knowledge_list_service(
        db: Session, project_id: int, user_id: int, page: int, page_size: int, search: Optional[str]
) -> schemas.PaginatedKnowledgeList:
    """获取术语列表 (分页)"""
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
    解析 CSV 文件并批量导入。
    """
    # 1. 权限检查
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    # 2. 文件读取与解析 (仅演示 CSV)
    if not file.filename.endswith('.csv'):
        raise ValidationException("Only CSV files are supported currently.")

    content = await file.read()
    decoded_content = content.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_content)

    success_items = []
    failures = []
    row_index = 1  # 假设第一行是 header

    for row in reader:
        row_index += 1
        term = row.get('term', '').strip()
        definition = row.get('definition', '').strip()
        examples = row.get('examples', '').strip()

        # 2.1 校验数据
        if not term:
            failures.append(schemas.ImportFailure(row=row_index, error="术语名称不能为空"))
            continue

        # 2.2 检查重复 (数据库IO操作，批量时可能影响性能，这里简化处理)
        # 实际生产中建议先收集所有term，一次性查询数据库比对
        if await crud_knowledge.check_term_exists(db, project_id, term):
            failures.append(schemas.ImportFailure(row=row_index, error="该术语已存在"))
            continue

        success_items.append({
            "term": term,
            "definition": definition,
            "examples": examples
        })

    # 3. 批量写入数据库
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
    """生成导出文件链接 (模拟)"""
    # 1. 权限检查
    project = await crud_project.get(db, project_id)
    if not project or project.user_id != user_id:
        raise ItemNotFoundException("Project not found.")

    # 2. 获取所有数据
    all_terms = await crud_knowledge.get_all_by_project(db, project_id)

    # 3. 生成 CSV 文件内容 (实际应上传到 S3/OSS 并获取 presigned url)
    # 这里我们只模拟生成 URL

    filename = f"knowledge_proj_{project_id}_{int(datetime.now().timestamp())}.csv"
    # mock_upload_to_s3(filename, all_terms)

    download_url = f"https://cdn.example.com/exports/{filename}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    return schemas.ExportResponse(download_url=download_url, expires_at=expires_at)