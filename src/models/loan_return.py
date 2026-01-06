from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LibrarianStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"


class LoanReturnBase(BaseModel):
    loan_id: str

    class Config:
        use_enum_values = True


class LoanReturnResponse(LoanReturnBase):
    id: str = Field(alias="_id")
    status: LibrarianStatus = LibrarianStatus.PENDING
    date: datetime


class LoanReturnCreate(LoanReturnBase):
    pass


class LoanReturnUpdate(LoanReturnBase):
    status: LibrarianStatus = LibrarianStatus.PENDING
