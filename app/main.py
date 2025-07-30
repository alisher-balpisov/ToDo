from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import create_tables
from app.routers import auth, crud, extra, task_sharing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any, None]:
    create_tables()
    yield
    print("\nПрограмма остановлена.")
    print("-" * 30 + "\n")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(crud.router)
app.include_router(extra.router)
app.include_router(task_sharing.router)
