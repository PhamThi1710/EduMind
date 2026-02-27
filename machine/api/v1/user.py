from datetime import date
from typing import List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import or_

from core.exceptions import BadRequestException, ForbiddenException, NotFoundException, SystemException
from core.response import Ok
from core.utils.file import generate_presigned_url, upload_to_s3
from core.utils.get_current_user import get_current_user
from machine.models import UserLogins, Users
from machine.providers import InternalProvider
from machine.schemas.requests.user import UserCreate, UserLoginCreate, UserRole

router = APIRouter(prefix="/users", tags=["users"])


# ---------------------------------------------------------------------------
# POST / – Create one or many users (admin only) - Now use Supabase Auth
# ---------------------------------------------------------------------------

# @router.post("/", description="Create a new user")
# async def create_user(
#     user: Union[UserCreate, List[UserCreate]],
#     current_user: Users = Depends(get_current_user),
#     user_controller=Depends(InternalProvider().get_user_controller),
# ):
#     if current_user.role != "admin":
#         raise ForbiddenException(message="You are not allowed to access this feature.")

#     async def _create_one(u: UserCreate) -> dict:
#         # Map old UserRole enum values to the new unified role column
#         role_value = "user"
#         if u.role in (UserRole.admin, UserRole.professor):
#             role_value = "admin"

#         user_attributes = {
#             "email": u.email,
#             "full_name": u.fullname or u.name,
#             "date_of_birth": u.date_of_birth,
#             "role": role_value,
#         }
#         # Store legacy IDs in the appropriate column
#         if u.role == UserRole.student:
#             user_attributes["student_id_number"] = u.ms
#         elif u.role in (UserRole.professor, UserRole.admin):
#             user_attributes["employee_id_number"] = u.ms

#         created = await user_controller.user_repository.create(attributes=user_attributes, commit=True)
#         return {
#             "id": created.id,
#             "email": created.email,
#             "full_name": created.full_name,
#             "role": created.role,
#         }

#     if isinstance(user, list):
#         result = [await _create_one(u) for u in user]
#         return Ok(data=result, message="Users created successfully")

#     result = await _create_one(user)
#     return Ok(data=result, message="User created successfully")

# ---------------------------------------------------------------------------
# PATCH / – Update own profile
# ---------------------------------------------------------------------------

@router.patch("/", description="Update user information")
async def update_user_information(
    full_name: Optional[str] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: Users = Depends(get_current_user),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    user_attributes = {}
    if full_name:
        user_attributes["full_name"] = full_name
    if date_of_birth:
        user_attributes["date_of_birth"] = date_of_birth
    if file:
        file_content = await file.read()
        s3_key = await upload_to_s3(file_content, file.filename)
        user_attributes["avatar_url"] = s3_key

    if not user_attributes:
        return Ok(data=True, message="No fields to update.")

    try:
        await user_controller.user_repository.update(
            where_=[Users.id == current_user.id],
            attributes=user_attributes,
            commit=True,
        )
    except Exception as e:
        raise SystemException(f"Error updating user information: {str(e)}")

    return Ok(data=True, message="User information updated successfully")


# ---------------------------------------------------------------------------
# GET / – Own profile
# ---------------------------------------------------------------------------

@router.get("/", description="Get profile")
async def get_profile(
    current_user: Users = Depends(get_current_user),
):
    avatar_url = ""
    if current_user.avatar_url:
        if str(current_user.avatar_url).startswith("documents/"):
            avatar_url = generate_presigned_url(current_user.avatar_url)
        else:
            avatar_url = str(current_user.avatar_url)

    user_response = {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "avatar": avatar_url,
        "email": current_user.email,
        "ms": current_user.student_id_number or current_user.employee_id_number,
        "date_of_birth": current_user.date_of_birth,
        "role": current_user.role,
    }
    return Ok(data=user_response, message="User profile")


# ---------------------------------------------------------------------------
# GET /count – Count users (admin only)
# ---------------------------------------------------------------------------

@router.get("/count")
async def count_user(
    role: Optional[str] = Query(None),
    current_user: Users = Depends(get_current_user),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    where_ = [Users.role == role] if role else None
    count = await user_controller.user_repository.count(where_=where_)
    label = f"{role}s" if role else "all users"
    return Ok(data=count, message=f"Counted {label}")


# ---------------------------------------------------------------------------
# GET /admin – List all users with filters (admin only)
# ---------------------------------------------------------------------------

@router.get("/admin", description="Get all users")
async def get_all_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status (true/false)"),
    search_query: Optional[str] = Query(None, description="Search by student_id_number, employee_id_number, or email"),
    current_user: Users = Depends(get_current_user),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    try:
        where_conditions = []
        if role:
            where_conditions.append(Users.role == role)
        if status is not None:
            is_active = status.lower() == "true"
            where_conditions.append(Users.is_active == is_active)
        if search_query:
            where_conditions.append(
                or_(
                    Users.student_id_number.ilike(f"%{search_query}%"),
                    Users.employee_id_number.ilike(f"%{search_query}%"),
                    Users.email.ilike(f"%{search_query}%"),
                )
            )

        users = await user_controller.user_repository.get_many(where_=where_conditions if where_conditions else None)
        users_response = [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "ms": u.student_id_number or u.employee_id_number,
                "date_of_birth": u.date_of_birth,
                "status": u.is_active,
                "role": u.role,
            }
            for u in users
        ]
        return Ok(data=users_response, message="Filtered users")
    except Exception as e:
        raise SystemException(f"Error fetching users: {str(e)}")


# ---------------------------------------------------------------------------
# GET /user-logs – Login logs (admin only) - Now no need to track this information
# ---------------------------------------------------------------------------

# @router.get("/user-logs", description="Get user login logs")
# async def get_user_login_logs(
#     current_user: Users = Depends(get_current_user),
#     user_logins_controller=Depends(InternalProvider().get_user_logins_controller),
# ):
#     if current_user.role != "admin":
#         raise ForbiddenException(message="You are not allowed to access this feature.")

#     user_logins = await user_logins_controller.user_logins_repository.get_many()
#     user_logins_response = [
#         {
#             "id": ul.id,
#             "user_id": ul.user_id,
#             "user_role": ul.user_role,
#             "login_timestamp": ul.login_timestamp,
#         }
#         for ul in user_logins
#     ]
#     return Ok(data=user_logins_response, message="User login logs")


# # ---------------------------------------------------------------------------
# # POST /user-logs – Create login log (admin only)
# # ---------------------------------------------------------------------------

# @router.post("/user-logs", description="Create user login log")
# async def create_user_login_log(
#     user_login: UserLoginCreate,
#     current_user: Users = Depends(get_current_user),
#     user_logins_controller=Depends(InternalProvider().get_user_logins_controller),
# ):
#     if current_user.role != "admin":
#         raise ForbiddenException(message="You are not allowed to access this feature.")

#     user_logins_attributes = {
#         "user_id": current_user.id,
#         "user_role": user_login.user_role,
#         "login_timestamp": user_login.login_timestamp.astimezone().replace(tzinfo=None),
#     }
#     created = await user_logins_controller.user_logins_repository.create(
#         attributes=user_logins_attributes, commit=True
#     )
#     return Ok(
#         data={
#             "id": created.id,
#             "user_id": created.user_id,
#             "user_role": created.user_role,
#             "login_timestamp": created.login_timestamp,
#         },
#         message="User login log created successfully",
#     )


# ---------------------------------------------------------------------------
# GET /{user_id} – Get single user (admin only)
# ---------------------------------------------------------------------------

@router.get("/{user_id}", description="Get user information for admin")
async def get_user_information(
    user_id: UUID,
    current_user: Users = Depends(get_current_user),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    user = await user_controller.user_repository.first(where_=[Users.id == user_id])
    if not user:
        raise NotFoundException(message="User not found")

    return Ok(
        data={
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "avatar": str(user.avatar_url) if user.avatar_url else "",
            "ms": user.student_id_number or user.employee_id_number,
            "role": user.role,
        },
        message="User information",
    )


# ---------------------------------------------------------------------------
# PATCH /status/{user_id} – Toggle active status (admin only)
# ---------------------------------------------------------------------------

@router.patch("/status/{user_id}", description="Update user status for admin")
async def update_user_status(
    user_id: UUID,
    current_user: Users = Depends(get_current_user),
    user_controller=Depends(InternalProvider().get_user_controller),
):
    if current_user.role != "admin":
        raise ForbiddenException(message="You are not allowed to access this feature.")

    user = await user_controller.user_repository.first(where_=[Users.id == user_id])
    if not user:
        raise NotFoundException(message="User not found")

    await user_controller.user_repository.update(
        where_=[Users.id == user_id],
        attributes={"is_active": not user.is_active},
        commit=True,
    )
    return Ok(data=True, message="User status updated successfully")