from fastapi import FastAPI
from app.routers import todos
from app.routers import auth

app = FastAPI()
app.include_router(auth.router)
app.include_router(todos.router)
