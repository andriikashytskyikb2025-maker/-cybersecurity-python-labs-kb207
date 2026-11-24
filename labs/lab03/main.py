from contextlib import asynccontextmanager
from fastapi import FastAPI
from labs.lab03.database import initialize_database
from labs.lab03.routers import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield

app = FastAPI(
    title="Реєстр вразливостей вебзастосунку",
    description="Сервіс обліку знахідок перевірки вебзастосунку. Одиниця вимірювання — score (0–10).",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)