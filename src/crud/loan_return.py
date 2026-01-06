from datetime import datetime
from typing import Optional

from bson import ObjectId

from src.models.loan_return import LoanReturnCreate, LibrarianStatus


async def create_loan_return(
    loan_return: LoanReturnCreate, status: LibrarianStatus, db
):
    loan_return_dict = loan_return.model_dump()
    loan_return_dict["status"] = status.value
    loan_return_dict["date"] = datetime.now()

    result = await db.loan_returns.insert_one(loan_return_dict)
    created_loan_return = await db.loan_returns.find_one({"_id": result.inserted_id})

    created_loan_return["_id"] = str(created_loan_return["_id"])
    return created_loan_return


async def get_loan_return(id: str, db):
    loan_return = await db.loan_returns.find_one({"_id": ObjectId(id)})

    if not loan_return:
        return None

    loan_return["_id"] = str(loan_return["_id"])
    return loan_return


async def get_loan_returns(
    db, skip: int, limit: int, status: Optional[LibrarianStatus] = None
):
    if status:
        loan_returns = (
            await db.loan_returns.find({"status": status.value})
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
    else:
        loan_returns = (
            await db.loan_returns.find().skip(skip).limit(limit).to_list(length=limit)
        )

    for loan_return in loan_returns:
        loan_return["_id"] = str(loan_return["_id"])

    return loan_returns


async def get_loan_id_returns(db, loan_id: str, skip: int, limit: int):
    loan_returns = (
        await db.loan_returns.find({"loan_id": ObjectId(loan_id)})
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    for loan_return in loan_returns:
        loan_return["_id"] = str(loan_return["_id"])

    return loan_returns


async def existing_loan_return(loan_id: str, db):
    existing = await db.loan_returns.find_one({"loan_id": ObjectId(loan_id)})

    if not existing:
        return None

    existing["_id"] = str(existing["_id"])
    return existing


async def update_loan_return(
    db,
    id: str,
    status: LibrarianStatus,
):
    await db.loan_returns.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": status.value}}
    )

    updated_loan_return = await get_loan_return(id, db)
    return updated_loan_return


async def delete_loan_return(id: str, db):
    deleted_loan_return = await db.loan_returns.delete_one({"_id": ObjectId(id)})

    if deleted_loan_return.deleted_count == 0:
        return False
    return True
