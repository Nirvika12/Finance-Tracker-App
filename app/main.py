from fastapi import FastAPI
from app.database import Base, engine
from app.routers import user_router, category_router, transaction_router, budget_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(user_router.router)
app.include_router(category_router.router)
app.include_router(transaction_router.router)
app.include_router(budget_router.router)



