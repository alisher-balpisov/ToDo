from fastapi import APIRouter

from src.sharing.edit.views import router as sharing_edit_router
from src.sharing.file.views import router as sharing_file_router
from src.sharing.share.views import router as sharing_share_router
from src.sharing.view.views import router as sharing_view_router

api_router = APIRouter()

api_router.include_router(sharing_edit_router)
api_router.include_router(sharing_file_router)
api_router.include_router(sharing_share_router)
api_router.include_router(sharing_view_router)


# from .crud import router as crud_router
# from .extra import router as extra_router
# from .task_file import router as task_file_router

# api_router = APIRouter()

# api_router.include_router(
#     crud_router, prefix="/tasks", tags=["Tasks"])

# api_router.include_router(
#     task_file_router, prefix="/tasks", tags=["Task Files"])

# api_router.include_router(
#     extra_router, prefix="/tasks", tags=["Extra"])
