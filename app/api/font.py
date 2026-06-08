"""
Iconify v2.4.0 - Font Generator API
Endpoint für Custom Icon Font Generierung
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import logging

from app.services import fontgen

logger = logging.getLogger(__name__)

router = APIRouter()


class FontRequest(BaseModel):
    """Request für Font-Generierung"""
    icons: list[dict]  # [{"set_id": str, "name": str, "style": str}]
    font_name: str = "my-icons"


class FontResponse(BaseModel):
    """Response nach Font-Generierung"""
    success: bool
    download_url: str = ""
    icon_count: int = 0
    error: str = ""


@router.post("/generate", response_model=FontResponse)
async def generate_font(request: FontRequest):
    """
    Generiert einen Icon-Font aus den ausgewählten Icons.
    
    Body:
    ```json
    {
        "icons": [
            {"set_id": "feather", "name": "alert-circle", "style": ""},
            {"set_id": "heroicons", "name": "check", "style": "24/solid"}
        ],
        "font_name": "my-custom-icons"
    }
    ```
    
    Returns:
        download_url: URL zum ZIP-Download
    """
    if not request.icons:
        raise HTTPException(status_code=400, detail="Keine Icons ausgewählt")
    
    # Font-Name bereinigen
    font_name = "".join(c for c in request.font_name if c.isalnum() or c in "-_")
    if not font_name:
        font_name = "my-icons"
    
    try:
        zip_path = fontgen.generate_font(request.icons, font_name)
        
        return FontResponse(
            success=True,
            download_url=f"/api/font/download/{zip_path.name}",
            icon_count=len(request.icons)
        )
    except Exception as e:
        logger.error(f"Font-Generierung fehlgeschlagen: {e}")
        return FontResponse(
            success=False,
            error=str(e)
        )


@router.get("/download/{filename}")
async def download_font(filename: str, background_tasks: BackgroundTasks):
    """Lädt das generierte Font-ZIP herunter"""
    
    # Sicherheitsprüfung
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Ungültiger Dateiname")
    
    file_path = Path("/app/temp") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Font nicht gefunden oder abgelaufen")
    
    # Nach Download löschen (nach 5 min um mehrfache Downloads zu erlauben)
    # background_tasks.add_task(cleanup_after_download, file_path)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip"
    )


@router.delete("/cleanup")
async def cleanup_fonts():
    """Löscht alte generierte Fonts (manueller Aufruf oder Cron)"""
    fontgen.cleanup_old_fonts(max_age_hours=24)
    return {"status": "ok", "message": "Alte Fonts bereinigt"}
