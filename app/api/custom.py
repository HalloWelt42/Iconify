"""
Iconify v2.4.0 - Custom Icon Sets API
Eigene Icon-Sets anlegen, verwalten und Icons hochladen
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import json
import re
import shutil
import logging

from app.config import ICONS_PATH

logger = logging.getLogger(__name__)

router = APIRouter()

# Custom Sets Konfiguration
CUSTOM_SETS_FILE = ICONS_PATH / "_custom_sets.json"


def load_custom_sets() -> dict:
    """Lädt Custom Sets Konfiguration"""
    if CUSTOM_SETS_FILE.exists():
        try:
            return json.loads(CUSTOM_SETS_FILE.read_text())
        except:
            return {}
    return {}


def save_custom_sets(sets: dict):
    """Speichert Custom Sets Konfiguration"""
    CUSTOM_SETS_FILE.write_text(json.dumps(sets, indent=2))


def sanitize_id(name: str) -> str:
    """Erzeugt sichere ID aus Namen"""
    # Nur alphanumerisch und Bindestriche
    safe = re.sub(r'[^a-z0-9-]', '-', name.lower())
    safe = re.sub(r'-+', '-', safe).strip('-')
    return safe or "custom"


class CreateSetRequest(BaseModel):
    name: str
    prefix: str = ""


class CreateSetResponse(BaseModel):
    success: bool
    set_id: str = ""
    error: str = ""


@router.get("/sets")
async def list_custom_sets():
    """Listet alle Custom Sets"""
    sets = load_custom_sets()
    result = []
    
    for set_id, info in sets.items():
        set_path = ICONS_PATH / set_id
        icon_count = len(list(set_path.glob("*.svg"))) if set_path.exists() else 0
        result.append({
            "id": set_id,
            "name": info.get("name", set_id),
            "prefix": info.get("prefix", set_id),
            "icon_count": icon_count,
            "is_custom": True
        })
    
    return {"sets": result}


@router.post("/sets", response_model=CreateSetResponse)
async def create_custom_set(request: CreateSetRequest):
    """Erstellt ein neues Custom Set"""
    if not request.name or len(request.name) < 2:
        return CreateSetResponse(success=False, error="Name zu kurz (min. 2 Zeichen)")
    
    set_id = f"custom-{sanitize_id(request.name)}"
    prefix = sanitize_id(request.prefix) if request.prefix else set_id.replace("custom-", "")
    
    sets = load_custom_sets()
    
    # Prüfen ob ID schon existiert
    if set_id in sets:
        return CreateSetResponse(success=False, error=f"Set '{set_id}' existiert bereits")
    
    # Ordner erstellen
    set_path = ICONS_PATH / set_id
    set_path.mkdir(parents=True, exist_ok=True)
    
    # In Config speichern
    sets[set_id] = {
        "name": request.name,
        "prefix": prefix,
        "license": "Custom",
        "website": ""
    }
    save_custom_sets(sets)
    
    logger.info(f"Custom Set erstellt: {set_id}")
    return CreateSetResponse(success=True, set_id=set_id)


@router.delete("/sets/{set_id}")
async def delete_custom_set(set_id: str):
    """Löscht ein Custom Set komplett"""
    sets = load_custom_sets()
    
    if set_id not in sets:
        raise HTTPException(status_code=404, detail="Custom Set nicht gefunden")
    
    # Ordner löschen
    set_path = ICONS_PATH / set_id
    if set_path.exists():
        shutil.rmtree(set_path)
    
    # Aus Config entfernen
    del sets[set_id]
    save_custom_sets(sets)
    
    logger.info(f"Custom Set gelöscht: {set_id}")
    return {"success": True, "message": f"Set '{set_id}' gelöscht"}


@router.post("/sets/{set_id}/icons")
async def upload_icons(set_id: str, files: list[UploadFile] = File(...)):
    """Lädt Icons in ein Custom Set hoch"""
    sets = load_custom_sets()
    
    if set_id not in sets:
        raise HTTPException(status_code=404, detail="Custom Set nicht gefunden")
    
    set_path = ICONS_PATH / set_id
    set_path.mkdir(parents=True, exist_ok=True)
    
    uploaded = []
    errors = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Nur SVG erlauben
        if not file.filename.lower().endswith('.svg'):
            errors.append(f"{file.filename}: Nur SVG-Dateien erlaubt")
            continue
        
        # Dateiname bereinigen
        safe_name = sanitize_id(Path(file.filename).stem) + ".svg"
        
        try:
            content = await file.read()
            
            # Basis-Validierung: Ist es SVG?
            content_str = content.decode('utf-8')
            if '<svg' not in content_str.lower():
                errors.append(f"{file.filename}: Keine gültige SVG-Datei")
                continue
            
            # Speichern
            (set_path / safe_name).write_bytes(content)
            uploaded.append(safe_name.replace('.svg', ''))
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return {
        "success": len(uploaded) > 0,
        "uploaded": uploaded,
        "errors": errors,
        "count": len(uploaded)
    }


@router.delete("/sets/{set_id}/icons/{icon_name}")
async def delete_icon(set_id: str, icon_name: str):
    """Löscht ein einzelnes Icon aus einem Custom Set"""
    sets = load_custom_sets()
    
    if set_id not in sets:
        raise HTTPException(status_code=404, detail="Custom Set nicht gefunden")
    
    set_path = ICONS_PATH / set_id
    icon_path = set_path / f"{icon_name}.svg"
    
    if not icon_path.exists():
        raise HTTPException(status_code=404, detail="Icon nicht gefunden")
    
    icon_path.unlink()
    logger.info(f"Icon gelöscht: {set_id}/{icon_name}")
    
    return {"success": True, "message": f"Icon '{icon_name}' gelöscht"}


@router.get("/sets/{set_id}/icons")
async def list_custom_icons(set_id: str):
    """Listet alle Icons in einem Custom Set"""
    sets = load_custom_sets()
    
    if set_id not in sets:
        raise HTTPException(status_code=404, detail="Custom Set nicht gefunden")
    
    set_path = ICONS_PATH / set_id
    icons = []
    
    if set_path.exists():
        for svg_file in sorted(set_path.glob("*.svg")):
            icons.append({
                "name": svg_file.stem,
                "path": f"/icons/{set_id}/{svg_file.stem}"
            })
    
    return {
        "set_id": set_id,
        "icons": icons,
        "total": len(icons)
    }
