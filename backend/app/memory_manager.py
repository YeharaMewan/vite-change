from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .database import SessionLocal
from .memory import ConversationMemory, MemoryMessage


class MemoryManager:
    def __init__(self, max_context_length: int = 10):
        self.max_context_length = max_context_length

    def _get_or_create_memory(self, db: Session, session_id: str, user_id: Optional[str] = None) -> ConversationMemory:
        memory: Optional[ConversationMemory] = (
            db.query(ConversationMemory)
            .filter(ConversationMemory.session_id == session_id)
            .first()
        )
        if memory:
            return memory

        memory = ConversationMemory(
            session_id=session_id,
            user_id=user_id,
            key_points=[],
            user_preferences={},
            context_window=[],
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        with SessionLocal() as db:
            memory = self._get_or_create_memory(db, session_id)
            message = MemoryMessage(
                memory_id=memory.id,
                role=role,
                content=content,
                message_metadata=metadata or {},
            )
            db.add(message)
            db.commit()
            self._refresh_context_window(db, memory.id)

    def get_context(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            memory: Optional[ConversationMemory] = (
                db.query(ConversationMemory)
                .filter(ConversationMemory.session_id == session_id)
                .first()
            )
            if not memory:
                return []

            limit_val = limit or self.max_context_length
            recent_messages = (
                db.query(MemoryMessage)
                .filter(MemoryMessage.memory_id == memory.id)
                .order_by(MemoryMessage.timestamp.desc())
                .limit(limit_val)
                .all()
            )

            context: List[Dict[str, Any]] = []
            for m in reversed(recent_messages):
                context.append(
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else "",
                    }
                )
            return context

    def cleanup(self, days_old: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days_old)
        with SessionLocal() as db:
            old_memories = (
                db.query(ConversationMemory)
                .filter(ConversationMemory.updated_at != None)
                .filter(ConversationMemory.updated_at < cutoff)
                .all()
            )
            count = len(old_memories)
            for mem in old_memories:
                db.delete(mem)
            db.commit()
            return count

    def _refresh_context_window(self, db: Session, memory_id: int) -> None:
        recent_messages = (
            db.query(MemoryMessage)
            .filter(MemoryMessage.memory_id == memory_id)
            .order_by(MemoryMessage.timestamp.desc())
            .limit(self.max_context_length)
            .all()
        )
        ctx = [{"role": m.role, "content": m.content} for m in reversed(recent_messages)]
        (
            db.query(ConversationMemory)
            .filter(ConversationMemory.id == memory_id)
            .update({"context_window": ctx})
        )
        db.commit()


