"""
Iconify v2.2.0 - Download-Service
Korrektes Async-Handling mit Timeouts für große Metadaten-Dateien
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from datetime import datetime

from app.config import ICON_SETS, ICONS_PATH, settings, IconSetConfig

logger = logging.getLogger(__name__)


class DownloadProgress:
    """Progress-Tracker"""
    def __init__(self, total: int = 0):
        self.total = total
        self.unique_icons = 0
        self.styles_count = 1
        self.completed = 0
        self.failed = 0
        self.status = "pending"
        self.message = ""
        self.current_icon = ""
        self.percent = 0
    
    def to_dict(self) -> dict:
        if self.total > 0:
            self.percent = int((self.completed / self.total) * 100)
        return {
            "total": self.total,
            "unique_icons": self.unique_icons,
            "styles_count": self.styles_count,
            "completed": self.completed,
            "failed": self.failed,
            "status": self.status,
            "message": self.message,
            "current_icon": self.current_icon,
            "percent": self.percent
        }


class IconDownloader:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        self.progress: dict[str, DownloadProgress] = {}
    
    def _create_session(self) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=10,
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )
        timeout = aiohttp.ClientTimeout(
            total=settings.download_timeout,
            connect=settings.connect_timeout,
            sock_read=settings.read_timeout
        )
        return aiohttp.ClientSession(connector=connector, timeout=timeout)
    
    async def _download_single(self, session: aiohttp.ClientSession, url: str, path: Path, progress: DownloadProgress) -> dict:
        async with self.semaphore:
            try:
                progress.current_icon = path.stem
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(content)
                        progress.completed += 1
                        return {"status": "success"}
                    elif response.status == 429:
                        retry = int(response.headers.get("Retry-After", 30))
                        logger.warning(f"Rate-Limited, warte {retry}s")
                        await asyncio.sleep(retry)
                        return await self._download_single(session, url, path, progress)
                    else:
                        progress.failed += 1
                        return {"status": "error", "code": response.status}
            except asyncio.TimeoutError:
                progress.failed += 1
                return {"status": "timeout"}
            except Exception as e:
                progress.failed += 1
                return {"status": "error", "error": str(e)}
    
    async def download_icon_set(self, set_id: str) -> dict:
        if set_id not in ICON_SETS:
            return {"error": f"Unbekanntes Set: {set_id}"}
        
        config = ICON_SETS[set_id]
        output_dir = ICONS_PATH / set_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        progress = DownloadProgress()
        progress.status = "downloading"
        progress.message = "Lade Metadaten..."
        self.progress[set_id] = progress
        
        async with self._create_session() as session:
            try:
                # 1. Icon-Liste laden
                icon_list = await self._fetch_icon_list(session, config)
                
                if not icon_list:
                    progress.status = "error"
                    progress.message = "Keine Icons gefunden"
                    return {"error": "Keine Icons gefunden"}
                
                progress.unique_icons = len(set(
                    i.get("name", i) if isinstance(i, dict) else i 
                    for i in icon_list
                ))
                progress.styles_count = len(config.styles)
                progress.total = len(icon_list)
                progress.message = f"Lade {progress.unique_icons} Icons..."
                
                logger.info(f"{set_id}: {progress.unique_icons} Icons, {len(icon_list)} Downloads")
                
                # 2. Downloads vorbereiten
                tasks = []
                for icon_info in icon_list:
                    name = icon_info.get("name", icon_info) if isinstance(icon_info, dict) else icon_info
                    style = icon_info.get("style", config.styles[0]) if isinstance(icon_info, dict) else config.styles[0]
                    category = icon_info.get("category", "") if isinstance(icon_info, dict) else ""
                    
                    # URL-Name (Material Symbols: - zu _)
                    url_name = name.replace("-", "_") if set_id == "material-symbols" else name
                    
                    url = config.svg_pattern.format(
                        name=url_name, 
                        style=style,
                        category=category
                    )
                    
                    # Dateipfad - abhängig von Set-Struktur
                    if set_id == "remix" and category:
                        # Remix: Nach Kategorie organisiert
                        file_path = output_dir / category / f"{name}.svg"
                    elif len(config.styles) > 1 and style:
                        # Style kann verschachtelt sein (z.B. "24/outline")
                        style_path = Path(*style.split("/")) if "/" in style else Path(style)
                        file_path = output_dir / style_path / f"{name}.svg"
                    else:
                        file_path = output_dir / f"{name}.svg"
                    
                    tasks.append(self._download_single(session, url, file_path, progress))
                
                # 3. Parallel ausführen
                await asyncio.gather(*tasks, return_exceptions=True)
                
            except Exception as e:
                progress.status = "error"
                progress.message = f"Fehler: {e}"
                logger.error(f"Download-Fehler {set_id}: {e}")
                return {"error": str(e)}
        
        # 4. Metadaten speichern
        meta = {
            "id": set_id,
            "name": config.name,
            "icon_count": progress.unique_icons,
            "total_files": progress.completed,
            "failed": progress.failed,
            "styles": config.styles,
            "downloaded_at": datetime.now().isoformat()
        }
        (output_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        
        progress.status = "completed"
        progress.message = f"{progress.completed} Icons heruntergeladen"
        
        logger.info(f"{set_id}: Abgeschlossen ({progress.completed}/{progress.total})")
        return {"success": True}
    
    async def _fetch_icon_list(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Lädt Icon-Liste - mit langem Timeout für große Dateien"""
        
        # Spezielle Handler für Sets ohne JSON-Metadaten
        if config.id == "remix":
            return await self._fetch_remix_icons(session, config)
        
        if config.id == "phosphor":
            return await self._fetch_phosphor_icons(session, config)
        
        if config.id == "mdi":
            return await self._fetch_mdi_icons(session, config)
        
        if not config.metadata_url:
            if config.github_contents_url:
                return await self._fetch_github_directory(session, config)
            return []
        
        logger.info(f"Lade Metadaten: {config.metadata_url}")
        
        # Langer Timeout für große JSON-Dateien (Material Symbols: 7.7 MB)
        timeout = aiohttp.ClientTimeout(
            total=settings.metadata_timeout,
            connect=settings.connect_timeout,
            sock_read=settings.metadata_timeout
        )
        
        try:
            async with session.get(config.metadata_url, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                text = await response.text()
                logger.info(f"Metadaten: {len(text)} bytes")
                
                data = json.loads(text)
        except asyncio.TimeoutError:
            raise Exception("Timeout beim Laden der Metadaten")
        
        # Format parsen je nach Set
        if config.id == "tabler":
            return [{"name": name} for name in data.keys()]
        
        elif config.id == "bootstrap":
            return [{"name": name} for name in data.keys()]
        
        elif config.id == "fontawesome":
            icons = []
            for name, info in data.items():
                for style in info.get("styles", ["solid"]):
                    if style in config.styles:
                        icons.append({"name": name, "style": style})
            return icons
        
        elif config.id in ["lucide", "feather"]:
            return [{"name": name} for name in data.keys()]
        
        elif config.id == "remix":
            # Remix Icons via GitHub API laden (tags.json hat keine Kategorien)
            return await self._fetch_remix_icons(session, config)
        
        elif config.id == "phosphor":
            return await self._fetch_phosphor_icons(session, config)
        
        elif config.id == "material-symbols":
            # Iconify JSON Format
            icons = []
            icons_data = data.get("icons", {})
            logger.info(f"Material Symbols: {len(icons_data)} Icons")
            for name in icons_data.keys():
                for style in config.styles:
                    icons.append({"name": name, "style": style})
            return icons
        
        else:
            return [{"name": name} for name in data.keys()]
    
    async def _fetch_github_directory(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Lädt Icons via GitHub API"""
        icons = []
        
        # Heroicons: Styles sind Unterordner, müssen separat geladen werden
        if config.id == "heroicons":
            return await self._fetch_heroicons(session, config)
        
        try:
            async with session.get(config.github_contents_url) as response:
                if response.status == 200:
                    items = await response.json()
                    
                    # Remix: Kategorien sind Unterordner
                    if config.id == "remix":
                        for item in items:
                            if item.get("type") == "dir":
                                category = item["name"]
                                cat_url = item["url"]
                                try:
                                    async with session.get(cat_url) as cat_response:
                                        if cat_response.status == 200:
                                            files = await cat_response.json()
                                            for f in files:
                                                if f.get("name", "").endswith(".svg"):
                                                    icons.append({
                                                        "name": f["name"].replace(".svg", ""),
                                                        "category": category
                                                    })
                                except Exception as e:
                                    logger.warning(f"Remix Kategorie {category} Fehler: {e}")
                    else:
                        for f in items:
                            if f.get("name", "").endswith(".svg"):
                                name = f["name"].replace(".svg", "")
                                for style in config.styles:
                                    icons.append({"name": name, "style": style})
        except Exception as e:
            logger.error(f"GitHub API Fehler: {e}")
        return icons
    
    async def _fetch_heroicons(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Heroicons - Jeder Style separat laden"""
        icons = []
        base_url = "https://api.github.com/repos/tailwindlabs/heroicons/contents/src"
        
        for style in config.styles:
            url = f"{base_url}/{style}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        files = await response.json()
                        for f in files:
                            if f.get("name", "").endswith(".svg"):
                                icons.append({
                                    "name": f["name"].replace(".svg", ""),
                                    "style": style
                                })
                        logger.info(f"Heroicons {style}: {len([i for i in icons if i.get('style') == style])} Icons")
                    else:
                        logger.warning(f"Heroicons {style}: HTTP {response.status}")
            except Exception as e:
                logger.warning(f"Heroicons {style} Fehler: {e}")
        
        logger.info(f"Heroicons total: {len(icons)} Icons")
        return icons
    
    async def _fetch_remix_icons(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Remix Icons via GitHub Directory Listing"""
        icons = []
        # Aktuelle Kategorien aus dem RemixIcon Repo (Stand 2025)
        categories = [
            "Arrows", "Buildings", "Business", "Communication", "Design", 
            "Development", "Device", "Document", "Editor", "Finance", 
            "Health", "Logos", "Map", "Media", "Others", "System", 
            "User", "Weather"
        ]
        
        for category in categories:
            url = f"https://api.github.com/repos/Remix-Design/RemixIcon/contents/icons/{category}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        files = await response.json()
                        for f in files:
                            if f.get("name", "").endswith(".svg"):
                                icons.append({
                                    "name": f["name"].replace(".svg", ""),
                                    "category": category
                                })
                    elif response.status == 404:
                        logger.debug(f"Remix Kategorie nicht gefunden: {category}")
                    else:
                        logger.warning(f"Remix {category}: HTTP {response.status}")
            except Exception as e:
                logger.warning(f"Remix {category} Fehler: {e}")
        
        logger.info(f"Remix: {len(icons)} Icons gefunden")
        return icons
    
    async def _fetch_phosphor_icons(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Phosphor Icons via GitHub Directory"""
        icons = []
        
        # Hole Icon-Liste aus regular Style (alle Styles haben gleiche Icons)
        url = "https://api.github.com/repos/phosphor-icons/core/contents/assets/regular"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    files = await response.json()
                    for f in files:
                        if f.get("name", "").endswith(".svg"):
                            name = f["name"].replace(".svg", "")
                            # Für jeden Style ein Eintrag
                            for style in config.styles:
                                icons.append({"name": name, "style": style})
                else:
                    logger.error(f"Phosphor: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Phosphor Fehler: {e}")
        
        logger.info(f"Phosphor: {len(icons)} Downloads ({len(icons)//len(config.styles)} Icons × {len(config.styles)} Styles)")
        return icons

    async def _fetch_mdi_icons(self, session: aiohttp.ClientSession, config: IconSetConfig) -> list[dict]:
        """Material Design Icons via GitHub Directory (paginiert wegen ~7500 Icons)"""
        icons = []
        
        # GitHub API gibt max 1000 Einträge zurück, wir müssen paginieren
        base_url = "https://api.github.com/repos/Templarian/MaterialDesign/contents/svg"
        page = 1
        per_page = 1000
        
        try:
            while True:
                url = f"{base_url}?per_page={per_page}&page={page}"
                async with session.get(url) as response:
                    if response.status == 200:
                        files = await response.json()
                        if not files:
                            break
                        
                        for f in files:
                            if f.get("name", "").endswith(".svg"):
                                name = f["name"].replace(".svg", "")
                                icons.append({"name": name})
                        
                        logger.info(f"MDI Page {page}: {len(files)} Dateien")
                        
                        # Wenn weniger als per_page, sind wir fertig
                        if len(files) < per_page:
                            break
                        page += 1
                    elif response.status == 403:
                        # Rate Limit
                        logger.warning("MDI: Rate Limit erreicht")
                        break
                    else:
                        logger.error(f"MDI: HTTP {response.status}")
                        break
        except Exception as e:
            logger.error(f"MDI Fehler: {e}")
        
        logger.info(f"Material Design Icons: {len(icons)} Icons geladen")
        return icons


# Globale Instanz
_downloader = IconDownloader()


async def download_icon_set(set_id: str) -> dict:
    return await _downloader.download_icon_set(set_id)


def get_progress(set_id: str) -> dict:
    if set_id in _downloader.progress:
        return _downloader.progress[set_id].to_dict()
    return None
