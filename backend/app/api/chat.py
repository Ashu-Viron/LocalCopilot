"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List, AsyncGenerator
import uuid
import json

from sqlalchemy.orm import Session

from app.models.chat_models import ChatRequest, ChatResponse, Conversation, Message
from app.agent.orchestrator import agent
from app.agent.memory import memory_manager
from app.database.connection import get_db, SessionLocal
from app.database.repository import ConversationRepository
from app.utils.logger import logger

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_repo():
    """Get repository with a new database session."""
    db = SessionLocal()
    try:
        return ConversationRepository(db)
    except Exception:
        db.close()
        raise


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI agent.
    
    Args:
        request: Chat request with message
        
    Returns:
        ChatResponse with assistant response
    """
    try:
        response = await agent.process_message(request)
        
        # Persist to database
        try:
            repo = get_repo()
            repo.add_message(response.conversation_id, "user", request.message)
            repo.add_message(response.conversation_id, "assistant", response.message)
            repo.db.close()
        except Exception as e:
            logger.warning(f"Failed to persist message to database: {e}")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/stream")
async def send_message_stream(request: ChatRequest):
    """
    Send a message to the AI agent with streaming response.
    
    Args:
        request: Chat request with message
        
    Returns:
        Server-Sent Events stream with response chunks
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        conversation_id = request.conversation_id
        has_file_changes = False
        
        try:
            # Send thinking status first
            yield f"data: {json.dumps({'type': 'status', 'content': 'thinking'})}\n\n"
            
            async for chunk in agent.process_message_stream(request, conversation_id):
                if chunk.get('type') == 'conversation_id':
                    conversation_id = chunk.get('content')
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get('type') == 'chunk':
                    full_response += chunk.get('content', '')
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get('type') == 'file_change':
                    has_file_changes = True
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get('type') == 'tool_log':
                    yield f"data: {json.dumps(chunk)}\n\n"
                elif chunk.get('type') == 'done':
                    # Persist to database
                    try:
                        repo = get_repo()
                        repo.add_message(conversation_id, "user", request.message)
                        repo.add_message(conversation_id, "assistant", full_response)
                        repo.db.close()
                    except Exception as e:
                        logger.warning(f"Failed to persist message to database: {e}")
                    
                    yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id, 'has_file_changes': has_file_changes})}\n\n"
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/conversation", response_model=dict)
async def create_conversation() -> dict:
    """
    Create a new conversation.
    
    Returns:
        Dict with conversation ID
    """
    conversation_id = str(uuid.uuid4())
    memory_manager.create_conversation(conversation_id)
    
    # Persist to database
    try:
        repo = get_repo()
        repo.create_conversation(conversation_id)
        repo.db.close()
    except Exception as e:
        logger.warning(f"Failed to persist conversation to database: {e}")
    
    return {"conversation_id": conversation_id}


@router.get("/conversations", response_model=list)
async def list_conversations() -> list:
    """
    List all active conversations.
    
    Returns:
        List of conversation summaries
    """
    try:
        # Try to load from database first
        repo = get_repo()
        db_conversations = repo.list_conversations()
        result = [repo.to_dict(conv) for conv in db_conversations]
        repo.db.close()
        
        if result:
            return result
    except Exception as e:
        logger.warning(f"Failed to load conversations from database: {e}")
    
    # Fallback to memory
    return memory_manager.list_conversations()


@router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str) -> Conversation:
    """
    Get conversation details with full message history.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Conversation object with messages
    """
    repo = None
    try:
        # Try to load from database first
        repo = get_repo()
        db_conv = repo.get_conversation(conversation_id)
        if db_conv:
            # Convert to API model while session is still open
            messages = [
                Message(role=m.role, content=m.content, timestamp=m.created_at)
                for m in db_conv.messages
            ]
            result = Conversation(
                id=db_conv.id,
                title=db_conv.title or f"Conversation {db_conv.id[:8]}",
                messages=messages,
                created_at=db_conv.created_at,
                updated_at=db_conv.updated_at,
            )
            
            logger.info(f"Loaded conversation {conversation_id} from DB with {len(messages)} messages")
            
            # Also populate memory for active use
            memory = memory_manager.get_or_create_conversation(conversation_id)
            if len(memory.messages) == 0:
                for msg in messages:
                    memory.add_message(msg.role, msg.content)
            
            return result
    except Exception as e:
        logger.warning(f"Failed to load conversation from database: {e}")
    finally:
        if repo:
            repo.db.close()
    
    # Fallback to memory
    memory = memory_manager.get_conversation(conversation_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return memory.get_conversation_object()


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    # Delete from memory
    memory_manager.delete_conversation(conversation_id)
    
    # Delete from database
    try:
        repo = get_repo()
        repo.delete_conversation(conversation_id)
        repo.db.close()
    except Exception as e:
        logger.warning(f"Failed to delete conversation from database: {e}")
    
    return {"message": "Conversation deleted"}


@router.post("/conversation/{conversation_id}/message", response_model=ChatResponse)
async def send_conversation_message(
    conversation_id: str,
    request: ChatRequest
) -> ChatResponse:
    """
    Send a message in a specific conversation.
    
    Args:
        conversation_id: Conversation ID
        request: Chat request
        
    Returns:
        ChatResponse
    """
    # Ensure conversation exists in memory (load from DB if needed)
    memory = memory_manager.get_conversation(conversation_id)
    if not memory:
        # Try to load from database
        try:
            repo = get_repo()
            db_conv = repo.get_conversation(conversation_id)
            if db_conv:
                memory = memory_manager.get_or_create_conversation(conversation_id)
                for msg in repo.get_messages(conversation_id):
                    memory.add_message(msg.role, msg.content)
            repo.db.close()
        except Exception as e:
            logger.warning(f"Failed to load conversation from database: {e}")
    
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    try:
        response = await agent.process_message(request, conversation_id)
        
        # Persist to database
        try:
            repo = get_repo()
            repo.add_message(conversation_id, "user", request.message)
            repo.add_message(conversation_id, "assistant", response.message)
            repo.db.close()
        except Exception as e:
            logger.warning(f"Failed to persist message to database: {e}")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str) -> dict:
    """
    Get conversation summary.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Summary dict
    """
    memory = memory_manager.get_conversation(conversation_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "summary": memory.get_summary(),
        "message_count": len(memory.get_history()),
        "created_at": memory.created_at
    }

