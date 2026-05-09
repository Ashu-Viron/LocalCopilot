"""Database repository for conversations and messages."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.database.models import ConversationDB, MessageDB
from app.models.chat_models import Message, Conversation
from app.utils.logger import logger


class ConversationRepository:
    """Repository for conversation operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, conversation_id: str, title: Optional[str] = None) -> ConversationDB:
        """Create a new conversation."""
        try:
            conversation = ConversationDB(
                id=conversation_id,
                title=title,
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            logger.info(f"Created conversation in DB: {conversation_id}")
            return conversation
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationDB]:
        """Get a conversation by ID with all messages eagerly loaded."""
        return (
            self.db.query(ConversationDB)
            .options(joinedload(ConversationDB.messages))
            .filter(ConversationDB.id == conversation_id)
            .first()
        )
    
    def list_conversations(self, limit: int = 50) -> List[ConversationDB]:
        """List all active conversations with messages."""
        return (
            self.db.query(ConversationDB)
            .options(joinedload(ConversationDB.messages))
            .filter(ConversationDB.is_active == True)
            .order_by(ConversationDB.updated_at.desc())
            .limit(limit)
            .all()
        )
    
    def update_conversation_title(self, conversation_id: str, title: str) -> Optional[ConversationDB]:
        """Update conversation title."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(conversation)
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete a conversation."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.is_active = False
            self.db.commit()
            return True
        return False
    
    def add_message(self, conversation_id: str, role: str, content: str) -> MessageDB:
        """Add a message to a conversation."""
        try:
            # Ensure conversation exists
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                conversation = self.create_conversation(conversation_id)
            
            message = MessageDB(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )
            self.db.add(message)
            
            # Update conversation's updated_at
            conversation.updated_at = datetime.utcnow()
            
            # Auto-generate title from first user message
            if role == "user" and not conversation.title:
                title = self._generate_title(content)
                conversation.title = title
            
            self.db.commit()
            self.db.refresh(message)
            logger.debug(f"Added message to conversation {conversation_id}")
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message: {e}")
            raise
    
    def get_messages(self, conversation_id: str) -> List[MessageDB]:
        """Get all messages for a conversation."""
        return (
            self.db.query(MessageDB)
            .filter(MessageDB.conversation_id == conversation_id)
            .order_by(MessageDB.created_at.asc())
            .all()
        )
    
    def _generate_title(self, content: str) -> str:
        """Generate a title from message content."""
        title = content.strip()
        title = title.replace('```', '').replace('`', '').replace('#', '')
        title = title.split('\n')[0].strip()
        if len(title) > 50:
            title = title[:47] + '...'
        return title if title else "New conversation"
    
    def to_conversation_model(self, conv_db: ConversationDB) -> Conversation:
        """Convert DB model to API model."""
        messages = [
            Message(role=m.role, content=m.content, timestamp=m.created_at)
            for m in conv_db.messages
        ]
        return Conversation(
            id=conv_db.id,
            title=conv_db.title or f"Conversation {conv_db.id[:8]}",
            messages=messages,
            created_at=conv_db.created_at,
            updated_at=conv_db.updated_at,
        )
    
    def to_dict(self, conv_db: ConversationDB) -> Dict[str, Any]:
        """Convert DB model to dictionary."""
        return {
            "id": conv_db.id,
            "title": conv_db.title or f"Conversation {conv_db.id[:8]}",
            "created_at": conv_db.created_at.isoformat() if conv_db.created_at else None,
            "updated_at": conv_db.updated_at.isoformat() if conv_db.updated_at else None,
            "message_count": len(conv_db.messages) if conv_db.messages else 0,
        }
