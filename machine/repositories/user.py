from core.repository import BaseRepository
from machine.models.users import Users


class UserRepository(BaseRepository[Users]):
    """
    Repository for the unified Users model.
    Add custom query methods as needed.
    """
    pass