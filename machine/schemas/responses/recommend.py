from uuid import UUID
from pydantic import BaseModel
from typing import List, Union
from core.repository.enum import StatusType, DifficultyLevel
from typing import Optional

class DocumentResponse(BaseModel):
    id: UUID
    name: str


class QuizQuestionResponse(BaseModel):
    id: UUID
    question_text: str
    question_type: str
    image: Optional[str] = None
    options: List[str] 
    correct_answer: List[str] 
    difficulty: DifficultyLevel
    points: float 
    explanation: str
    user_choice: Optional[Union[str, List[str]]] = None

class QuizExerciseResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: StatusType
    score: Optional[float] = None  
    max_score: float
    time_limit: Optional[int] = None
    duration: Optional[int] = None
    questions: List[QuizQuestionResponse]

class QuizListResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: StatusType
    score:  Optional[float] = None
    max_score: float
    time_limit: Optional[int] = None
    duration: Optional[int] = None  
    question_count: int
   
class ModuleResponse(BaseModel):
    module_id: UUID
    title: str
    progress: int
    objectives: List[str]
    
class ModuleQuizResponse(BaseModel):
    module_id: UUID
    title: str
    objectives: List[str]
    quizzes: List[QuizListResponse]
    

class RecommendLessonResponse(BaseModel):
    id: UUID
    title: str
    learning_outcomes: Optional[List[str]] = None
    description: Optional[str] = None
    progress: int
    status: str
    recommend_content: Optional[str] = None
    explain: Optional[str] = None
    modules: List[ModuleResponse]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_notes: Optional[str] = None
