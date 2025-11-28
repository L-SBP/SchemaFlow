from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Union, Any

# 基础数据传输对象 (DTO)
class GlossaryBase(BaseModel):
    projectId: str
    term: str
    definition: str
    synonyms: List[str] = []
    relatedTable: Optional[str] = None

class GlossaryCreate(GlossaryBase):
    pass

class GlossaryUpdate(BaseModel):
    # 允许部分更新
    term: Optional[str] = None
    definition: Optional[str] = None
    synonyms: Optional[List[str]] = None
    relatedTable: Optional[str] = None

class GlossaryItem(GlossaryBase):
    id: int
    updatedAt: str

    model_config = ConfigDict(from_attributes=True)

# 核心包装器 (满足前端要求)
class GlossaryResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Union[List[GlossaryItem], GlossaryItem]] = None