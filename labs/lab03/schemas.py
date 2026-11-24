from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class CategoryCreate(StrictBaseModel):
    name: str = Field(..., min_length=2, max_length=40, description="Назва категорії")

    @field_validator("name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        v_stripped = v.strip()
        if len(v_stripped) < 2:
            raise ValueError("Назва категорії не може бути порожньою")
        return v_stripped

class CategoryRead(BaseModel):
    id: int = Field(..., gt=0)
    name: str

class RecordCreate(StrictBaseModel):
    code: str = Field(..., min_length=3, max_length=40, description="Унікальний код")
    title: str = Field(..., min_length=3, max_length=120, description="Назва запису")
    category_id: int = Field(..., gt=0, description="ID категорії")
    value: float = Field(..., ge=0.0, le=10.0, description="Оцінка небезпеки (0..10)")
    status: Literal['new', 'in_progress', 'done'] = Field(..., description="Стан опрацювання")

    @field_validator("code", "title")
    @classmethod
    def validate_strip(cls, v: str) -> str:
        v_stripped = v.strip()
        if len(v_stripped) < 3:
            raise ValueError("Рядок не може бути порожнім після видалення пробілів")
        return v_stripped

class RecordReplace(RecordCreate):
    pass

class RecordRead(BaseModel):
    id: int = Field(..., gt=0)
    code: str
    title: str
    category_id: int = Field(..., gt=0)
    category_name: str
    value: float
    status: Literal['new', 'in_progress', 'done']