import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.core import (
    config,
    BG_DIR,
    CACHE_DIR,
    mcp_manager,
    app_logger
)
from src.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles graceful startup and shutdown lifecycle for external tools and services."""
    app_logger.info("Server", "Starting Personal AI VTuber server...")
    try:
        await mcp_manager.initialize()
    except Exception as e:
        app_logger.error("Server", f"Failed to initialize MCP Manager: {e}")
    yield
    app_logger.info("Server", "Shutting down server...")
    await mcp_manager.close()


# Application Instance
app = FastAPI(
    title="Personal AI VTuber",
    description="Clean, modular, and lightweight interactive AI VTuber Companion",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Asset Mounts
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
app.mount("/cache", StaticFiles(directory=str(CACHE_DIR)), name="cache")
app.mount("/backgrounds", StaticFiles(directory=str(BG_DIR)), name="backgrounds")

# Register Modular Routers
app.include_router(api_router)


if __name__ == "__main__":
    host = os.getenv("HOST", config["server"].get("host", "127.0.0.1"))
    port = int(os.getenv("PORT", config["server"].get("port", 8080)))
    print(f"==================================================")
    print(f" Personal AI VTuber Server running on: http://{host}:{port}")
    print(f" Settings Dashboard available at:     http://{host}:{port}/settings")
    print(f"==================================================")
    uvicorn.run("app:app", host=host, port=port, reload=True)
