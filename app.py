from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

# ... (your existing imports and agent initialization)

# --- Pydantic Models ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    reply: str
    recommendations: list = []
    end_of_conversation: bool = False

# --- FastAPI App ---
app = FastAPI(title="SHL Assessment Agent")

# --- The corrected endpoint ---
@app.post("/chat", response_model=ChatResponse)  # <-- MUST be @app.post, NOT @app.get
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for SHL assessment recommendations."""
    try:
        # Convert Pydantic model to dict for your agent
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Call your agent's process method
        result = agent.process(messages)  # Adjust based on your agent's interface
        
        return ChatResponse(
            reply=result["reply"],
            recommendations=result.get("recommendations", []),
            end_of_conversation=result.get("end_of_conversation", False)
        )
    except Exception as e:
        print(f"Error: {e}")
        return ChatResponse(
            reply="I encountered an error. Please rephrase your request.",
            recommendations=[],
            end_of_conversation=False
        )