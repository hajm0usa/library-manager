from fastapi import FastAPI

from src.database import close_mongo_connection, connect_to_mongo
from src.routes.book import router as book_router
from src.routes.user import router as user_router


async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)

app.include_router(book_router)
app.include_router(user_router)


@app.get("/")
def home():
    return "Project started successfuly"
