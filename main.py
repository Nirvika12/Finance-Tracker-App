from fastapi import FastAPI
from app.database import Base, engine
from app.routers import user_router, category_router, transaction_router

app = FastAPI()

app.include_router(user_router.router)
app.include_router(category_router.router)
app.include_router(transaction_router.router)

