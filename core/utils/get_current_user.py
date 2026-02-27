"""
FastAPI dependency providing the current authenticated user.

Flow:
1. Extract Bearer token from Authorization header
2. Verify against Supabase Auth (server-side)
3. Look up user row in the local `users` table by Supabase UUID
4. Auto-create user row on first request (role defaults to "user")
5. Return the Users ORM object

Usage:
    from core.utils.get_current_user import get_current_user

    @router.get("/me")
    async def me(current_user: Users = Depends(get_current_user)):
        return current_user
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.utils.auth_utils import verify_token
from machine.models.users import Users

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Users:
    """
    Verifies the Supabase token and auto-provisions a users row on first login.
    Injects DB session via InternalProvider to avoid circular imports.
    """
    from machine.providers.internal import InternalProvider
    from core.db.session import DB_MANAGER, Dialect

    token = credentials.credentials
    payload = await verify_token(token)
    user_id = payload["sub"]
    email = payload["email"]

    # Get DB session
    async for db_session in DB_MANAGER[Dialect.POSTGRES].get_session():
        from machine.repositories.user import UserRepository

        repo = UserRepository(model=Users, db_session=db_session)
        user = await repo.first(where_=[Users.id == user_id])

        if user is None:
            # Auto-provision on first login
            user = await repo.create(
                attributes={"id": user_id, "email": email, "role": "user"},
                commit=True,
            )

        return user


async def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency that additionally asserts the user has admin role."""
    from core.exceptions import ForbiddenException
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")
    return current_user
