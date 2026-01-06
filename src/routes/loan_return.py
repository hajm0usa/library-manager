from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth import get_current_user
from src.crud.book import get_book_by_title, update_book
from src.crud.loan import get_loan, update_loan
from src.crud.loan_return import (create_loan_return, delete_loan_return,
                                  existing_loan_return, get_loan_id_returns,
                                  get_loan_return, get_loan_returns,
                                  update_loan_return)
from src.database import get_database
from src.models.book import BookUpdate
from src.models.loan import LoanStatus, LoanUpdate
from src.models.loan_return import (LibrarianStatus, LoanReturnCreate,
                                    LoanReturnResponse)
from src.models.user import Role

router = APIRouter(prefix="/loan_return", tags=["loan_return"])


@router.get("/id/{id}", response_model=LoanReturnResponse)
async def loan_return_get_by_id_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    loan_return = await get_loan_return(id, db)

    if not loan_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan return request not found",
        )

    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return loan_return

    loan = await get_loan(loan_return["loan_id"], db)
    if loan["username"] != user_data["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't see loan requests from other users as a member",
        )
    return loan_return


@router.post("/", response_model=LoanReturnResponse)
async def loan_return_create_route(
    loan_return_data: LoanReturnCreate,
    user_data=Depends(get_current_user),
    db=Depends(get_database),
):
    loan_return = loan_return_data.model_dump()

    existing = await existing_loan_return(loan_return["loan_id"], db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This loan return already exists",
        )

    loan = await update_loan(
        loan_return["loan_id"], LoanUpdate(status=LoanStatus.RETURNED), db
    )
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        loan_return_status = LibrarianStatus.APPROVED

        book = await get_book_by_title(loan["book_title"], db)
        await update_book(
            book["_id"],
            BookUpdate(
                available_count=book["available_count"] + 1,
                total_count=book["total_count"],
            ),
            db,
        )
    else:
        if loan["username"] != user_data["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't request return of other users loans",
            )
        loan_return_status = LibrarianStatus.PENDING

    loan_return["date"] = datetime.now()
    loan_return["status"] = LibrarianStatus.PENDING
    new_loan_return = await create_loan_return(
        LoanReturnCreate(**loan_return), loan_return_status, db
    )

    new_loan_return["_id"] = str(new_loan_return["_id"])
    return new_loan_return


@router.post("/approve/{id}", response_model=LoanReturnResponse)
async def loan_return_approve_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't approve loan return requests as a member",
        )

    loan_return = await get_loan_return(id, db)
    if loan_return is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan return request not found",
        )

    if LibrarianStatus(loan_return["status"]) == LibrarianStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This return request already approved",
        )

    await update_loan_return(db, id, LibrarianStatus.APPROVED)

    loan = await get_loan(loan_return["loan_id"], db)
    book = await get_book_by_title(loan["book_title"], db)
    await update_book(
        book["_id"],
        BookUpdate(
            available_count=book["available_count"] + 1, total_count=book["total_count"]
        ),
        db,
    )

    new_loan_return = await get_loan_return(id, db)
    return new_loan_return


@router.get("/loan/{loan_id}", response_model=List[LoanReturnResponse])
async def loan_return_loan_list_route(
    loan_id: str,
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_loan_id_returns(db, loan_id, skip, limit)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see a loan returns as a member",
    )


@router.get("/list", response_model=List[LoanReturnResponse])
async def loan_return_list_route(
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    librarian_status: Optional[LibrarianStatus] = LibrarianStatus.PENDING,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_loan_returns(db, skip, limit, status=librarian_status)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see loan returns list as a member",
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def loan_return_delete_route(
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
        deleted_loan_return = await delete_loan_return(id, db)

        if not deleted_loan_return:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No such loan return exists",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't delete loan returns as a memeber",
    )
