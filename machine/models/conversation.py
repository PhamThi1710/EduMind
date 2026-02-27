from uuid import uuid4
from core.db import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func


class Conversation(Base):
    """Stores AI tutor conversation sessions."""
    __tablename__ = "conversations"

    id = Column(UUID, primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="select")


class Message(Base):
    """Stores individual messages within a Conversation."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(UUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False)     # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
