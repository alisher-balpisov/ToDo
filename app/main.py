from fastapi import FastAPI
from app.routes import todos
from app.routes import auth
app = FastAPI()
app.include_router(todos.router)
app.include_router(auth.router)

