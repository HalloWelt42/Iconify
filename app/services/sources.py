"""
Iconify v2.4.0 - Icon-Quellen (Strategie-Muster)

Jedes Icon-Set wird über eine IconSource bedient. Eine Quelle weiß dreierlei:
  * fetch_icon_list(session) -> Liste von dicts (mind. 'name')
  * source_url(icon)         -> von welcher URL die SVG geladen wird
  * target_path(out, icon)   -> wo die SVG lokal landet (Pfad-Vertrag!)

Damit verschwinden die früher über downloader.py verstreuten Set-Spezialfälle.
Die Set->Quelle-Zuordnung steht deklarativ in ICON_SETS (config.py, Feld `source_type`).
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import aiohttp

from app.config import IconSetConfig, settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"


class IconSource(ABC):
    """Basis-Strategie für eine Icon-Quelle."""

    def __init__(self, config: IconSetConfig):
        self.config = config

    @abstractmethod
    async def fetch_icon_list(self, session: aiohttp.ClientSession) -> list[dict]:
        """Liefert die Icon-Liste. Jeder Eintrag hat mind. 'name'."""
        raise NotImplementedError

    def source_url(self, icon: dict) -> str:
        """Standard: svg_pattern mit name/style/category füllen."""
        return self.config.svg_pattern.format(
            name=icon["name"],
            style=icon.get("style", self.config.styles[0] if self.config.styles else "default"),
            category=icon.get("category", ""),
        )

    def target_path(self, output_dir: Path, icon: dict) -> Path:
        """
        Zentraler Pfad-Vertrag (identisch zur historischen Logik in
        download_icon_set): flach | {style}/ | verschachtelt | {category}/.
        """
        category = icon.get("category", "")
        style = icon.get("style", "")
        if category:
            return output_dir / category / f"{icon['name']}.svg"
        if len(self.config.styles) > 1 and style:
            return output_dir.joinpath(*style.split("/"), f"{icon['name']}.svg")
        return output_dir / f"{icon['name']}.svg"


async def _load_json(session: aiohttp.ClientSession, url: str) -> dict:
    """Lädt eine (ggf. große) JSON-Metadatendatei mit langzügigem Timeout."""
    timeout = aiohttp.ClientTimeout(
        total=settings.metadata_timeout,
        connect=settings.connect_timeout,
        sock_read=settings.metadata_timeout,
    )
    logger.info(f"Lade Metadaten: {url}")
    async with session.get(url, timeout=timeout) as resp:
        if resp.status != 200:
            raise Exception(f"HTTP {resp.status} für {url}")
        text = await resp.text()
    logger.info(f"Metadaten: {len(text)} bytes")
    return json.loads(text)


class JsonKeysSource(IconSource):
    """JSON, dessen Schlüssel die Icon-Namen sind (tabler-Altformat, bootstrap, lucide, feather)."""

    async def fetch_icon_list(self, session: aiohttp.ClientSession) -> list[dict]:
        data = await _load_json(session, self.config.metadata_url)
        return [{"name": name} for name in data.keys()]


class FontAwesomeJsonSource(IconSource):
    """Font-Awesome-Metadaten: pro Icon mehrere Styles, gefiltert gegen config.styles."""

    async def fetch_icon_list(self, session: aiohttp.ClientSession) -> list[dict]:
        data = await _load_json(session, self.config.metadata_url)
        icons: list[dict] = []
        for name, info in data.items():
            for style in info.get("styles", ["solid"]):
                if style in self.config.styles:
                    icons.append({"name": name, "style": style})
        return icons


class GithubTreeSource(IconSource):
    """
    Listet alle SVGs eines GitHub-Repos über die **Git-Trees-API**
    (`/git/trees/{sha}?recursive=1`). Das umgeht das 1000-Einträge-Limit der
    Contents-API (Ursache der gekappten mdi/phosphor-Zählung) und liefert die
    echten Dateinamen aller Styles in EINEM rekursiven Aufruf je Set.

    Die lokale Pfadstruktur **spiegelt** die Unterstruktur unterhalb von
    `github_tree_path` — dadurch leitet catalog.search_icons Style/Kategorie
    weiterhin korrekt aus den Verzeichnissen ab.
    """

    @property
    def _headers(self) -> dict:
        h = {"User-Agent": "Iconify", "Accept": "application/vnd.github+json"}
        if settings.github_token:
            h["Authorization"] = f"Bearer {settings.github_token}"
        return h

    async def _tree(self, session: aiohttp.ClientSession, repo: str, ref: str) -> dict | None:
        url = f"{GITHUB_API}/repos/{repo}/git/trees/{ref}"
        timeout = aiohttp.ClientTimeout(total=settings.metadata_timeout,
                                        connect=settings.connect_timeout)
        async with session.get(url, headers=self._headers, timeout=timeout) as resp:
            if resp.status != 200:
                logger.warning(f"GitHub-API {resp.status}: {url}")
                return None
            return await resp.json()

    async def fetch_icon_list(self, session: aiohttp.ClientSession) -> list[dict]:
        repo = self.config.github_repo
        branch = self.config.github_branch
        base = (self.config.github_tree_path or "").strip("/")
        if not repo or not base:
            logger.error(f"{self.config.id}: github_repo/github_tree_path fehlen")
            return []

        # 1. Vom Branch-Root zur SHA des Basis-Unterbaums laufen
        root = await self._tree(session, repo, branch)
        if not root:
            return []
        sha = root.get("sha")
        entries = root.get("tree", [])
        segments = base.split("/")
        for i, seg in enumerate(segments):
            child = next((e for e in entries
                          if e.get("type") == "tree" and e.get("path") == seg), None)
            if not child:
                logger.warning(f"{self.config.id}: Pfad '{base}' nicht im Repo {repo}@{branch}")
                return []
            sha = child["sha"]
            if i < len(segments) - 1:
                node = await self._tree(session, repo, sha)
                if not node:
                    return []
                entries = node.get("tree", [])

        # 2. Basis-Unterbaum rekursiv auflisten
        final = await self._tree(session, repo, f"{sha}?recursive=1")
        if not final:
            return []
        if final.get("truncated"):
            logger.warning(f"{self.config.id}: GitHub-Baum ist abgeschnitten (truncated) "
                           f"— Set evtl. unvollständig")

        icons: list[dict] = []
        for e in final.get("tree", []):
            path = e.get("path", "")
            if e.get("type") == "blob" and path.endswith(".svg"):
                name = path.split("/")[-1][:-4]
                icons.append({"name": name, "rel": path})
        logger.info(f"{self.config.id}: {len(icons)} SVGs im Baum {repo}/{base}")
        return icons

    def source_url(self, icon: dict) -> str:
        base = (self.config.github_tree_path or "").strip("/")
        return f"{GITHUB_RAW}/{self.config.github_repo}/{self.config.github_branch}/{base}/{icon['rel']}"

    def target_path(self, output_dir: Path, icon: dict) -> Path:
        # Unterstruktur 1:1 spiegeln (outline/, regular/, 24/outline/, Device/ ...)
        return output_dir.joinpath(*icon["rel"].split("/"))


_SOURCE_REGISTRY: dict[str, type[IconSource]] = {
    "json_keys": JsonKeysSource,
    "fontawesome_json": FontAwesomeJsonSource,
    "github_tree": GithubTreeSource,
}


def create_source(config: IconSetConfig) -> IconSource:
    """Factory: erzeugt die passende IconSource anhand von config.source_type."""
    cls = _SOURCE_REGISTRY.get(config.source_type)
    if cls is None:
        raise ValueError(f"Unbekannter source_type: {config.source_type!r} (Set {config.id})")
    return cls(config)
