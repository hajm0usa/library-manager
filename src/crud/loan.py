from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from src.models.loan import LoanCreate, LoanStatus, LoanUpdate


async def create_loan(loan: LoanCreate, db):
    loan_dict = loan.model_dump()

    now = datetime.now()
    loan_dict["date"] = now
    loan_dict["return_date"] = now + timedelta(days=14)

    result = await db.loans.insert_one(loan_dict)
    created_book = await db.loans.find_one({"_id": result.inserted_id})

    created_book["_id"] = str(created_book["_id"])
    return created_book


async def get_loan(id: str, db):
    loan = await db.loans.find_one({"_id": ObjectId(id)})

    if not loan:
        return None

    loan["_id"] = str(loan["_id"])
    return loan


async def get_loans(db, skip: int, limit: int, status: Optional[LoanStatus] = None):
    if status:
        loans = (
            await db.loans.find({"status": status.value})
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
    else:
        loans = await db.loans.find().skip(skip).limit(limit).to_list(length=limit)

    for loan in loans:
        loan["_id"] = str(loan["_id"])

    return loans


async def get_user_loans(db, username: str, skip=0, limit=10):
    loans = (
        await db.loans.find({"username": username})
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    for loan in loans:
        loan["_id"] = str(loan["_id"])

    return loans


async def get_book_loans(db, book_title: str, skip: int, limit: int):
    loans = (
        await db.loans.find({"book_title": book_title})
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    for loan in loans:
        loan["_id"] = str(loan["_id"])

    return loans


async def existing_loan(username: str, book_title: str, db):
    existing = await db.loans.find_one({"username": username, "book_title": book_title})

    if not existing:
        return None

    existing["_id"] = str(existing["_id"])
    return existing


async def update_loan(id: str, loan_update: LoanUpdate, db):
    loan = {k: v for k, v in loan_update.model_dump().items() if v is not None}

    await db.loans.update_one({"_id": ObjectId(id)}, {"$set": loan})

    updated_loan = await get_loan(id, db)
    return updated_loan


async def delete_loan(id: str, db):
    deleted_loan = await db.loans.delete_one({"_id": ObjectId(id)})

    if deleted_loan.deleted_count == 0:
        return False
    return True
