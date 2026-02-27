from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date

    
class CreateCourseRequest(BaseModel):
    name: str
    description: Optional[str] = None
    learning_outcomes: Optional[List[str]] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None


class UpdateCourseRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class PutLearningOutcomesCoursesRequest(BaseModel):
    learning_outcomes: List[str]

class JoinCourseRequest(BaseModel):
    course_id: UUID