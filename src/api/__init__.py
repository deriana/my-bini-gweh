from fastapi import APIRouter

from .pages import router as pages_router
from .config_routes import router as config_router
from .persona_routes import router as persona_router
from .tts_routes import router as tts_router
from .memory_routes import router as memory_router
from .media_routes import router as media_router
from .logs_routes import router as logs_router
from .websocket import router as ws_router

# Central aggregator router
api_router = APIRouter()

api_router.include_router(pages_router)
api_router.include_router(config_router)
api_router.include_router(persona_router)
api_router.include_router(tts_router)
api_router.include_router(memory_router)
api_router.include_router(media_router)
api_router.include_router(logs_router)
api_router.include_router(ws_router)

__all__ = ["api_router"]
