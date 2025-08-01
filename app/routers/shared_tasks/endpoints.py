from fastapi import APIRouter

from .file import router as file_router
from .sharing import router as sharing_router
from .task_edit import router as task_edit_router
from .task_view import router as task_view_router

router = APIRouter()


router.include_router(file_router)
router.include_router(sharing_router)
router.include_router(task_edit_router)
router.include_router(task_view_router)
