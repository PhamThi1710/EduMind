from uuid import UUID
from pydantic import BaseModel
from typing import List
from core.repository.enum import *

class StudentList(BaseModel):
    student_id: UUID
    student_name: str
    student_email: str

class ProfessorInformation(BaseModel):
    professor_id: UUID
    professor_name: str
    professor_email: str
class GetCoursesResponse(BaseModel):
    id: UUID
    name: str
    start_date: str
    end_date: str
    student_list: List[StudentList]
    learning_outcomes: List[str]
    professor: ProfessorInformation
    status: StatusType
    image: str
    percentage_complete: str
    last_accessed: str
 
class GetCoursesPaginatedResponse(BaseModel):
    content: List[GetCoursesResponse]
    currentPage: int
    pageSize: int
    totalRows: int
    totalPages: int

class GetExercisesResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: StatusType
    type: ExerciseType
class GetLessonsResponse(BaseModel):
    id: UUID
    title: str
    description: str 
    lesson_type: LessonType
    bookmark: bool
    order: int
    status: StatusType
    exercises: List[GetExercisesResponse]
class GetCourseDetailResponse(BaseModel):
    course_id: UUID
    student_id: UUID
    completed_lessons: int
    time_spent:str 
    assignments_done: int
    lessons: List[GetLessonsResponse]
    
class BookmarkLessonResponse(BaseModel):
    lesson_id: UUID
    student_id: UUID
    course_id: UUID