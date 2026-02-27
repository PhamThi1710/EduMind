from core.controller import BaseController
from machine.models.user_logins import UserLogins
from machine.repositories.user_logins import UserLoginsRepository


class UserLoginsController(BaseController[UserLogins]):
    def __init__(self, user_logins_repository: UserLoginsRepository):
        super().__init__(model_class=UserLogins, repository=user_logins_repository)
        self.user_logins_repository = user_logins_repository
