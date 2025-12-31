from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field


def book_count_validator(value: int) -> int:
    if value < 0:
        raise ValueError("The count of books can not be a negative number")
    return value


class BookBase(BaseModel):
    title: str
    author: str
    category: str
    total_count: Optional[Annotated[int, BeforeValidator(book_count_validator)]] = 0
    available_count: Optional[Annotated[int, BeforeValidator(book_count_validator)]] = 0


class BookResponse(BookBase):
    id: str = Field(alias="_id")


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    total_count: Optional[Annotated[int, BeforeValidator(book_count_validator)]] = 0
    available_count: Optional[Annotated[int, BeforeValidator(book_count_validator)]] = 0
