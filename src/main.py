from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import create_tables
from src.endpoints import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    print("\nПрограмма остановлена.")
    print("-" * 30 + "\n")

app = FastAPI(
    title="TodoApp API",
    description="Enterprise Todo Application",
    version="1.0.0",
    lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


app.include_router(api_router)
