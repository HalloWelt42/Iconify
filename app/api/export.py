"""
Iconify v2.5.0 - Export-API
Erzeugt aus einer Icon-Auswahl ein SVG-ZIP oder ein SVG-Sprite-Sheet.
(Font-Export liegt in app/api/font.py.)
"""
import re
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.config import ICONS_PATH

router = APIRouter()
TEMP_PATH = Path("/app/temp")


class ExportRequest(BaseModel):
    icons: list[dict]   # [{"set_id": str, "name": str, "style": str}]
    name: str = "icons"


def _svg_path(icon: dict) -> Path | None:
    base = ICONS_PATH / icon.get("set_id", "")
    name = icon.get("name", "")
    style = icon.get("style", "")
    if style:
        p = base.joinpath(*style.split("/"), f"{name}.svg")
        if p.exists():
            return p
    p = base / f"{name}.svg"
    if p.exists():
        return p
    hits = list(base.glob(f"**/{name}.svg")) if base.exists() else []
    return hits[0] if hits else None


def _safe(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in "-_") or "icons"


@router.post("/zip")
async def export_zip(req: ExportRequest, background_tasks: BackgroundTasks):
    """Packt die ausgewählten SVGs in ein ZIP."""
    TEMP_PATH.mkdir(parents=True, exist_ok=True)
    name = _safe(req.name)
    zip_path = TEMP_PATH / f"{name}-{uuid.uuid4().hex[:8]}.zip"
    seen: set[str] = set()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for icon in req.icons:
            p = _svg_path(icon)
            if not p:
                continue
            arc = f"{icon.get('set_id', 'icons')}/{p.name}"
            if arc in seen:
                continue
            seen.add(arc)
            zf.write(p, arc)
    return FileResponse(zip_path, filename=f"{name}.zip", media_type="application/zip")


@router.post("/sprite")
async def export_sprite(req: ExportRequest):
    """Baut ein SVG-Sprite-Sheet (<symbol> je Icon) zum Einbinden via <use>."""
    symbols = []
    for icon in req.icons:
        p = _svg_path(icon)
        if not p:
            continue
        svg = p.read_text()
        m = re.search(r'viewBox="([^"]+)"', svg)
        vb = m.group(1) if m else "0 0 24 24"
        inner = re.sub(r"^.*?<svg[^>]*>", "", svg, count=1, flags=re.S)
        inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
        sid = re.sub(r"[^a-z0-9-]", "-", f"{icon.get('set_id','')}-{icon.get('name','')}".lower())
        symbols.append(f'<symbol id="{sid}" viewBox="{vb}">{inner.strip()}</symbol>')
    sprite = ('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">'
              + "".join(symbols) + "</svg>")
    return Response(
        content=sprite,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'attachment; filename="{_safe(req.name)}-sprite.svg"'},
    )
