from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth import get_current_user
from src.crud.book import get_book_by_title, update_book
from src.crud.loan import (create_loan, delete_loan, existing_loan,
                           get_book_loans, get_loan, get_loans, get_user_loans,
                           update_loan)
from src.crud.user import get_user_by_username
from src.database import get_database
from src.models.book import BookUpdate
from src.models.loan import LoanCreate, LoanResponse, LoanStatus, LoanUpdate
from src.models.user import Role

router = APIRouter(prefix="/loan", tags=["loan"])


@router.get("/id/{id}", response_model=LoanResponse)
async def loan_get_by_id_route(id: str, db=Depends(get_database)):
    loan = await get_loan(id, db)

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    return loan


@router.put("/approve/{id}", response_model=LoanResponse)
async def loan_approve_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't approve loan requests as a member",
        )

    loan = await get_loan(id, db)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )

    book = await get_book_by_title(loan["book_title"], db)
    available_books = book["available_count"]

    if available_books == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is no available book in library",
        )

    await update_book(
        book["_id"],
        BookUpdate(
            available_count=available_books - 1, total_count=book["total_count"]
        ),
        db,
    )

    loan["status"] = LoanStatus.APPROVED
    now = datetime.now()
    loan["date"] = now
    loan["return_date"] = now + timedelta(days=14)

    approved_loan = await update_loan(id, LoanUpdate(**loan), db)

    return approved_loan


@router.post("/", response_model=LoanResponse)
async def loan_create_route(
    loan_data: LoanCreate, user_data=Depends(get_current_user), db=Depends(get_database)
):
    loan = loan_data.model_dump()

    if Role(user_data["role"]) == Role.MEMBER:
        loan["username"] = user_data["sub"]
        loan["status"] = LoanStatus.PENDING
    elif Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        loan["status"] = LoanStatus.APPROVED

        user = get_user_by_username(loan["username"], db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    existing = await existing_loan(loan["username"], loan["book_title"], db)
    if existing and LoanStatus(existing["status"]) != LoanStatus.RETURNED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You already loaned this book"
        )

    book = await get_book_by_title(loan["book_title"], db)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such book found"
        )

    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        available_books = book["available_count"]

        if available_books == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There is no available book in library",
            )

        await update_book(
            book["_id"],
            BookUpdate(
                available_count=available_books - 1,
                total_count=book["total_count"]
            ),
            db,
        )

    new_loan = await create_loan(LoanCreate(**loan), db)

    new_loan["_id"] = str(new_loan["_id"])
    return new_loan


@router.get("/my_loans", response_model=List[LoanResponse])
async def loan_user_list_route(
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_database),
):
    return await get_user_loans(db, user_data["sub"], skip, limit)


@router.get("/book/{book_title}", response_model=List[LoanResponse])
async def loan_book_list_route(
    book_title: str,
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_book_loans(db, book_title, skip, limit)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see a book loans as a member",
    )


@router.get("/list", response_model=List[LoanResponse])
async def loan_list_route(
    user_data=Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
    loan_status: Optional[LoanStatus] = None,
    db=Depends(get_database),
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        return await get_loans(db, skip, limit, status=loan_status)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't see loans list as a member",
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def loan_delete_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) in [Role.ADMIN, Role.LIBRARIAN]:
        deleted_loan = await delete_loan(id, db)

        if not deleted_loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No such loan exists"
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't delete loans as a memeber",
    )
