from typing import Optional

from bson import ObjectId

from src.models.book import BookCreate, BookUpdate


async def get_book_by_id(id: str, db):
    book = await db.books.find_one({"_id": ObjectId(id)})

    if not book:
        return None

    book["_id"] = str(book["_id"])
    return book


async def search_book(
    db,
    skip: int,
    limit: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[str] = None,
):

    search_query = []

    if title:
        search_query.append({"title": {"$regex": title, "$options": "i"}})
    if author:
        search_query.append({"author": {"$regex": author, "$options": "i"}})
    if category:
        search_query.append({"category": {"$regex": category, "$options": "i"}})

    search_result = await db.books.find({"$or": search_query}).skip(skip).limit(limit).to_list(length=limit)

    for book in search_result:
        book["_id"] = str(book.pop("_id"))

    return search_result


async def get_books(db, skip: int, limit: int):
    books = await db.books.find().skip(skip).limit(limit).to_list(length=limit)

    for book in books:
        book["_id"] = str(book["_id"])

    return books


async def create_book(book: BookCreate, db):
    book_dict = book.model_dump()

    result = await db.books.insert_one(book_dict)
    created_book = await db.books.find_one({"_id": result.inserted_id})

    created_book["_id"] = str(created_book["_id"])
    return created_book


async def update_book(id: str, book: BookUpdate, db):
    updated_data = {k: v for k, v in book.model_dump().items() if v is not None}

    if updated_data:
        await db.books.update_one({"_id": ObjectId(id)}, {"$set": updated_data})

    updated_book = await db.books.find_one({"_id": ObjectId(id)})

    updated_book["_id"] = str(updated_book["_id"])
    return updated_book


async def delete_book(id: str, db):
    result = await db.books.delete_one({"_id": ObjectId(id)})

    if result.deleted_count == 0:
        return False
    return True
