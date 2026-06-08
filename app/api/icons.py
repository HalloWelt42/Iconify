"""
Iconify v2.1.0 - Icons API
Inkl. Code-Generierung für SVG, IMG, Font
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pathlib import Path
import re

from app.services import catalog
from app.config import ICONS_PATH, ICON_SETS

router = APIRouter()


@router.get("/search")
async def search_icons(
    set_id: str = Query(...),
    q: str = Query(""),
    style: str = Query(""),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=10, le=10000)
):
    """Sucht Icons in einem Set mit Pagination"""
    result = catalog.search_icons(
        set_id=set_id,
        query=q,
        style=style,
        page=page,
        per_page=per_page
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{set_id}/{icon_name}/svg")
async def get_icon_svg(set_id: str, icon_name: str, style: str = Query("")):
    """Gibt das SVG eines Icons zurück"""
    set_path = ICONS_PATH / set_id
    
    # Pfad finden
    svg_path = None
    if style:
        svg_path = set_path / style / f"{icon_name}.svg"
    else:
        # In Root oder erstem Style-Ordner suchen
        candidate = set_path / f"{icon_name}.svg"
        if candidate.exists():
            svg_path = candidate
        else:
            for d in set_path.iterdir():
                if d.is_dir():
                    candidate = d / f"{icon_name}.svg"
                    if candidate.exists():
                        svg_path = candidate
                        break
    
    if not svg_path or not svg_path.exists():
        raise HTTPException(status_code=404, detail="SVG nicht gefunden")
    
    return Response(content=svg_path.read_text(), media_type="image/svg+xml")


@router.get("/{set_id}/{icon_name}/code")
async def get_icon_code(
    set_id: str, 
    icon_name: str, 
    style: str = Query(""),
    color: str = Query("#000000"),
    size: int = Query(24)
):
    """
    Gibt alle Code-Snippets für ein Icon zurück:
    - SVG inline
    - IMG Tag
    - Font HTML
    - Font CSS
    """
    if set_id not in ICON_SETS:
        raise HTTPException(status_code=404, detail="Set nicht gefunden")
    
    config = ICON_SETS[set_id]
    set_path = ICONS_PATH / set_id
    
    # SVG finden und laden
    svg_content = None
    svg_path = None
    actual_style = style
    
    if style:
        svg_path = set_path / style / f"{icon_name}.svg"
    else:
        candidate = set_path / f"{icon_name}.svg"
        if candidate.exists():
            svg_path = candidate
        else:
            for d in set_path.iterdir():
                if d.is_dir():
                    candidate = d / f"{icon_name}.svg"
                    if candidate.exists():
                        svg_path = candidate
                        actual_style = d.name
                        break
    
    if svg_path and svg_path.exists():
        svg_content = svg_path.read_text()
        
        # Farbe ersetzen
        svg_colored = svg_content.replace('currentColor', color)
        
        # Größe setzen
        svg_colored = re.sub(r'width="[^"]*"', f'width="{size}"', svg_colored)
        svg_colored = re.sub(r'height="[^"]*"', f'height="{size}"', svg_colored)
        if 'width=' not in svg_colored:
            svg_colored = svg_colored.replace('<svg', f'<svg width="{size}" height="{size}"', 1)
    else:
        svg_colored = None
    
    # Icon-Pfad für IMG
    if actual_style:
        icon_path = f"/icons/{set_id}/{actual_style}/{icon_name}.svg"
    else:
        icon_path = f"/icons/{set_id}/{icon_name}.svg"
    
    # Font-Klasse generieren
    font_html = None
    font_css = None
    
    if config.font_class_pattern and config.font_url:
        font_class = config.font_class_pattern.replace("{name}", icon_name)
        if "{style}" in font_class:
            font_class = font_class.replace("{style}", actual_style or config.styles[0])
        
        font_html = f'<i class="{font_class}" style="font-size: {size}px; color: {color};"></i>'
        
        font_css = f'''/* Font einbinden */
@import url('{config.font_url}');

/* Icon verwenden */
.my-icon {{
    font-family: '{config.font_family or "inherit"}';
    font-size: {size}px;
    color: {color};
}}
.my-icon::before {{
    content: "\\e000"; /* Codepoint variiert */
}}'''
    
    return {
        "svg": svg_colored,
        "img": f'<img src="{icon_path}" width="{size}" height="{size}" alt="{icon_name}">',
        "font_html": font_html,
        "font_css": font_css,
        "font_url": config.font_url,
        "has_font": bool(config.font_url)
    }
