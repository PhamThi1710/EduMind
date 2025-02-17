from pydantic import BaseModel, validator, Field
from typing import Optional, List
from uuid import UUID
from data.constant import expectedHeaders

class BookmarkLessonRequest(BaseModel):
    student_id: UUID
    lesson_id: UUID
    course_id: UUID
    
class CreateCourseRequest_Course(BaseModel):
    professor_email: str
    name: str
    nCredit: int
    nSemester: int
    student_list: List[str]
    courseID: str
class CreateCourseRequest(BaseModel):
    headers: List[str]
    courses: List[CreateCourseRequest_Course]
    
class StudentCoursesListResponse(BaseModel):
    student_id: UUID
    course_id: UUID
    last_accessed: str
    completed_lessons: int
    time_spent: str
    assignments_done: int
class CreateCourseResponse(BaseModel):
    course_id: UUID
    courseID: str
    name: str
    professor_id: UUID
    start_date: str
    end_date: str
    status: str
    nCredit: int
    nSemester: int
    learning_outcomes: str
    image_url: str
    student_courses_list: List[StudentCoursesListResponse]
    
class PutLearningOutcomesCoursesRequest(BaseModel):
    learning_outcomes: list[str]
