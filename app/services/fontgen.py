"""
Iconify v2.4.0 - Font Generator Service
Generiert Icon-Fonts mit Original-Klassennamen der Sets
"""

import asyncio
import json
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
from datetime import datetime
import logging

from app.config import ICON_SETS

logger = logging.getLogger(__name__)

ICONS_PATH = Path("/app/icons")
TEMP_PATH = Path("/app/temp")


def get_icon_prefix(icons: list[dict]) -> tuple[str, bool]:
    """
    Ermittelt den Prefix für den Font.
    
    Returns:
        (prefix, is_single_set) - Prefix und ob alle Icons aus einem Set stammen
    """
    sets = set(icon.get("set_id", "") for icon in icons)
    
    if len(sets) == 1:
        # Alle aus einem Set - Original-Prefix verwenden
        set_id = list(sets)[0]
        if set_id in ICON_SETS:
            return ICON_SETS[set_id].font_prefix, True
    
    # Gemischt - generischer Prefix, aber mit Set-Kennzeichnung in Namen
    return "icon", False


def generate_font(icons: list[dict], font_name: str = "my-icons") -> Path:
    """
    Generiert einen Icon-Font aus den ausgewählten Icons.
    
    Bei Icons aus einem einzelnen Set werden die Original-Klassennamen verwendet.
    Bei gemischten Sets wird ein kombinierter Prefix verwendet.
    
    Args:
        icons: Liste von {"set_id": str, "name": str, "style": str, "path": str}
        font_name: Name für den Font (default: my-icons)
    
    Returns:
        Path zum generierten ZIP-Archiv
    """
    # Eindeutiger Arbeitsordner
    work_id = str(uuid.uuid4())[:8]
    work_dir = TEMP_PATH / work_id
    svg_dir = work_dir / "svg"
    output_dir = work_dir / "output"
    
    svg_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    try:
        # Prefix ermitteln
        prefix, is_single_set = get_icon_prefix(icons)
        
        # 1. SVGs kopieren und normalisieren
        icon_map = {}
        used_names = set()
        
        for i, icon in enumerate(icons):
            set_id = icon.get("set_id", "")
            name = icon.get("name", "")
            style = icon.get("style", "")
            
            # Quell-SVG finden
            if style:
                src_path = ICONS_PATH / set_id / style / f"{name}.svg"
            else:
                src_path = ICONS_PATH / set_id / f"{name}.svg"
            
            if not src_path.exists():
                # Suche in Unterordnern
                for svg_file in (ICONS_PATH / set_id).glob(f"**/{name}.svg"):
                    src_path = svg_file
                    break
            
            if src_path.exists():
                # Font-Klassennamen generieren
                if is_single_set:
                    # Original-Namen beibehalten (z.B. "arrow-left" -> "arrow-left")
                    class_name = name
                else:
                    # Set-Prefix voranstellen für Eindeutigkeit (z.B. "ti-arrow-left")
                    set_prefix = ICON_SETS[set_id].font_prefix if set_id in ICON_SETS else set_id
                    class_name = f"{set_prefix}-{name}"
                
                # Eindeutigkeit sicherstellen
                safe_name = class_name.replace(" ", "-")
                if safe_name in used_names:
                    safe_name = f"{safe_name}-{i}"
                used_names.add(safe_name)
                
                dst_path = svg_dir / f"{safe_name}.svg"
                
                # SVG kopieren und optimieren
                svg_content = src_path.read_text()
                svg_content = optimize_svg_for_font(svg_content)
                dst_path.write_text(svg_content)
                
                icon_map[safe_name] = {
                    "original_name": name,
                    "set": set_id,
                    "style": style,
                    "class": f"{prefix}-{safe_name}"
                }
            else:
                logger.warning(f"SVG nicht gefunden: {src_path}")
        
        if not icon_map:
            raise ValueError("Keine gültigen Icons gefunden")
        
        # 2. fantasticon ausführen
        result = subprocess.run(
            ["fantasticon", str(svg_dir), "-o", str(output_dir), "-n", font_name,
             "--font-types", "woff2", "woff", "ttf",
             "--asset-types", "css", "html", "json",
             "--prefix", prefix,
             "--normalize",
             "--font-height", "1000"],
            capture_output=True,
            text=True,
            timeout=120  # Mehr Zeit für große Sets
        )
        
        if result.returncode != 0:
            logger.error(f"fantasticon Fehler: {result.stderr}")
            raise Exception(f"fantasticon fehlgeschlagen: {result.stderr}")
        
        # 3. Set-Info für README
        sets_used = {}
        for info in icon_map.values():
            set_id = info["set"]
            if set_id not in sets_used:
                if set_id in ICON_SETS:
                    cfg = ICON_SETS[set_id]
                    sets_used[set_id] = {
                        "name": cfg.name,
                        "license": cfg.license,
                        "license_spdx": cfg.license_spdx,
                        "license_url": cfg.license_url,
                        "requires_attribution": cfg.requires_attribution,
                        "website": cfg.website,
                        "count": 0
                    }
                else:
                    sets_used[set_id] = {
                        "name": set_id, "license": "Custom", "license_spdx": "",
                        "license_url": "", "requires_attribution": False,
                        "website": "", "count": 0
                    }
            sets_used[set_id]["count"] += 1

        # 4. README + ATTRIBUTION.txt erstellen
        readme = generate_readme(font_name, prefix, icon_map, sets_used, is_single_set)
        (output_dir / "README.md").write_text(readme)
        (output_dir / "ATTRIBUTION.txt").write_text(generate_attribution(sets_used))
        
        # 5. Icon-Map als JSON speichern
        (output_dir / "icons.json").write_text(json.dumps(icon_map, indent=2))
        
        # 6. ZIP erstellen
        zip_path = TEMP_PATH / f"{font_name}-{work_id}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in output_dir.iterdir():
                zf.write(file, f"{font_name}/{file.name}")
            # SVGs auch beilegen
            svg_subdir = f"{font_name}/svg"
            for svg_file in svg_dir.iterdir():
                zf.write(svg_file, f"{svg_subdir}/{svg_file.name}")
        
        # Arbeitsordner aufräumen
        shutil.rmtree(work_dir, ignore_errors=True)
        
        return zip_path
        
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise e


def optimize_svg_for_font(svg_content: str) -> str:
    """
    Optimiert SVG für Font-Generierung.
    """
    import re
    
    # Entferne width/height Attribute, behalte viewBox
    svg_content = re.sub(r'\s+width="[^"]*"', '', svg_content)
    svg_content = re.sub(r'\s+height="[^"]*"', '', svg_content)
    
    # Ersetze currentColor durch black (für Font-Generierung)
    svg_content = svg_content.replace('currentColor', '#000000')
    
    return svg_content


def generate_readme(font_name: str, prefix: str, icon_map: dict, sets_used: dict, is_single_set: bool) -> str:
    """Generiert README mit korrekten Klassennamen und Lizenzinfo"""
    
    icon_count = len(icon_map)
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Lizenz-Info
    license_info = "\n".join([
        f"- **{info['name']}** ({info['count']} Icons) - {info['license']} - {info['website']}"
        for set_id, info in sets_used.items()
    ])
    
    # Beispiel-Icons (erste 10)
    example_icons = list(icon_map.items())[:10]
    example_html = "\n".join([f'<i class="{prefix} {prefix}-{name}"></i> <!-- {info["original_name"]} -->'
                              for name, info in example_icons])
    
    # Icon-Liste
    icon_list = "\n".join([f"- `.{prefix}-{name}` ({info['set']})" 
                          for name, info in icon_map.items()])
    
    # Hinweis für Single-Set
    compatibility_note = ""
    if is_single_set and len(sets_used) == 1:
        set_id = list(sets_used.keys())[0]
        if set_id in ICON_SETS:
            original = ICON_SETS[set_id]
            if original.font_url:
                compatibility_note = f"""
## Kompatibilität

Dieser Font verwendet den Original-Prefix `{prefix}` von **{original.name}**.
Die Klassennamen sind kompatibel mit dem offiziellen Font:

```html
<!-- Offizieller Font -->
<link rel="stylesheet" href="{original.font_url}">

<!-- Dieser Custom Font (lokale Alternative) -->
<link rel="stylesheet" href="{font_name}.css">

<!-- Gleiche Verwendung -->
<i class="{prefix} {prefix}-{example_icons[0][0] if example_icons else 'example'}"></i>
```
"""

    return f"""# {font_name}

Custom Icon Font - Generiert mit Iconify am {date}

## Inhalt

- **{icon_count} Icons** 
- Font-Dateien: WOFF2, WOFF, TTF
- CSS mit Klassen (Prefix: `{prefix}`)
- HTML-Demo/Cheatsheet

## Verwendete Icon-Sets

{license_info}
{compatibility_note}
## Einbindung

### 1. CSS einbinden

```html
<link rel="stylesheet" href="{font_name}.css">
```

### 2. Icons verwenden

```html
{example_html}
```

### 3. Größe und Farbe anpassen

```css
.{prefix} {{
    font-size: 24px;
    color: #333;
}}
```

## Alle Icons

{icon_list}

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `{font_name}.woff2` | Modernes Font-Format (empfohlen) |
| `{font_name}.woff` | Fallback für ältere Browser |
| `{font_name}.ttf` | TrueType Font |
| `{font_name}.css` | CSS mit Icon-Klassen |
| `{font_name}.html` | Demo/Cheatsheet |
| `icons.json` | Icon-Mapping als JSON |
| `svg/` | Original SVG-Dateien |

---
Generiert mit Iconify
"""


def generate_attribution(sets_used: dict) -> str:
    """Erzeugt eine ATTRIBUTION.txt (NOTICE) mit Lizenz-/Quellenhinweisen je Set."""
    lines = [
        "ATTRIBUTION / LIZENZHINWEISE",
        "=" * 40,
        "",
        "Dieser Icon-Font wurde mit Iconify aus den folgenden Icon-Sets erzeugt.",
        "Die Icons unterliegen den jeweiligen Set-Lizenzen:",
        "",
    ]
    needs_attr = False
    for info in sets_used.values():
        spdx = info.get("license_spdx") or ""
        lines.append(f"- {info['name']} ({info['count']} Icons)")
        lines.append(f"    Lizenz: {info.get('license', '')}" + (f" [{spdx}]" if spdx else ""))
        if info.get("license_url"):
            lines.append(f"    Lizenztext: {info['license_url']}")
        if info.get("website"):
            lines.append(f"    Quelle: {info['website']}")
        if info.get("requires_attribution"):
            needs_attr = True
            lines.append("    HINWEIS: Dieses Set verlangt eine Namensnennung (Attribution).")
        lines.append("")
    if needs_attr:
        lines += [
            "-" * 40,
            "Mindestens ein verwendetes Set ist attributionspflichtig (z. B. CC BY 4.0).",
            "Bitte diese Datei bei der Weitergabe beibehalten und die Urheber nennen.",
            "",
        ]
    return "\n".join(lines)


def cleanup_old_fonts(max_age_hours: int = 24):
    """Löscht alte generierte Fonts"""
    import time
    
    now = time.time()
    max_age = max_age_hours * 3600
    
    for f in TEMP_PATH.glob("*.zip"):
        if now - f.stat().st_mtime > max_age:
            f.unlink()
            logger.info(f"Alte Font-Datei gelöscht: {f}")
