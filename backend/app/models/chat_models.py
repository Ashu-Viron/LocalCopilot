"""Pydantic models for chat operations."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Represents a single chat message."""
    
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "role": "user",
                "content": "Fix the login bug",
                "timestamp": "2026-01-19T10:30:00"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    include_logs: bool = Field(True, description="Include tool execution logs in response")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What files are in the src directory?",
                "conversation_id": "conv_123",
                "include_logs": True
            }
        }


class PlanStep(BaseModel):
    """Represents a single step in the agent's plan."""
    
    step_number: int = Field(..., description="Step number in the plan")
    action: str = Field(..., description="Action to perform")
    tool: Optional[str] = Field(None, description="Tool to use")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    expected_output: Optional[str] = Field(None, description="Expected outcome")


class Plan(BaseModel):
    """AI agent's execution plan."""
    
    reasoning: str = Field(..., description="Why this plan was created")
    steps: List[PlanStep] = Field(..., description="Steps to execute")
    estimated_time: Optional[float] = Field(None, description="Estimated execution time in seconds")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    id: str = Field(..., description="Response ID")
    conversation_id: str = Field(..., description="Conversation ID")
    message: str = Field(..., description="Assistant response")
    plan: Optional[Plan] = Field(None, description="Execution plan if applicable")
    tool_logs: List[str] = Field(default_factory=list, description="Tool execution logs")
    has_file_changes: bool = Field(False, description="Whether files were modified")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "resp_123",
                "conversation_id": "conv_123",
                "message": "I found and fixed the login bug...",
                "plan": None,
                "tool_logs": ["Executed: ls src/"],
                "has_file_changes": True,
                "timestamp": "2026-01-19T10:31:00"
            }
        }


class Conversation(BaseModel):
    """Represents a chat conversation."""
    
    id: str = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    messages: List[Message] = Field(default_factory=list, description="Chat messages")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "conv_123",
                "title": "Login Feature Development",
                "messages": [
                    {"role": "user", "content": "Help me fix the login"},
                    {"role": "assistant", "content": "I'll analyze the auth.js file..."}
                ],
                "created_at": "2026-01-19T10:00:00",
                "updated_at": "2026-01-19T10:31:00"
            }
        }
