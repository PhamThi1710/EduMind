from core.exceptions import UnauthorizedException


async def verify_token(token: str) -> dict:
    """
    Verifies a Supabase JWT using the Supabase Admin API.
    Returns a dict with 'sub' (UUID string) and 'email'.
    Raises UnauthorizedException if the token is invalid or expired.
    """
    from core.supabase import supabase
    try:
        response = supabase.auth.get_user(token)
    except Exception as e:
        raise UnauthorizedException(f"Token verification failed: {e}")

    if not response or not response.user:
        raise UnauthorizedException("Invalid or expired token")

    return {
        "sub": str(response.user.id),
        "email": response.user.email,
    }
