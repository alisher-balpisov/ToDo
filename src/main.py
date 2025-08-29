# src/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import create_tables
from src.core.exception_handlers import register_exception_handlers
from src.endpoints import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router)
