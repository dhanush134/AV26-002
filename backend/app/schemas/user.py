from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    age: int = Field(ge=1, le=120)
    gender: str | None = Field(default=None, max_length=50)
    height_cm: float = Field(ge=50, le=250)
    weight_kg: float = Field(ge=10, le=300)
    target_age: int | None = Field(default=None, ge=1, le=120)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = Field(default=None, max_length=50)
    height_cm: float | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=10, le=300)
    target_age: int | None = Field(default=None, ge=1, le=120)


class UserResponse(UserBase, ORMModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
