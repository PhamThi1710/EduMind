from core.db import Base  # noqa: F401, This import is necessary for Alembic to detect the models

from .users import Users
from .courses import Courses
from .exercises import Exercises
from .documents import Documents
from .modules import Modules
from .recommend_quizzes import RecommendQuizzes, RecommendQuizQuestion
from .recommend_documents import RecommendDocuments
from .recommend_lessons import RecommendLessons
from .learning_paths import LearningPaths
from .feedback import Feedback
from .user_logins import UserLogins
from .extracted_text import ExtractedText
from .conversation import Conversation, Message
