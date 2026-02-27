from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from core.repository.enum import *
from datetime import date


class MemberInfo(BaseModel):
    user_id: UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

class OwnerInformation(BaseModel):
    owner_id: UUID
    owner_name: str
    owner_email: str
    owner_avatar: Optional[str] = None

class GetCoursesResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    image_url: Optional[str] = None

    learning_outcomes: Optional[List[str]] = None
    status: StatusType
    is_owner: bool = False
    members_count: int = 0

class GetCoursesPaginatedResponse(BaseModel):
    content: List[GetCoursesResponse]
    currentPage: int
    pageSize: int
    totalRows: int
    totalPages: int
    
class GetAdminCoursesResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: StatusType

    owner_name: Optional[str] = None
    members_count: int = 0
    
class GetAdminCoursesPaginatedResponse(BaseModel):
    content: List[GetAdminCoursesResponse]
    currentPage: int
    pageSize: int
    totalRows: int
    totalPages: int
    
class GetDocumentsResponse(BaseModel):
    id: UUID
    name: str
    type: DocumentType
    url: str

class GetExercisesResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    status: Optional[StatusType] = None
    type: ExerciseType

class GetCourseDetailResponse(BaseModel):
    course_id: UUID
    course_name: str
    course_description: Optional[str] = None
    course_start_date: Optional[str] = None
    course_end_date: Optional[str] = None
    course_learning_outcomes: Optional[List[str]] = None
    course_status: str
    course_image: Optional[str] = None

    is_owner: bool = False
    members_count: int = 0
    nDocuments: int = 0
    nExercises: int = 0

class PutLearningOutcomesCoursesResponse(BaseModel):
    course_id: UUID
    learning_outcomes: list[str]

class GetDocumentsProfessor(BaseModel):
    id: UUID
    name: str
    type: str
    url: str

class GetCourseDetailProfessorResponse(BaseModel):
    course_id: UUID
    course_name: str
    course_description: Optional[str] = None
    course_start_date: Optional[str] = None
    course_end_date: Optional[str] = None
    course_learning_outcomes: Optional[List[str]] = None
    course_status: StatusType
    course_image_url: Optional[str] = None

    members_count: int = 0
    nExercises: int = 0
    nDocuments: int = 0

class ModuleResponse(BaseModel):
    module_id: UUID
    title: str
    progress: int
    objectives: List[str]
