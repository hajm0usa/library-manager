from fastapi import FastAPI

from src.database import close_mongo_connection, connect_to_mongo


async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return "Project started successfuly"
