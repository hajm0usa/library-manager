from datetime import datetime
from typing import Optional

from bson import ObjectId

from src.models.loan_renewal import LibrarianStatus, LoanRenewalCreate


async def create_loan_renewal(
    loan_renewal: LoanRenewalCreate, status: LibrarianStatus, db
):
    loan_renewal_dict = loan_renewal.model_dump()
    loan_renewal_dict["status"] = status.value
    loan_renewal_dict["date"] = datetime.now()

    result = await db.loan_renewals.insert_one(loan_renewal_dict)
    created_loan_renewal = await db.loan_renewals.find_one({"_id": result.inserted_id})

    created_loan_renewal["_id"] = str(created_loan_renewal["_id"])
    return created_loan_renewal


async def get_loan_renewal(id: str, db):
    loan_renewal = await db.loan_renewals.find_one({"_id": ObjectId(id)})

    if not loan_renewal:
        return None

    loan_renewal["_id"] = str(loan_renewal["_id"])
    return loan_renewal


async def get_loan_renewals(
    db, skip: int, limit: int, status: Optional[LibrarianStatus] = None
):
    if status:
        loan_renewals = (
            await db.loan_renewals.find({"status": status.value})
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
    else:
        loan_renewals = (
            await db.loan_renewals.find().skip(skip).limit(limit).to_list(length=limit)
        )

    for loan_renewal in loan_renewals:
        loan_renewal["_id"] = str(loan_renewal["_id"])

    return loan_renewals


async def get_loan_id_renewals(db, loan_id: str, skip: int, limit: int):
    loan_renewals = (
        await db.loan_renewals.find({"loan_id": loan_id})
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    for loan_renewal in loan_renewals:
        loan_renewal["_id"] = str(loan_renewal["_id"])

    return loan_renewals


async def existing_loan_renewal(loan_id: str, db):
    existing = await db.loan_renewals.find_one({"loan_id": loan_id})

    if not existing:
        return None

    existing["_id"] = str(existing["_id"])
    return existing


async def update_loan_renewal(
    db,
    id: str,
    status: LibrarianStatus,
):
    await db.loan_renewals.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": status.value}}
    )

    updated_loan_renewal = await get_loan_renewal(id, db)
    return updated_loan_renewal


async def delete_loan_renewal(id: str, db):
    deleted_loan_renewal = await db.loan_renewals.delete_one({"_id": ObjectId(id)})

    if deleted_loan_renewal.deleted_count == 0:
        return False
    return True
