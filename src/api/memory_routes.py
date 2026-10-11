from typing import Dict
from fastapi import APIRouter

from src.core import db, app_logger

router = APIRouter(prefix="/api/history", tags=["Memory & History"])


@router.get("")
async def get_history(session_id: str = "default"):
    """Returns conversation history for a given session from SQLite."""
    sessions = db.get_sessions()
    messages = db.get_messages(session_id=session_id)
    return {"sessions": sessions, "messages": messages}


@router.post("/reset")
async def reset_session_memory(payload: Dict[str, str]):
    """Clears messages for the active session (AI forgets recent chat context)."""
    session_id = payload.get("session_id", "default")
    db.clear_session_messages(session_id)
    app_logger.info("Memory", f"Reset conversation memory for session: {session_id}")
    return {"status": "success", "message": f"Memori sesi '{session_id}' telah dibersihkan."}


@router.delete("")
async def delete_all_history():
    """Wipes all conversation sessions and messages from SQLite database."""
    db.delete_all()
    app_logger.info("Memory", "All conversation history deleted from database.")
    return {"status": "success", "message": "Seluruh riwayat chat telah dihapus."}
