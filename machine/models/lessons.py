from uuid import uuid4
from core.db import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy import Column, String, ForeignKey, Integer

class Lessons(Base):
    __tablename__ = "lessons"

    id = Column(UUID, primary_key=True, default=uuid4)
    course_id = Column(UUID, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)  
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    order = Column(Integer, nullable=False) 
    learning_outcomes = Column(ARRAY(String), nullable=True)

    course = relationship("Courses", back_populates="lessons")
    documents = relationship("Documents", back_populates="lesson") 
    recommend_lesson = relationship("RecommendLessons", back_populates="lesson")
