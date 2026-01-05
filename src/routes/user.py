from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.auth import get_current_user, hash_password
from src.crud.user import (check_username_exists, create_user, delete_user,
                           get_user_by_id, get_user_by_username, get_users, update_user)
from src.database import get_database
from src.models.user import Role, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def user_create_route(
    user: UserCreate, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) == Role.ADMIN:
        existing_username = await check_username_exists(user.username, db)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )
        return await create_user(user, hash_password(user.password), db)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You cannot create a user as a member",
    )


@router.get("/id/{user_id}", response_model=UserResponse)
async def user_get_by_id_route(id: str, user_data=Depends(get_current_user), db=Depends(get_database)):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't see users as a member")
    user = await get_user_by_id(id, db)
    if user:
        return user
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/username/{username}", response_model=UserResponse)
async def user_get_by_username(username: str, user_data=Depends(get_current_user), db=Depends(get_database)):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't see users as a member")
    user = await get_user_by_username(username, db)
    if user:
        return user
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

@router.get("/list", response_model=List[UserResponse])
async def user_list_route(skip: int = 0, limit: int = 10, user_data=Depends(get_current_user), db=Depends(get_database)):
    if Role(user_data["role"]) not in [Role.ADMIN, Role.LIBRARIAN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't see list of users as a member")

    users_list = await get_users(db, skip, limit)
    return users_list


@router.put("/{username}", response_model=UserResponse)
async def user_update_route(
    id: str,
    user: UserUpdate,
    user_data=Depends(get_current_user),
    db=Depends(get_database),
):
    if Role(user_data["role"]) == Role.ADMIN or id == user_data["id"]:
        if user.username:
            existing_username = await check_username_exists(user.username, db)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username already exists",
                )

        return await update_user(id, user, db)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="You can't edit other users info"
    )


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def user_delete_route(
    username: str, user_data=Depends(get_current_user), db=Depends(get_database)
):
    if Role(user_data["role"]) == Role.ADMIN or id == user_data["id"]:
        deleted_user = await delete_user(username, db)
        if not deleted_user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="You can't delete other users"
    )
