from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from agent import SHLAssessmentAgent

# Initialize FastAPI app
app = FastAPI(title="SHL Assessment Agent", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = SHLAssessmentAgent(catalog_path="shl_catalog_master.json")

# ============ PYDANTIC MODELS ============

class Message(BaseModel):
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="Full conversation history")

class Recommendation(BaseModel):
    name: str = Field(..., description="Assessment name")
    url: str = Field(..., description="SHL catalog URL")
    test_type: str = Field(..., description="Assessment type")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Agent's response")
    recommendations: List[Recommendation] = Field(default=[], description="List of recommendations (0-10 items)")
    end_of_conversation: bool = Field(False, description="True when task is complete")

# ============ ENDPOINTS ============

@app.get("/health")
async def health_check():
    return {"status": "ok", "assessments_loaded": agent.retriever.count()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for SHL assessment recommendations."""
    try:
        # Get last user message
        last_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_message = msg.content
                break
        
        if not last_message:
            return ChatResponse(
                reply="I'm here to help with SHL assessment recommendations. What role are you hiring for?",
                recommendations=[],
                end_of_conversation=False
            )
        
        # Convert conversation history to dict format for agent
        conversation_history = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.messages[:-1]  # Exclude current message
        ]
        
        # Call agent's process method with correct parameters
        result = agent.process(last_message, conversation_history)
        
        # Format recommendations
        recommendations = [
            Recommendation(
                name=rec["name"],
                url=rec["url"],
                test_type=rec["test_type"]
            )
            for rec in result.get("recommendations", [])
        ]
        
        return ChatResponse(
            reply=result["reply"],
            recommendations=recommendations,
            end_of_conversation=result.get("end_of_conversation", False)
        )
        
    except Exception as e:
        print(f"Error in chat_endpoint: {e}")
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            reply="I encountered an error. Please rephrase your request about SHL assessments.",
            recommendations=[],
            end_of_conversation=False
        )

@app.get("/")
async def root():
    return {
        "service": "SHL Assessment Agent",
        "version": "2.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Conversational agent",
            "GET /catalog": "View all assessments"
        },
        "assessments_loaded": agent.retriever.count()
    }

@app.get("/catalog")
async def get_catalog(limit: int = 20):
    assessments = agent.retriever.get_all()
    return {
        "total": len(assessments),
        "assessments": [
            {
                "id": a.get('id') or a.get('entity_id'),
                "name": a.get('name'),
                "type": a.get('test_type'),
                "url": a.get('link') or a.get('url')
            }
            for a in assessments[:limit]
        ]
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)