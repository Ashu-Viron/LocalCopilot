"""SQLAlchemy models for database tables."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class ConversationDB(Base):
    """Conversation table model."""
    
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to messages
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan", order_by="MessageDB.created_at")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"


class MessageDB(Base):
    """Message table model."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to conversation
    conversation = relationship("ConversationDB", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
