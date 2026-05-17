"""FastAPI application for SHL Assessment Agent."""
import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, Message
from agent import SHLAssessmentAgent

# Initialize FastAPI
app = FastAPI(
    title="SHL Assessment Agent",
    description="Conversational agent for SHL assessment recommendations",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent with your JSON file
AGENT = SHLAssessmentAgent(catalog_path="shl_catalog_master.json")


@app.get("/health")
async def health_check():
    """Health check endpoint - required for Render."""
    return {
        "status": "ok",
        "assessments_loaded": AGENT.retriever.count()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Args:
        request: Chat request with conversation history
        
    Returns:
        Chat response with reply and recommendations
    """
    try:
        if not request.messages:
            return ChatResponse(
                reply="Hello! I'm the SHL Assessment Agent. I can help you find assessments for your hiring needs. What role are you hiring for?",
                recommendations=[],
                end_of_conversation=False
            )
        
        # Get last user message
        last_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_message = msg.content
                break
        
        if not last_message:
            return ChatResponse(
                reply="I'm here to help with SHL assessment recommendations. Could you tell me about the role you're hiring for?",
                recommendations=[],
                end_of_conversation=False
            )
        
        # Convert history to dict format
        history = [{"role": m.role, "content": m.content} for m in request.messages[:-1]]
        
        # Process message
        result = AGENT.process(last_message, history)
        
        return ChatResponse(
            reply=result['reply'],
            recommendations=result['recommendations'],
            end_of_conversation=result['end_of_conversation']
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return ChatResponse(
            reply="I encountered an issue. Please rephrase your request about SHL assessments.",
            recommendations=[],
            end_of_conversation=False
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SHL Assessment Agent",
        "version": "2.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Conversational agent",
            "GET /catalog": "View all assessments"
        },
        "assessments_loaded": AGENT.retriever.count()
    }


@app.get("/catalog")
async def get_catalog(limit: int = 20):
    """Get list of available assessments."""
    assessments = AGENT.retriever.get_all()
    return {
        "total": len(assessments),
        "assessments": [
            {
                "id": a['id'],
                "name": a['name'],
                "type": a['test_type'],
                "url": a['url']
            }
            for a in assessments[:limit]
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)