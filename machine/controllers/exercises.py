from typing import Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select

from core.controller import BaseController
from core.db import Transactional
from core.exceptions.base import NotFoundException
from machine.models import Exercises
from machine.models.conversation import Conversation, Message
from machine.repositories import ExercisesRepository


class ExercisesController(BaseController[Exercises]):
    def __init__(
        self,
        exercises_repository: ExercisesRepository,
        llm_client: AsyncOpenAI,
    ):
        super().__init__(model_class=Exercises, repository=exercises_repository)
        self.exercises_repository = exercises_repository
        self.llm_client = llm_client
