from fastapi import APIRouter

from src.core import app_logger

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("")
async def get_system_logs():
    """Returns recent model and system activity logs."""
    return {"logs": app_logger.get_logs(limit=200)}


@router.post("/clear")
async def clear_system_logs():
    """Clears the in-memory log buffer."""
    app_logger.clear()
    return {"status": "success", "message": "Log telah dibersihkan."}
