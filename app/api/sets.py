"""
Iconify v2.1.0 - Sets API
"""
from fastapi import APIRouter, HTTPException
import asyncio

from app.services import catalog, downloader
from app.config import ICON_SETS

router = APIRouter()


@router.get("")
async def list_sets():
    """Listet alle verfügbaren Icon-Sets"""
    return catalog.get_available_sets()


@router.get("/{set_id}")
async def get_set_info(set_id: str):
    """Gibt detaillierte Infos zu einem Icon-Set"""
    info = catalog.get_set_info(set_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Set nicht gefunden: {set_id}")
    return info


@router.post("/{set_id}/download")
async def download_set(set_id: str):
    """Startet Download eines Icon-Sets"""
    if set_id not in ICON_SETS:
        raise HTTPException(status_code=404, detail=f"Unbekanntes Set: {set_id}")
    
    asyncio.create_task(downloader.download_icon_set(set_id))
    
    return {
        "status": "started",
        "set_id": set_id,
        "message": f"Download von {ICON_SETS[set_id].name} gestartet"
    }


@router.get("/{set_id}/progress")
async def get_download_progress(set_id: str):
    """Gibt aktuellen Download-Fortschritt zurück"""
    progress = downloader.get_progress(set_id)
    if not progress:
        return {"status": "idle", "message": "Kein aktiver Download"}
    return progress


@router.delete("/{set_id}")
async def delete_set(set_id: str):
    """Löscht ein heruntergeladenes Icon-Set"""
    success = catalog.delete_set(set_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Set nicht gefunden: {set_id}")
    return {"status": "deleted", "set_id": set_id}
