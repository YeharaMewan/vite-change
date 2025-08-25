from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import json
import time
import asyncio

app = FastAPI(title="HR Agentic Application API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models for API requests
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

# In-memory storage for demo purposes
sessions_store = {}
messages_store = {}

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the HR Agentic Application API!"}

@app.post("/chat", tags=["Agent"])
async def chat_with_agent(request: ChatRequest):
    """
    Standard synchronous chat endpoint (non-streaming)
    """
    session_id = request.session_id or f"sess-{int(datetime.now().timestamp())}"
    
    # Store user message
    if session_id not in messages_store:
        messages_store[session_id] = []
    
    user_msg = {
        "role": "user",
        "content": request.query,
        "ts": datetime.now().isoformat()
    }
    messages_store[session_id].append(user_msg)
    
    # Simple mock response
    if "policy" in request.query.lower():
        response_text = "Here are our key HR policies: We offer flexible working hours, comprehensive health insurance, and 20 days of annual leave. Our dress code is business casual, and we have an open-door policy for feedback and concerns."
    elif "benefit" in request.query.lower():
        response_text = "Our employee benefits include: Health insurance (medical, dental, vision), 401k matching up to 5%, life insurance, flexible spending accounts, gym membership reimbursement, and professional development budget."
    elif "leave" in request.query.lower():
        response_text = "Leave Management: You can request time off through our HR portal. We offer vacation days, sick leave, personal days, and parental leave. Please submit requests at least 2 weeks in advance when possible."
    elif "performance" in request.query.lower():
        response_text = "Performance Reviews: We conduct annual performance reviews with quarterly check-ins. Reviews focus on goal achievement, professional development, and feedback. Self-assessments are due one week before your review meeting."
    else:
        response_text = f"Thank you for your question about '{request.query}'. I'm here to help with HR-related queries including policies, benefits, leave management, and performance reviews. How else can I assist you?"
    
    # Store assistant response
    assistant_msg = {
        "role": "assistant",
        "content": response_text,
        "ts": datetime.now().isoformat()
    }
    messages_store[session_id].append(assistant_msg)
    
    return JSONResponse(content={"response": response_text})

@app.post("/chat/stream", tags=["Agent"])
async def chat_with_agent_stream(request: ChatRequest):
    """
    Streaming chat endpoint with real-time responses
    """
    session_id = request.session_id or f"sess-{int(datetime.now().timestamp())}"
    
    # Store user message
    if session_id not in messages_store:
        messages_store[session_id] = []
    
    user_msg = {
        "role": "user",
        "content": request.query,
        "ts": datetime.now().isoformat()
    }
    messages_store[session_id].append(user_msg)
    
    async def generate_streaming_response():
        # Simple mock response
        if "policy" in request.query.lower():
            response_text = "Here are our key HR policies: We offer flexible working hours, comprehensive health insurance, and 20 days of annual leave. Our dress code is business casual, and we have an open-door policy for feedback and concerns."
        elif "benefit" in request.query.lower():
            response_text = "Our employee benefits include: Health insurance (medical, dental, vision), 401k matching up to 5%, life insurance, flexible spending accounts, gym membership reimbursement, and professional development budget."
        elif "leave" in request.query.lower():
            response_text = "Leave Management: You can request time off through our HR portal. We offer vacation days, sick leave, personal days, and parental leave. Please submit requests at least 2 weeks in advance when possible."
        elif "performance" in request.query.lower():
            response_text = "Performance Reviews: We conduct annual performance reviews with quarterly check-ins. Reviews focus on goal achievement, professional development, and feedback. Self-assessments are due one week before your review meeting."
        else:
            response_text = f"Thank you for your question about '{request.query}'. I'm here to help with HR-related queries including policies, benefits, leave management, and performance reviews. How else can I assist you?"
        
        # Stream the response word by word
        words = response_text.split()
        for i, word in enumerate(words):
            if i == 0:
                yield f"data: {json.dumps({'content': word})}\n\n"
            else:
                yield f"data: {json.dumps({'content': ' ' + word})}\n\n"
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
        
        # Store assistant response
        assistant_msg = {
            "role": "assistant", 
            "content": response_text,
            "ts": datetime.now().isoformat()
        }
        messages_store[session_id].append(assistant_msg)
        
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# ------ Sessions API for frontend history ------
@app.get("/sessions", tags=["Sessions"])
async def list_sessions(limit: int = 50):
    """List recent session ids."""
    session_ids = list(messages_store.keys())[-limit:]
    return {"sessions": session_ids}

@app.get("/sessions/{session_id}", tags=["Sessions"])
async def get_session_messages(session_id: str, limit: int = 100):
    """Return recent messages for a given session."""
    if session_id not in messages_store:
        return {"session_id": session_id, "messages": []}
    
    messages = messages_store[session_id][-limit:]
    return {
        "session_id": session_id,
        "messages": messages,
    }

@app.post("/sessions", tags=["Sessions"])
async def create_session(session_id: Optional[str] = None):
    """Create a session explicitly; if session_id omitted, use current timestamp."""
    sid = session_id or f"sess-{int(datetime.now().timestamp())}"
    if sid not in messages_store:
        messages_store[sid] = []
        sessions_store[sid] = {
            "created_at": datetime.now().isoformat(),
            "title": "New Conversation"
        }
        return {"session_id": sid, "created": True}
    return {"session_id": sid, "created": False}

@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Delete a session and its messages."""
    if session_id not in messages_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del messages_store[session_id]
    if session_id in sessions_store:
        del sessions_store[session_id]
    
    return {"deleted": True}

@app.delete("/sessions", tags=["Sessions"])
async def delete_all_sessions():
    """Delete all sessions and messages."""
    messages_store.clear()
    sessions_store.clear()
    return {"deleted_all": True}