import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from src.core import BG_DIR, app_logger

router = APIRouter(prefix="/api", tags=["Media"])


@router.post("/upload-bg")
async def upload_background(file: UploadFile = File(...)):
    """Handles custom wallpaper background uploads."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File tidak valid")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(status_code=400, detail="Hanya format gambar yang didukung (JPG, PNG, WebP)")

    save_path = BG_DIR / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    bg_url = f"/backgrounds/{file.filename}"
    app_logger.info("Background", f"Uploaded new wallpaper: {bg_url}")
    return {"status": "success", "url": bg_url}
