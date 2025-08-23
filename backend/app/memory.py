from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base, engine


class ConversationMemory(Base):
    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    conversation_summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    user_preferences = Column(JSON, nullable=True)
    context_window = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    messages = relationship(
        "MemoryMessage",
        back_populates="memory",
        cascade="all, delete-orphan",
    )


class MemoryMessage(Base):
    __tablename__ = "memory_messages"

    id = Column(Integer, primary_key=True)
    memory_id = Column(Integer, ForeignKey("conversation_memories.id"))
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata = Column(JSON, nullable=True)

    memory = relationship("ConversationMemory", back_populates="messages")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    language_preference = Column(String(10), default="en")
    communication_style = Column(String(50), default="formal")
    hr_topics_interest = Column(JSON, nullable=True)
    department = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Ensure tables are created on startup if they do not exist
Base.metadata.create_all(bind=engine)


