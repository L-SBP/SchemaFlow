# backend/app/service/glossary_service.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession as Session

# 隐式绝对导入
from crud.crud_glossary import crud_glossary
from schema import glossary as schemas
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException

# Service: 严格只调用 CRUD
async def get_all_terms(db: Session, project_id: str) -> List[schemas.GlossaryItem]:
    """
    业务逻辑：获取所有术语并转换 DTO
    """
    db_objs = await crud_glossary.get_by_project(db, project_id)
    return [schemas.GlossaryItem.model_validate(obj) for obj in db_objs]

async def create_term(db: Session, term_in: schemas.GlossaryCreate) -> schemas.GlossaryItem:
    """
    业务逻辑：创建新术语
    """
    # 业务逻辑：可以在这里添加权限、验证同义词等
    term_data = term_in.model_dump()
    db_obj = await crud_glossary.create(db, obj_in=term_data)
    return schemas.GlossaryItem.model_validate(db_obj)