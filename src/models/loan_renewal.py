from datetime import datetime

from pydantic import BaseModel, Field

from src.models.loan_return import LibrarianStatus


class LoanRenewalBase(BaseModel):
    loan_id: str

    class Config:
        use_enum_values = True


class LoanRenewalResponse(LoanRenewalBase):
    id: str = Field(alias="_id")
    status: LibrarianStatus = LibrarianStatus.PENDING
    date: datetime


class LoanRenewalCreate(LoanRenewalBase):
    pass


class LoanRenewalUpdate(LoanRenewalBase):
    status: LibrarianStatus
