from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["Pages"])


@router.get("/")
async def index_page():
    """Serves the main interactive Live2D VTuber web stage."""
    return FileResponse("static/index.html")


@router.get("/settings")
async def settings_page():
    """Serves the dedicated full-system settings page."""
    return FileResponse("static/settings.html")
