from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from core.repository.enum import *


class GetCoursesListResponse(BaseModel):
    course_id: UUID
    course_name: str

    course_start_date: Optional[date] = None
    course_end_date: Optional[date] = None

class LessonInLearningPath(BaseModel):
    recommend_lesson_id: UUID
    title: str
    description: Optional[str] = None
    progress: int

class LearningPathProgressInCourse(BaseModel):
    learning_path_id: UUID
    progress: int
    objective: Optional[str] = None
    lessons: List[LessonInLearningPath]
