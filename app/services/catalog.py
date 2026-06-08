"""
Iconify v2.3.0 - Catalog Service
Verwaltet heruntergeladene Icon-Sets inkl. Custom Sets
"""
import json
import shutil
from pathlib import Path
from typing import Optional

from app.config import ICON_SETS, ICONS_PATH


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


def get_available_sets() -> list[dict]:
    """Listet alle verfügbaren Sets mit Download-Status"""
    sets = []
    
    # Standard Icon-Sets
    for config in ICON_SETS.values():
        set_path = ICONS_PATH / config.id
        downloaded = set_path.exists() and any(set_path.iterdir()) if set_path.exists() else False
        
        info = {
            "id": config.id,
            "name": config.name,
            "estimated_count": config.icon_count,
            "license": config.license,
            "website": config.website,
            "styles": config.styles,
            "downloaded": downloaded,
            "has_font": bool(config.font_url),
            "icon_count": 0,
            "is_custom": False
        }
        
        if downloaded:
            meta_path = set_path / "meta.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    info["icon_count"] = meta.get("icon_count", 0)
                    info["total_files"] = meta.get("total_files", 0)
                    info["downloaded_at"] = meta.get("downloaded_at")
                except:
                    pass
        
        sets.append(info)
    
    # Custom Sets hinzufügen
    custom_sets = load_custom_sets()
    for set_id, config in custom_sets.items():
        set_path = ICONS_PATH / set_id
        icon_count = len(list(set_path.glob("*.svg"))) if set_path.exists() else 0
        
        sets.append({
            "id": set_id,
            "name": config.get("name", set_id),
            "estimated_count": icon_count,
            "license": config.get("license", "Custom"),
            "website": config.get("website", ""),
            "styles": ["default"],
            "downloaded": True,  # Custom Sets sind immer "downloaded"
            "has_font": False,
            "icon_count": icon_count,
            "is_custom": True,
            "prefix": config.get("prefix", set_id)
        })
    
    # Heruntergeladene zuerst, dann alphabetisch
    return sorted(sets, key=lambda x: (not x["downloaded"], x["name"]))


def get_set_info(set_id: str) -> Optional[dict]:
    """Gibt detaillierte Infos zu einem Set"""
    
    # Prüfe Standard-Sets
    if set_id in ICON_SETS:
        config = ICON_SETS[set_id]
        set_path = ICONS_PATH / set_id
        
        info = {
            "id": config.id,
            "name": config.name,
            "license": config.license,
            "website": config.website,
            "styles": config.styles,
            "downloaded": set_path.exists(),
            "font_url": config.font_url,
            "font_class_pattern": config.font_class_pattern,
            "font_family": config.font_family,
            "has_font": bool(config.font_url),
            "is_custom": False
        }
        
        if set_path.exists():
            meta_path = set_path / "meta.json"
            if meta_path.exists():
                try:
                    info.update(json.loads(meta_path.read_text()))
                except:
                    pass
        
        return info
    
    # Prüfe Custom Sets
    custom_sets = load_custom_sets()
    if set_id in custom_sets:
        config = custom_sets[set_id]
        set_path = ICONS_PATH / set_id
        icon_count = len(list(set_path.glob("*.svg"))) if set_path.exists() else 0
        
        return {
            "id": set_id,
            "name": config.get("name", set_id),
            "license": config.get("license", "Custom"),
            "website": config.get("website", ""),
            "styles": ["default"],
            "downloaded": True,
            "font_url": None,
            "font_class_pattern": None,
            "font_family": None,
            "has_font": False,
            "is_custom": True,
            "icon_count": icon_count,
            "prefix": config.get("prefix", set_id)
        }
    
    return None


def search_icons(
    set_id: str,
    query: str = "",
    style: str = "",
    page: int = 1,
    per_page: int = 100
) -> dict:
    """Sucht Icons in einem Set"""
    
    # Prüfe ob Set existiert
    custom_sets = load_custom_sets()
    is_custom = set_id in custom_sets
    
    if set_id not in ICON_SETS and not is_custom:
        return {"error": f"Set nicht gefunden: {set_id}", "icons": [], "total": 0}
    
    set_path = ICONS_PATH / set_id
    
    if not set_path.exists():
        return {"error": "Set nicht heruntergeladen", "icons": [], "total": 0}
    
    icons = []
    seen_names = set()
    found_styles = set()
    
    # Icons sammeln - rekursiv aus allen Unterordnern
    for svg_file in set_path.glob("**/*.svg"):
        name = svg_file.stem
        
        # Relativen Pfad berechnen
        rel_path = svg_file.relative_to(set_path)
        
        if len(rel_path.parts) > 1:
            # Alle Teile außer dem Dateinamen = Style-Pfad
            style_parts = rel_path.parts[:-1]
            icon_style = "/".join(style_parts)
            icon_path = f"/icons/{set_id}/{icon_style}/{name}"
            found_styles.add(icon_style)
        else:
            icon_style = ""
            icon_path = f"/icons/{set_id}/{name}"
        
        # Style-Filter
        if style and icon_style != style:
            continue
        
        # Query-Filter
        if query and query.lower() not in name.lower():
            continue
        
        # Duplikate vermeiden (gleiches Icon in mehreren Styles)
        if not style and name in seen_names:
            continue
        seen_names.add(name)
        
        icons.append({
            "name": name,
            "style": icon_style,
            "path": icon_path,
            "set_id": set_id
        })
    
    # Sortieren
    icons.sort(key=lambda x: x["name"])
    
    # Pagination
    total = len(icons)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = icons[start:end]
    
    # Styles sortiert zurückgeben
    available_styles = sorted(found_styles) if found_styles else []
    
    # Font-Info
    has_font = False
    if set_id in ICON_SETS:
        has_font = bool(ICON_SETS[set_id].font_url)
    
    return {
        "icons": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
        "styles": available_styles,
        "has_font": has_font,
        "is_custom": is_custom
    }


def delete_set(set_id: str) -> bool:
    """Löscht ein Set"""
    set_path = ICONS_PATH / set_id
    if set_path.exists():
        shutil.rmtree(set_path)
        
        # Bei Custom Sets auch aus Config entfernen
        custom_sets = load_custom_sets()
        if set_id in custom_sets:
            del custom_sets[set_id]
            CUSTOM_SETS_FILE.write_text(json.dumps(custom_sets, indent=2))
        
        return True
    return False
