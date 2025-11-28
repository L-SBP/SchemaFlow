# backend/app/service/report_service.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession as Session

from crud import crud_report
from schema import report as schemas

async def get_report_list(db: Session, project_id: str) -> List[schemas.Report]:
    """
    业务逻辑：获取报表列表。
    """
    db_objs = await crud_report.get_by_project(db, project_id)
    return [schemas.Report.model_validate(obj) for obj in db_objs]