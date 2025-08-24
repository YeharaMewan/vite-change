from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

# Import the compiled HR agent system
from app.agents import hr_agent_system
from app.memory_manager import MemoryManager
from app.streaming_endpoint import chat_stream_endpoint
from datetime import datetime
from fastapi import HTTPException
from typing import Optional

app = FastAPI(title="HR Agentic Application API")
memory = MemoryManager()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the HR Agentic Application API!"}

@app.post("/chat", tags=["Agent"])
async def chat_with_agent(query: str, session_id: Optional[str] = None):
    """
    Standard synchronous chat endpoint (non-streaming)
    """
    return await _chat_sync(query, session_id)

@app.post("/chat/stream", tags=["Agent"])
async def chat_with_agent_stream(query: str, session_id: Optional[str] = None):
    """
    Streaming chat endpoint with real-time responses
    """
    return await chat_stream_endpoint(query, session_id)

async def _chat_sync(query: str, session_id: Optional[str] = None):
    """
    Internal synchronous chat function
    """
    try:
        sid = session_id or "default"

        # Store user message in memory
        memory.add_message(sid, "user", query, {"ts": datetime.now().isoformat()})

        # Gather context from memory
        ctx = memory.get_context(sid)

        # Create context string from recent messages
        context_snippet = ""
        if ctx:
            context_snippet = "Recent conversation context:\n" + "\n".join(
                [f"- {m.get('role')}: {m.get('content')[:120]}..." for m in ctx[-3:]]
            )

        # Prepare the user message with context
        user_content = query
        if context_snippet:
            user_content = f"{context_snippet}\n\nCurrent question: {query}"

        # Define the initial state for the supervisor system
        initial_state = {
            "messages": [HumanMessage(content=user_content)]
        }
        
        # Invoke the HR agent system
        response = hr_agent_system.invoke(initial_state)
        
        # Extract the final response
        final_message = response["messages"][-1]
        response_text = final_message.content

        # Store assistant response in memory
        memory.add_message(sid, "assistant", response_text, {"ts": datetime.now().isoformat()})

        return JSONResponse(content={"response": response_text})
        
    except Exception as e:
        # Return a more descriptive error to the frontend
        print(f"Error during agent invocation: {e}")  # Log error to backend console
        return JSONResponse(content={"error": f"Agent Error: {e}"}, status_code=500)


# ------ Sessions API for frontend history ------
@app.get("/sessions", tags=["Sessions"])
async def list_sessions(limit: int = 50):
    """List recent session ids (simple heuristic from stored memories)."""
    from app.memory import ConversationMemory
    from app.database import SessionLocal

    with SessionLocal() as db:
        rows = (
            db.query(ConversationMemory.session_id)
            .order_by(ConversationMemory.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"sessions": [r[0] for r in rows]}


@app.get("/sessions/{session_id}", tags=["Sessions"])
async def get_session_messages(session_id: str, limit: int = 100):
    """Return recent messages for a given session."""
    from app.memory import ConversationMemory, MemoryMessage
    from app.database import SessionLocal

    with SessionLocal() as db:
        mem = db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id).first()
        if not mem:
            return {"session_id": session_id, "messages": []}
        msgs = (
            db.query(MemoryMessage)
            .filter(MemoryMessage.memory_id == mem.id)
            .order_by(MemoryMessage.timestamp.asc())
            .limit(limit)
            .all()
        )
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": m.role, 
                    "content": m.content, 
                    "ts": m.timestamp.isoformat() if m.timestamp else ""
                } for m in msgs
            ],
        }


@app.post("/sessions", tags=["Sessions"])
async def create_session(session_id: Optional[str] = None):
    """Create a session explicitly; if session_id omitted, use current timestamp."""
    from app.memory import ConversationMemory
    from app.database import SessionLocal
    sid = session_id or f"sess-{int(datetime.now().timestamp())}"
    with SessionLocal() as db:
        exists = db.query(ConversationMemory).filter(ConversationMemory.session_id == sid).first()
        if exists:
            return {"session_id": sid, "created": False}
        mem = ConversationMemory(
            session_id=sid, 
            key_points=[], 
            user_preferences={}, 
            context_window=[]
        )
        db.add(mem)
        db.commit()
        return {"session_id": sid, "created": True}


@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Delete a session and its messages."""
    from app.memory import ConversationMemory
    from app.database import SessionLocal

    with SessionLocal() as db:
        mem = db.query(ConversationMemory).filter(ConversationMemory.session_id == session_id).first()
        if not mem:
            raise HTTPException(status_code=404, detail="Session not found")
        db.delete(mem)
        db.commit()
        return {"deleted": True}


@app.delete("/sessions", tags=["Sessions"])
async def delete_all_sessions():
    """Delete all sessions and messages."""
    from app.memory import ConversationMemory
    from app.database import SessionLocal

    with SessionLocal() as db:
        db.query(ConversationMemory).delete()
        db.commit()
        return {"deleted_all": True}