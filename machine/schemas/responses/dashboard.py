from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from core.repository.enum import ActivityType,ExerciseType
from typing import List, Optional, Union
class WelcomeMessageResponse(BaseModel):
    course: str
    course_id: UUID
    last_accessed: datetime
    
class GetRecentActivitiesResponse(BaseModel):
    activity_id: UUID
    activity_description: str
    activity_type: ActivityType
    activity_date: datetime
    
class Events(BaseModel):
    exercise_id: UUID
    exercise_name: str
    exercise_time_open: Union[str, datetime]
    exercise_time_close: Union[str, datetime]
    exercise_type: ExerciseType
    course_name: str
    course_id: UUID
    course_courseID: str
    course_nSemester: int
    
class GetDashboardProfessorResponse(BaseModel):
    professor_id: UUID
    professor_name: str
    nCourses: int
    nLessons: int
    nStudents: int
    nExercises: int
    upcoming_events: Optional[List[Events]]
    
    
