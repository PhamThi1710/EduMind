from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from core.repository.enum import ExerciseType
from typing import List, Optional, Union


class WelcomeMessageResponse(BaseModel):
    course: str
    course_id: UUID
    
class Events(BaseModel):
    exercise_id: UUID
    exercise_name: str
    exercise_time_open: Union[str, datetime]
    exercise_time_close: Union[str, datetime]
    exercise_type: ExerciseType
    course_name: str
    course_id: UUID

    
class GetDashboardResponse(BaseModel):
    user_id: UUID
    user_name: str
    nCourses: int
    nExercises: int
    upcoming_events: Optional[List[Events]] = None