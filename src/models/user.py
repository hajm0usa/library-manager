from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, BeforeValidator, Field


class Role(Enum):
    ADMIN = "ADMIN"
    LIBRARIAN = "LIBRARIAN"
    MEMBER = "MEMBER"


class UserBase(BaseModel):
    username: str
    role: Role = Role.MEMBER
    full_name: Optional[str] = None

    class Config:
        use_enum_values = True


class UserResponse(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime


def password_validator(value: Any) -> Any:
    if len(value) < 8:
        raise ValueError("Password is short. it sould be at least 8 characters")
    if not any(char.isdigit() for char in value):
        raise ValueError("Password should be a combination of digits and characters")
    return value


class UserCreate(UserBase):
    password: Annotated[str, BeforeValidator(password_validator)]


class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

    class Config:
        use_enum_values = True
