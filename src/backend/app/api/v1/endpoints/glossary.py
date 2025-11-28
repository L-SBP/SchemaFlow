# backend/app/api/v1/endpoints/glossary.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession as Session
from typing import Any

# 隐式绝对导入
from api.v1.deps import get_db, get_current_active_user
from schema import glossary as schemas
from service import glossary_service
from core.exceptions import ItemNotFoundException, DatabaseOperationFailedException

router = APIRouter()


# 5.1 获取术语列表
@router.get("/", response_model=schemas.GlossaryResponse)
async def read_glossary(
        projectId: str,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user),
) -> Any:
    """获取术语列表 (Glossary GET)"""
    try:
        # Router 严格只调用 Service
        terms = await glossary_service.get_all_terms(db, projectId)

        # Router 负责包装成 {code: 200, data: [...]}
        return {"code": 200, "message": "success", "data": terms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {e}")


# 5.2 创建术语 (其他 POST/PUT/DELETE 接口类似，调用相应的 Service 函数)
@router.post("/", response_model=schemas.GlossaryResponse)
async def create_term(
        term_in: schemas.GlossaryCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user),
) -> Any:
    """创建新术语 (Glossary POST)"""
    try:
        new_term = await glossary_service.create_term(db, term_in)
        return {"code": 200, "message": "success", "data": new_term}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Creation failed: {e}")