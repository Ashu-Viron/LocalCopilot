"""Memory management for conversations."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import json

from app.models.chat_models import Message, Conversation
from app.utils.logger import logger


class ConversationMemory:
    """Manages conversation history and context."""
    
    def __init__(self, conversation_id: str, max_history: int = 100):
        """
        Initialize conversation memory.
        
        Args:
            conversation_id: Unique conversation ID
            max_history: Maximum messages to keep in memory
        """
        self.conversation_id = conversation_id
        self.max_history = max_history
        self.messages: deque = deque(maxlen=max_history)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
        self.title: Optional[str] = None
    
    def _generate_title_from_message(self, content: str) -> str:
        """
        Generate a title from the first user message.
        
        Args:
            content: Message content
            
        Returns:
            Generated title (max 50 chars)
        """
        # Clean and truncate the message
        title = content.strip()
        # Remove markdown, code blocks, etc.
        title = title.replace('```', '').replace('`', '').replace('#', '')
        # Get first line only
        title = title.split('\n')[0].strip()
        # Truncate to 50 chars
        if len(title) > 50:
            title = title[:47] + '...'
        return title if title else "New conversation"
    
    def add_message(self, role: str, content: str) -> Message:
        """
        Add a message to history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            
        Returns:
            Message object
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if role == "user" and self.title is None:
            self.title = self._generate_title_from_message(content)
            logger.debug(f"Auto-generated title: {self.title}")
        
        logger.debug(f"Added {role} message to conversation {self.conversation_id}")
        return message
    
    def add_user_message(self, content: str) -> Message:
        """Add user message."""
        return self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> Message:
        """Add assistant message."""
        return self.add_message("assistant", content)
    
    def get_history(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get message history.
        
        Args:
            limit: Optional limit on number of messages
            
        Returns:
            List of messages
        """
        messages = list(self.messages)
        if limit:
            return messages[-limit:]
        return messages
    
    def get_context(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM prompt.
        
        Args:
            max_tokens: Approximate token limit
            
        Returns:
            List of message dicts for LLM
        """
        context = []
        token_count = 0
        
        # Estimate 4 characters per token
        token_estimate_factor = 4
        
        for message in reversed(self.messages):
            message_tokens = len(message.content) // token_estimate_factor
            
            if token_count + message_tokens > max_tokens:
                break
            
            context.insert(0, {
                "role": message.role,
                "content": message.content
            })
            token_count += message_tokens
        
        return context
    
    def clear(self):
        """Clear all messages."""
        self.messages.clear()
        logger.info(f"Cleared memory for conversation {self.conversation_id}")
    
    def get_summary(self) -> str:
        """
        Get a summary of the conversation.
        
        Returns:
            Summary string
        """
        user_messages = [m for m in self.messages if m.role == "user"]
        assistant_messages = [m for m in self.messages if m.role == "assistant"]
        
        summary = f"Conversation {self.conversation_id}\n"
        summary += f"Created: {self.created_at}\n"
        summary += f"Total messages: {len(self.messages)}\n"
        summary += f"User messages: {len(user_messages)}\n"
        summary += f"Assistant messages: {len(assistant_messages)}\n"
        
        return summary
    
    def get_conversation_object(self, title: Optional[str] = None) -> Conversation:
        """
        Get Conversation model object.
        
        Args:
            title: Optional conversation title (overrides auto-generated)
            
        Returns:
            Conversation object
        """
        return Conversation(
            id=self.conversation_id,
            title=title or self.title or f"Conversation {self.conversation_id[:8]}",
            messages=list(self.messages),
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class MemoryManager:
    """Manages multiple conversations."""
    
    def __init__(self):
        """Initialize memory manager."""
        self.conversations: Dict[str, ConversationMemory] = {}
    
    def create_conversation(self, conversation_id: str) -> ConversationMemory:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Unique ID for conversation
            
        Returns:
            ConversationMemory object
        """
        if conversation_id in self.conversations:
            logger.warning(f"Conversation {conversation_id} already exists")
            return self.conversations[conversation_id]
        
        memory = ConversationMemory(conversation_id)
        self.conversations[conversation_id] = memory
        logger.info(f"Created conversation {conversation_id}")
        return memory
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """
        Get existing conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ConversationMemory or None
        """
        return self.conversations.get(conversation_id)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """Get list of active conversations with metadata."""
        result = []
        for conv_id, memory in self.conversations.items():
            result.append({
                "id": conv_id,
                "title": memory.title or f"Conversation {conv_id[:8]}",
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
                "message_count": len(memory.messages)
            })
        # Sort by updated_at descending
        result.sort(key=lambda x: x["updated_at"], reverse=True)
        return result
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False
    
    def get_or_create_conversation(self, conversation_id: str) -> ConversationMemory:
        """
        Get conversation or create if doesn't exist.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ConversationMemory object
        """
        if conversation_id not in self.conversations:
            return self.create_conversation(conversation_id)
        return self.conversations[conversation_id]


# Global memory manager instance
memory_manager = MemoryManager()
