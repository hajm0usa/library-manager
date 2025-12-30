import os

from motor.motor_asyncio import AsyncIOMotorClient

DB_NAME = os.environ["MONGO_DB_NAME"]


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def get_database():
    return db.client[DB_NAME]


async def connect_to_mongo():
    # TODO: Implement a logger and log database connections
    try:
        db.client = AsyncIOMotorClient("mongodb://mongo:27017")
        return True
    except:
        return False


async def close_mongo_connection():
    db.client.close()
