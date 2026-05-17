"""Pydantic models for request/response validation."""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="Message content", min_length=1)
    
    @validator('role')
    def validate_role(cls, v: str) -> str:
        if v not in ['user', 'assistant']:
            raise ValueError(f"Role must be 'user' or 'assistant', got '{v}'")
        return v


class ChatRequest(BaseModel):
    """Request model for /chat endpoint."""
    messages: List[Message] = Field(..., description="Full conversation history", min_items=1)


class Recommendation(BaseModel):
    """Assessment recommendation model."""
    name: str = Field(..., description="Assessment name from SHL catalog")
    url: str = Field(..., description="SHL catalog URL")
    test_type: str = Field(..., description="Assessment type/category")


class ChatResponse(BaseModel):
    """Response model - EXACT schema required by SHL."""
    reply: str = Field(..., description="Agent's response", min_length=1)
    recommendations: List[Recommendation] = Field(default=[], description="List of recommendations (0-10 items)")
    end_of_conversation: bool = Field(False, description="True when task is complete")
    
    @validator('recommendations')
    def validate_max_recommendations(cls, v: List[Recommendation]) -> List[Recommendation]:
        if len(v) > 10:
            raise ValueError(f"Maximum 10 recommendations allowed, got {len(v)}")
        return v