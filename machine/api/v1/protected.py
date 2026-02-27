from fastapi import APIRouter, Depends
from core.utils.get_current_user import get_current_user
from machine.models.users import Users

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/protected")
async def protected_route(current_user: Users = Depends(get_current_user)):
    return {
        "message": "Token is valid",
        "user_info": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
        }
    }
