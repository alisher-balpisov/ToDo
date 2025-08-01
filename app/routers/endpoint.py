from fastapi import APIRouter

from .auth import router as auth_router
from .crud import router as crud_router
from .extra import router as extra_router
from .shared_tasks.endpoints import router as shared_tasks_router
from .task_file import router as task_file_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(crud_router, prefix="/tasks", tags=["Tasks"])
router.include_router(task_file_router, prefix="/tasks", tags=["Task Files"])
router.include_router(extra_router, prefix="/tasks", tags=["Extra"])
router.include_router(shared_tasks_router, tags=["Shared Tasks"])
