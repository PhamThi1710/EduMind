from fastapi import APIRouter

# from machine.api.v2.user import router as user_router

# # router.include_router(user_router)
from .courses import router as courses_router

router = APIRouter(prefix="/v2")

router.include_router(courses_router)

__all__ = ["router"]
