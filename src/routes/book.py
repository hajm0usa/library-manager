from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth import get_current_user
from src.crud.book import (create_book, delete_book, get_book_by_id, get_books,
                           search_book, update_book)
from src.database import get_database
from src.models.book import BookCreate, BookResponse, BookUpdate
from src.models.user import Role

router = APIRouter(prefix="/book", tags=["book"])


@router.get("/book/{id}", response_model=list[BookResponse])
async def book_get_by_id_route(id: str, db=Depends(get_database)):
    book = await get_book_by_id(id, db)
    return book


@router.get("/search")
async def book_search_route(
    title: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
    db=Depends(get_database),
):
    books = await search_book(db, title, author, category)
    return books


@router.get("/list", response_model=list[BookResponse])
async def book_list_route(skip=0, limit=10, db=Depends(get_database)):
    books = await get_books(db, skip, limit)
    return books


@router.post("/", response_model=BookResponse)
async def book_create_route(
    book: BookCreate, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if user_data["role"] in [Role.ADMIN, Role.LIBRARIAN]:
        unique = search_book(title=book.title, author=book.author, db=db)
        if not unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book with this title and author exists",
            )
        book = await create_book(book, db)
        return book
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins and librarians can add books",
    )


@router.put("/book/{id}", response_model=BookResponse)
async def book_update_route(
    id: str,
    book: BookUpdate,
    user_data=Depends(get_current_user),
    db=Depends(get_database),
):
    if user_data["role"] in [Role.ADMIN, Role.LIBRARIAN]:
        old_book = await get_book_by_id(id, db)
        if not old_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            )

        if not book.title:
            book.title = old_book["title"]
        if not book.author:
            book.author = old_book["author"]
        if not book.category:
            book.category = old_book["category"]
        if not book.total_count:
            book.total_count = old_book["total_count"]
        if not book.available_count:
            book.available_count = old_book["available_count"]

        if book.total_count < book.available_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total count of books cannot be less than availabe count",
            )

        unique = await search_book(db, book.title, book.author, book.category)
        if not unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book with this fields already exists",
            )

        new_book = await update_book(id, book, db)
        return new_book
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins and librarians can edit books",
    )


@router.delete("/book/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def book_delete_route(
    id: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if user_data["role"] in [Role.ADMIN, Role.LIBRARIAN]:
        deleted_book = await delete_book(id, db)
        if not deleted_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Book not found"
            )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins and librarians can delete books",
    )
