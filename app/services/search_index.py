"""
Iconify v2.5.0 - In-Memory Such-Index (SQLite)

Set-übergreifende Sofort-Suche über ALLE Icons. Wird aus den SVG-Dateien auf der
Platte gebaut (Prinzip „DB=Index, Artefakte=Dateien") und ist jederzeit neu baubar
— es liegt nichts dauerhaft auf der Platte und nichts im Repo.

Der Index hält pro Icon: set_id, name, style, path, is_custom, license_category,
license_spdx. Suche kombiniert Scope × Lizenz × Style × Text (UND).
"""
import json
import logging
import sqlite3
import threading

from app.config import ICON_SETS, ICONS_PATH

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_conn: sqlite3.Connection | None = None

CUSTOM_FILE = ICONS_PATH / "_custom_sets.json"


def _load_custom() -> dict:
    if CUSTOM_FILE.exists():
        try:
            return json.loads(CUSTOM_FILE.read_text())
        except Exception:
            return {}
    return {}


def _new_conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.execute(
        "CREATE TABLE icons(set_id TEXT, name TEXT, style TEXT, path TEXT, "
        "is_custom INT, lic_cat TEXT, lic_spdx TEXT)"
    )
    return c


def build() -> None:
    """Scannt alle Icon-Dateien und baut den Index neu (atomarer Swap)."""
    conn = _new_conn()
    rows: list[tuple] = []

    for sid, cfg in ICON_SETS.items():
        d = ICONS_PATH / sid
        if not d.exists():
            continue
        cat = cfg.license_category
        spdx = cfg.license_spdx or cfg.license
        for f in d.glob("**/*.svg"):
            rel = f.relative_to(d)
            parts = rel.parts
            style = "/".join(parts[:-1]) if len(parts) > 1 else ""
            path = "/icons/" + sid + "/" + rel.with_suffix("").as_posix()
            rows.append((sid, f.stem, style, path, 0, cat, spdx))

    for sid, info in _load_custom().items():
        d = ICONS_PATH / sid
        if not d.exists():
            continue
        for f in d.glob("*.svg"):
            path = "/icons/" + sid + "/" + f.stem
            rows.append((sid, f.stem, "", path, 1, "none", info.get("license", "Custom")))

    conn.executemany("INSERT INTO icons VALUES (?,?,?,?,?,?,?)", rows)
    conn.commit()
    global _conn
    with _LOCK:
        old, _conn = _conn, conn
    if old:
        old.close()
    logger.info(f"Such-Index gebaut: {len(rows)} Einträge")


def ensure() -> None:
    if _conn is None:
        build()


def refresh_set(set_id: str) -> None:
    """Aktualisiert nur EIN Set im Index (schnell, ohne kompletten Rebuild)."""
    ensure()
    d = ICONS_PATH / set_id
    custom = _load_custom()
    rows: list[tuple] = []
    if d.exists():
        if set_id in custom:
            spdx = custom[set_id].get("license", "Custom")
            for f in d.glob("*.svg"):
                rows.append((set_id, f.stem, "", "/icons/" + set_id + "/" + f.stem, 1, "none", spdx))
        elif set_id in ICON_SETS:
            cfg = ICON_SETS[set_id]
            cat, spdx = cfg.license_category, (cfg.license_spdx or cfg.license)
            for f in d.glob("**/*.svg"):
                rel = f.relative_to(d)
                parts = rel.parts
                style = "/".join(parts[:-1]) if len(parts) > 1 else ""
                rows.append((set_id, f.stem, style, "/icons/" + set_id + "/" + rel.with_suffix("").as_posix(), 0, cat, spdx))
    with _LOCK:
        _conn.execute("DELETE FROM icons WHERE set_id=?", (set_id,))
        if rows:
            _conn.executemany("INSERT INTO icons VALUES (?,?,?,?,?,?,?)", rows)
        _conn.commit()


def _styles_for(set_id: str) -> list[str]:
    if _conn is None or not set_id:
        return []
    cur = _conn.execute(
        "SELECT DISTINCT style FROM icons WHERE set_id=? AND style!='' ORDER BY style", (set_id,)
    )
    return [r[0] for r in cur.fetchall()]


def search(query: str = "", scope: str = "set", set_id: str = "", style: str = "",
           license: str = "", page: int = 1, per_page: int = 120) -> dict:
    """
    scope:   set | all | custom
    license: '' | permissive | attribution | with | without
    """
    ensure()

    where: list[str] = []
    params: list = []

    if scope == "custom":
        where.append("is_custom=1")
    elif scope != "all":  # 'set' (Default)
        if not set_id:
            return {"icons": [], "total": 0, "page": page, "per_page": per_page,
                    "pages": 1, "styles": [], "has_font": False, "is_custom": False}
        where.append("set_id=?")
        params.append(set_id)

    if license == "permissive":
        where.append("lic_cat='permissive'")
    elif license == "attribution":
        where.append("lic_cat='attribution'")
    elif license == "with":
        where.append("lic_cat!='none'")
    elif license == "without":
        where.append("lic_cat='none'")

    if query:
        where.append("name LIKE ?")
        params.append(f"%{query}%")
    if style:
        where.append("style=?")
        params.append(style)

    wsql = (" WHERE " + " AND ".join(where)) if where else ""

    with _LOCK:
        # Bei Style-Filter exakt; sonst pro (set,name) entdoppeln (gleiches Icon, mehrere Styles)
        if style:
            base = f"SELECT set_id,name,style,path FROM icons{wsql}"
            total = _conn.execute(f"SELECT COUNT(*) FROM ({base})", params).fetchone()[0]
            rows = _conn.execute(
                f"{base} ORDER BY name LIMIT ? OFFSET ?", params + [per_page, (page - 1) * per_page]
            ).fetchall()
        else:
            base = (f"SELECT set_id,name,MIN(style) s,MIN(path) p FROM icons{wsql} "
                    f"GROUP BY set_id,name")
            total = _conn.execute(f"SELECT COUNT(*) FROM ({base})", params).fetchone()[0]
            rows = _conn.execute(
                f"{base} ORDER BY name LIMIT ? OFFSET ?", params + [per_page, (page - 1) * per_page]
            ).fetchall()

    icons = [{"name": r[1], "style": r[2], "path": r[3], "set_id": r[0]} for r in rows]
    has_font = bool(set_id in ICON_SETS and ICON_SETS[set_id].font_url) if scope != "all" else False

    return {
        "icons": icons,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
        "styles": _styles_for(set_id) if scope == "set" else [],
        "has_font": has_font,
        "is_custom": scope == "custom",
    }
