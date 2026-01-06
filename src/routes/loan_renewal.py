from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth import get_current_user
from src.crud.loan import get_loan, update_loan
from src.crud.loan_renewal import (create_loan_renewal, delete_loan_renewal,
                                   existing_loan_renewal, get_loan_id_renewals,
                                   get_loan_renewal, get_loan_renewals,
                                   update_loan_renewal)
from src.database import get_database
from src.models.loan import LoanStatus, LoanUpdate
from src.models.loan_renewal import (LibrarianStatus, LoanRenewalCreate,
                                     LoanRenewalResponse)
from src.models.user import Role

router = APIRouter(prefix="/loan_renewal", tags=["loan_renewal"])


@router.get("/id/{id}", response_model=LoanRenewalResponse)
async def loan_renewal_get_by_id_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    loan_renewal = await get_loan_renewal(id, db)

    if not loan_renewal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan renewal request not found",
        )

    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return loan_renewal

    loan = await get_loan(loan_renewal["loan_id"], db)

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No loan found for this loan renewal request. maybe it's deleted",
        )
    if loan["username"] != user_data["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't see loan renewal requests from other users as a member",
        )
    return loan_renewal


@router.post("/", response_model=LoanRenewalResponse)
async def loan_renewal_create_route(
    loan_renewal_data: LoanRenewalCreate,
    user_data=Depends(get_current_user),
    db=Depends(get_database),
):
    loan_renewal = loan_renewal_data.model_dump()

    loan = await get_loan(loan_renewal["loan_id"], db)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )

    if Role(user_data["role"]) == Role.MEMBER:
        if loan["username"] != user_data["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't request renewal of other users loans",
            )

        if LoanStatus(loan["status"]) != LoanStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only renew approved loans",
            )

    existing = await existing_loan_renewal(loan_renewal["loan_id"], db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This loan renewal already exists",
        )

    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        loan_renewal_status = LibrarianStatus.APPROVED

        await update_loan(
            loan_renewal["loan_id"], LoanUpdate(status=LoanStatus.APPROVED), db
        )

        new_return_date = loan["return_date"] + timedelta(days=14)
        await update_loan(
            loan_renewal["loan_id"], LoanUpdate(return_date=new_return_date), db
        )
    else:
        loan_renewal_status = LibrarianStatus.PENDING

        await update_loan(
            loan_renewal["loan_id"], LoanUpdate(status=LoanStatus.RENEW_PENDING), db
        )

    new_loan_renewal = await create_loan_renewal(
        LoanRenewalCreate(**loan_renewal), loan_renewal_status, db
    )

    new_loan_renewal["_id"] = str(new_loan_renewal["_id"])
    return new_loan_renewal


@router.post("/approve/{id}", response_model=LoanRenewalResponse)
async def loan_renewal_approve_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't approve loan renewal requests as a member",
        )

    loan_renewal = await get_loan_renewal(id, db)
    if loan_renewal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan renewal request not found",
        )

    if LibrarianStatus(loan_renewal["status"]) == LibrarianStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This renewal request already approved",
        )

    await update_loan_renewal(db, id, LibrarianStatus.APPROVED)

    loan = await get_loan(loan_renewal["loan_id"], db)
    new_return_date = loan["return_date"] + timedelta(days=14)

    await update_loan(
        loan_renewal["loan_id"],
        LoanUpdate(status=LoanStatus.APPROVED, return_date=new_return_date),
        db,
    )

    new_loan_renewal = await get_loan_renewal(id, db)
    return new_loan_renewal


@router.get("/loan/{loan_id}", response_model=List[LoanRenewalResponse])
async def loan_renewal_loan_list_route(
    loan_id: str,
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_loan_id_renewals(db, loan_id, skip, limit)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see a loan renewals as a member",
    )


@router.get("/list", response_model=List[LoanRenewalResponse])
async def loan_renewal_list_route(
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    librarian_status: Optional[LibrarianStatus] = None,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_loan_renewals(db, skip, limit, status=librarian_status)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see loan renewals list as a member",
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def loan_renewal_delete_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    loan = await get_loan(id, db)

    if not loan:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such loan renewal exists"
        )

    if (
        Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]
        or user_data["sub"] == loan["username"]
    ):
        deleted_loan_renewal = await delete_loan_renewal(id, db)

        if not deleted_loan_renewal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No such loan renewal exists",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't delete loan renewals as a memeber",
    )
