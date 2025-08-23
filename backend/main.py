from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

# Import the compiled agent executor from the 'app' package
from app.agent import agent_executor, AgentState
from app.memory_manager import MemoryManager
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
    Receives a user query and returns the agent's response.
    """
    try:
        sid = session_id or "default"

        # store user message
        memory.add_message(sid, "user", query, {"ts": datetime.now().isoformat()})

        # gather context
        ctx = memory.get_context(sid)

        # Define the initial state for the graph
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "session_id": sid,
            "memory_context": ctx,
            "user_preferences": {},
        }
        
        # Invoke the agent graph asynchronously
        response_stream = agent_executor.astream(initial_state)
        
        final_response = None
        async for event in response_stream:
            if "agent" in event:
                # The final message from the agent after the loop
                final_response = event["agent"]["messages"][-1]

        if final_response:
             response_text = final_response.content
        else:
            response_text = "The agent could not process the request."

        return JSONResponse(content={"response": response_text})
    except Exception as e:
        # Return a more descriptive error to the frontend
        print(f"Error during agent invocation: {e}") # Log error to backend console
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
            "messages": [{"role": m.role, "content": m.content, "ts": m.timestamp.isoformat() if m.timestamp else ""} for m in msgs],
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
        mem = ConversationMemory(session_id=sid, key_points=[], user_preferences={}, context_window=[])
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