from uuid import uuid4
from core.db import Base
from sqlalchemy.orm import relationship
from core.db.mixins import TimestampMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, UUID, DateTime, Boolean, func

class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    mssv = Column(String(10), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    fullname = Column(String(255), nullable=True)
    
    is_email_verified = Column(Boolean, default=False, nullable=False) 
    verification_code = Column(String(6), nullable=True) 
    verification_code_expires_at = Column(DateTime, nullable=True) 

    password_reset_code = Column(String(6), nullable=True) 
    password_reset_code_expires_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)  
    
    activities = relationship("Activities", back_populates="student")
    student_courses = relationship("StudentCourses", back_populates="student")
    student_lessons = relationship("StudentLessons", back_populates="student")
    student_exercises = relationship("StudentExercises", back_populates="student")
    learning_paths = relationship("LearningPaths", back_populates="student")
