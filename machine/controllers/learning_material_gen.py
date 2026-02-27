from core.db import Transactional
from uuid import UUID
from core.repository.enum import ExerciseType
import machine.repositories as repos
import machine.models as models


class LearningMaterialGenController:
    def __init__(
        self,
        module_repo: repos.ModulesRepository,
        exercises_repo: repos.ExercisesRepository,
    ):
        self.module_repo = module_repo
        self.exercises_repo = exercises_repo

    @Transactional()
    async def generate_quiz_exercise(self, module_id: UUID):
        """
        Placeholder for future AI-based quiz exercise generation.
        (Programming exercise generation with Judge0 has been removed.)
        """
        module = await self.module_repo.first(where_=[models.Modules.id == module_id])
        if not module:
            raise ValueError("Module not found.")

        # Future: call an LLM service here to generate quiz questions
        raise NotImplementedError("Quiz exercise generation not yet implemented.")
