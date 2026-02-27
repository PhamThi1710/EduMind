from .user import UserRepository
from .courses import CoursesRepository
from .exercises import ExercisesRepository
from .documents import DocumentsRepository, ExtractedTextRepository
from .modules import ModulesRepository
from .recommend_quizzes import RecommendQuizzesRepository, RecommendQuizQuestionRepository
from .recommend_documents import RecommendDocumentsRepository
from .learning_paths import LearningPathsRepository
from .recommend_lessons import RecommendLessonsRepository
from .feedback import FeedbackRepository
from .conversation import ConversationRepository, MessageRepository
from .user_logins import UserLoginsRepository

__all__ = [
    "UserRepository",
    "CoursesRepository",
    "ExercisesRepository",
    "DocumentsRepository",
    "ExtractedTextRepository",
    "ModulesRepository",
    "RecommendDocumentsRepository",
    "LearningPathsRepository",
    "RecommendLessonsRepository",
    "RecommendQuizzesRepository",
    "RecommendQuizQuestionRepository",
    "FeedbackRepository",
    "ConversationRepository",
    "MessageRepository",
    "UserLoginsRepository",
]
