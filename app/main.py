from fastapi import FastAPI

from app.routers import crud, auth, extra, task_sharing

app = FastAPI()
app.include_router(auth.router)
app.include_router(crud.router)
app.include_router(extra.router)
app.include_router(task_sharing.router)