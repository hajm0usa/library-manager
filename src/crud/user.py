from datetime import datetime

from bson import ObjectId

from src.database import get_database
from src.models.user import UserCreate, UserUpdate


async def check_username_exists(username: str, db):
    user = await db.users.find_one({"username": username})
    if user:
        return True
    return False


async def create_user(user: UserCreate, hashed_password: str, db):
    user_dict = user.model_dump()
    user_dict["password"] = hashed_password
    user_dict["created_at"] = datetime.now()

    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    created_user["_id"] = str(created_user["_id"])
    return created_user


async def get_user_by_username(username: str, db):
    user = await db.users.find_one({"username": username})

    if not user:
        return None

    user["_id"] = str(user["_id"])
    return user


async def get_user_by_id(id: str, db):
    user = await db.users.find_one({"_id": ObjectId(id)})

    if not user:
        return None

    user["_id"] = str(user["_id"])
    return user


async def get_users(db, skip=0, limit=10):
    users_list = await db.users.find().skip(skip).limit(limit).to_list(length=limit)

    for user in users_list:
        user["_id"] = str(user["_id"])

    return users_list


async def update_user(id: str, user_update: UserUpdate, db):
    updated_data = {k: v for k, v in user_update.model_dump().items() if v is not None}

    if updated_data:
        await db.users.update_one({"_id": id}, {"$set": updated_data})

    updated_user = await db.users.find_one({"_id": ObjectId(id)})

    updated_user["_id"] = str(updated_user["_id"])
    return updated_user


async def delete_user(username: str, db) -> bool:
    result = await db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        return False
    return True
