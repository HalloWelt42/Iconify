"""
Iconify v2.5.0 - LLM-Anbindung (LM-Studio / OpenAI-kompatibel) — OPTIONAL.

KI ist reiner Zusatz: Ist LM-Studio deaktiviert oder nicht erreichbar, läuft alles
normal weiter (es werden KEINE Exceptions nach außen geworfen). Muster angelehnt an
ImageVault. Verwendet aiohttp (bereits vorhanden). Config liegt im icons-Volume
(gitignored), atomar geschrieben.
"""
import json
import logging
import re

import aiohttp

from app.config import ICONS_PATH

logger = logging.getLogger(__name__)

CONFIG_FILE = ICONS_PATH / "_llm_config.json"
DEFAULTS = {
    "base_url": "http://192.168.178.51:1234",   # LM-Studio auf dem Mac im LAN (wie ImageVault, Port 8040)
    "model": "",                                  # leer = erstes verfügbares Modell
    "enabled": True,
    "timeout": 45,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception:
            pass
    return cfg


def save_config(updates: dict) -> dict:
    cfg = load_config()
    for k, v in updates.items():
        if k in DEFAULTS and v is not None:
            cfg[k] = v
    try:
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, indent=2))
        tmp.replace(CONFIG_FILE)
    except Exception as e:
        logger.warning(f"LLM-Config konnte nicht gespeichert werden: {e}")
    return cfg


def _base(cfg: dict) -> str:
    return (cfg.get("base_url") or "").rstrip("/")


async def check(cfg: dict | None = None) -> dict:
    """Health-Check: ist LM-Studio erreichbar? Liefert verfügbare Modelle."""
    cfg = cfg or load_config()
    base = _base(cfg)
    if not base:
        return {"connected": False, "models": [], "error": "keine URL"}
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(base + "/v1/models") as r:
                if r.status != 200:
                    return {"connected": False, "models": [], "error": f"HTTP {r.status}"}
                data = await r.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                return {"connected": True, "models": models}
    except Exception as e:
        return {"connected": False, "models": [], "error": str(e)[:120]}


async def suggest_terms(query: str) -> dict:
    """Freitext/Prosa -> englische Icon-Suchbegriffe (für die FTS-Suche). Graceful."""
    cfg = load_config()
    if not cfg.get("enabled"):
        return {"connected": False, "terms": [], "error": "KI deaktiviert"}
    base = _base(cfg)
    status = await check(cfg)
    if not status["connected"]:
        return {"connected": False, "terms": [], "error": status.get("error", "nicht verbunden")}

    model = cfg.get("model") or (status["models"][0] if status["models"] else "")
    prompt = (f'Ein Nutzer sucht ein passendes Icon für: "{query}". '
              f"Gib 3 bis 8 ENGLISCHE Icon-Suchbegriffe (einzelne Wörter, wie sie in "
              f"Icon-Bibliotheken vorkommen, z. B. home, trash, arrow-left). "
              f"Antworte NUR mit den Begriffen, kommagetrennt, ohne Erklärung.")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 60,
        "stream": False,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=cfg.get("timeout", 45))
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post(base + "/v1/chat/completions", json=payload) as r:
                if r.status != 200:
                    return {"connected": True, "terms": [], "error": f"HTTP {r.status}"}
                data = await r.json()
                txt = data["choices"][0]["message"]["content"]
        terms = [t.strip().lower() for t in re.split(r"[,\n;]+", txt) if t.strip()]
        terms = [re.sub(r"[^a-z0-9 -]", "", t).strip() for t in terms]
        terms = [t for t in terms if t][:8]
        return {"connected": True, "terms": terms, "model": model}
    except Exception as e:
        logger.warning(f"KI-Suche fehlgeschlagen: {e}")
        return {"connected": True, "terms": [], "error": str(e)[:120]}
