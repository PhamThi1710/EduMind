from uuid import uuid4
from core.db import Base
from sqlalchemy.orm import relationship
from core.db.mixins import TimestampMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean, Date


class Users(Base, TimestampMixin):
    """
    Unified user table.
    id = Supabase Auth UUID (no default — must be set explicitly from Supabase sub).
    role: "user" (default) or "admin".
    """
    __tablename__ = "users"

    id = Column(UUID, primary_key=True)  # Supabase Auth UUID — must be provided explicitly
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(String(20), default="user", nullable=False)  # "user" or "admin"
    date_of_birth = Column(Date, nullable=True)
    student_id_number = Column(String(20), nullable=True)   # mssv (for students)
    employee_id_number = Column(String(20), nullable=True)  # mscb (for professors)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    courses = relationship("Courses", back_populates="owner", foreign_keys="Courses.owner_id")
    learning_paths = relationship("LearningPaths", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
