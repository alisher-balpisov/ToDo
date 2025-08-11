from fastapi import APIRouter

from src.auth.views import router as auth_router
from src.sharing.edit.views import router as sharing_edit_router
from src.sharing.file.views import router as sharing_file_router
from src.sharing.share.views import router as sharing_share_router
from src.sharing.view.views import router as sharing_view_router
from src.tasks.crud.views import router as tasks_crud_router
from src.tasks.extra.views import router as tasks_extra_router
from src.tasks.file.views import router as tasks_file_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")

api_router.include_router(sharing_edit_router, prefix="/sharing")
api_router.include_router(sharing_file_router, prefix="/sharing")
api_router.include_router(sharing_share_router, prefix="/sharing")
api_router.include_router(sharing_view_router, prefix="/sharing")

api_router.include_router(tasks_crud_router, prefix="/tasks")
api_router.include_router(tasks_extra_router, prefix="/tasks")
api_router.include_router(tasks_file_router, prefix="/tasks")
