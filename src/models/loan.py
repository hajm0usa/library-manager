from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LoanStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    RETURNED = "RETURNED"
    RENEW_PENDING = "RENEW_PENDING"


class LoanBase(BaseModel):
    username: str
    book_title: str
    status: LoanStatus = LoanStatus.PENDING

    class Config:
        use_enum_values = True


class LoanResponse(LoanBase):
    id: str = Field(alias="_id")
    date: datetime
    return_date: datetime


class LoanCreate(LoanBase):
    pass


class LoanUpdate(BaseModel):
    username: Optional[str] = None
    book_title: Optional[str] = None
    date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    status: Optional[LoanStatus] = LoanStatus.PENDING

    class Config:
        use_enum_values = True
