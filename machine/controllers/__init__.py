from .user import UserController
from .courses import CoursesController
from .lessons import DocumentsController, ExtractedTextController
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
    "CoursesController",
    "ExercisesController",
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
