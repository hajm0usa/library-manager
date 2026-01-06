from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth import Token, authenticate_user, create_access_token
from src.database import close_mongo_connection, connect_to_mongo, get_database
from src.routes.book import router as book_router
from src.routes.loan import router as loan_router
from src.routes.loan_renewal import router as loan_renewal_router
from src.routes.loan_return import router as loan_return_router
from src.routes.user import router as user_router


async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(lifespan=lifespan)

app.include_router(book_router)
app.include_router(user_router)
app.include_router(loan_router)
app.include_router(loan_return_router)
app.include_router(loan_renewal_router)


@app.get("/")
def home():
    return "Project started successfuly"


@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(
    login_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_database)
):
    user = await authenticate_user(login_data.username, login_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})

    return {"access_token": access_token, "token_type": "bearer"}
