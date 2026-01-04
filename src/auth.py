import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordBearer)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from src.crud.user import get_user_by_username
from src.database import get_database
from src.models.user import UserBase

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = OAuth2PasswordBearer(tokenUrl="token")


class UserInDB(UserBase):
    hashed_password: str = Field(alias="password")


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


async def get_user(username: str, db):
    user = await get_user_by_username(username, db)
    if not user:
        return None
    return UserInDB(**user)


async def authenticate_user(username: str, password: str, db):
    user = await get_user(username, db)
    if not (user and verify_password(password, user.hashed_password)):
        return None
    return user


def create_access_token(data: dict, expire_delta: Optional[datetime] = None):
    expire = datetime.now(timezone.utc) + (expire_delta or timedelta(minutes=15))
    data.update({"exp": str(expire)})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_database),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user(username, db)
    if user is None:
        raise credentials_exception
    return UserBase(**user.model_dump())
