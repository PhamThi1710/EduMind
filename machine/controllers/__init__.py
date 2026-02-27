from .user import UserController
from .dashboard import StudentCoursesController, ActivitiesController
from .courses import CoursesController, StudentExercisesController
from .lessons import LessonsController, DocumentsController, ExtractedTextController
from .exercises import ExercisesController
from .recommend import (
    ModulesController,
    RecommendDocumentsController,
    RecommendLessonsController,
    LearningPathsController,
    RecommendQuizzesController,
    RecommendQuizQuestionController
)
from .feedback import FeedbackController
from .conversation import ConversationController
from .learning_material_gen import LearningMaterialGenController
from .user_logins import UserLoginsController

__all__ = [
    "UserController",
    "StudentCoursesController",
    "ActivitiesController",
    "CoursesController",
    "LessonsController",
    "ExercisesController",
    "StudentExercisesController",
    "ModulesController",
    "RecommendQuizzesController",
    "RecommendQuizQuestionController",
    "DocumentsController",
    "RecommendDocumentsController",
    "RecommendLessonsController",
    "LearningPathsController",
    "FeedbackController",
    "ExtractedTextController",
    "ConversationController",
    "LearningMaterialGenController",
    "UserLoginsController",
]
