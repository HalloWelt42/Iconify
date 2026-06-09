"""
Iconify v2.4.0 - Download-Service (Orchestrator)

Schlank: Session/Semaphore/Retry/Progress + Delegation an die jeweilige IconSource
(app/services/sources.py). Set-Spezialfälle stehen NICHT mehr hier.
"""
import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from datetime import datetime

from app.config import ICON_SETS, ICONS_PATH, settings
from app.services.sources import create_source
from app.services import search_index

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
            "percent": self.percent,
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
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(
            total=settings.download_timeout,
            connect=settings.connect_timeout,
            sock_read=settings.read_timeout,
        )
        return aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def _download_single(self, session: aiohttp.ClientSession, url: str,
                               path: Path, progress: DownloadProgress,
                               max_attempts: int = 4) -> dict:
        # Resume: bereits vorhandene Datei nicht erneut laden -> idempotent &
        # wiederaufnehmbar (ein erneuter Import setzt dort fort, wo er aufhörte).
        if path.exists():
            progress.completed += 1
            return {"status": "skipped"}

        async with self.semaphore:
            progress.current_icon = path.stem
            # Beschränkte Retry-Schleife (KEINE Rekursion -> kein Semaphor-Deadlock).
            for attempt in range(1, max_attempts + 1):
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(content)
                            progress.completed += 1
                            return {"status": "success"}
                        if response.status == 429:
                            # Rate-Limit: gedeckelt warten (max ~15s), dann erneut.
                            retry = min(int(response.headers.get("Retry-After", 5)), 15)
                            await asyncio.sleep(retry + attempt)
                            continue
                        if response.status in (500, 502, 503, 504):
                            await asyncio.sleep(attempt)
                            continue
                        progress.failed += 1
                        return {"status": "error", "code": response.status}
                except (asyncio.TimeoutError, aiohttp.ClientError):
                    await asyncio.sleep(attempt)  # kurzer Backoff, dann erneut
                    continue
            progress.failed += 1
            return {"status": "error", "error": "max_attempts"}

    async def download_icon_set(self, set_id: str) -> dict:
        if set_id not in ICON_SETS:
            return {"error": f"Unbekanntes Set: {set_id}"}

        config = ICON_SETS[set_id]
        source = create_source(config)
        output_dir = ICONS_PATH / set_id
        output_dir.mkdir(parents=True, exist_ok=True)

        progress = DownloadProgress()
        progress.status = "downloading"
        progress.message = "Lade Metadaten..."
        progress.styles_count = len(config.styles)
        self.progress[set_id] = progress

        async with self._create_session() as session:
            try:
                # 1. Icon-Liste über die Quelle holen
                icon_list = await source.fetch_icon_list(session)
                if not icon_list:
                    progress.status = "error"
                    progress.message = "Keine Icons gefunden"
                    return {"error": "Keine Icons gefunden"}

                progress.unique_icons = len({i["name"] for i in icon_list})
                progress.total = len(icon_list)
                progress.message = f"Lade {progress.unique_icons} Icons..."
                logger.info(f"{set_id}: {progress.unique_icons} Icons, "
                            f"{len(icon_list)} Downloads")

                # 2. Downloads vorbereiten + parallel ausführen
                tasks = [
                    self._download_single(
                        session,
                        source.source_url(icon),
                        source.target_path(output_dir, icon),
                        progress,
                    )
                    for icon in icon_list
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                progress.status = "error"
                progress.message = f"Fehler: {e}"
                logger.error(f"Download-Fehler {set_id}: {e}")
                return {"error": str(e)}

        # 3. Metadaten aus den TATSÄCHLICHEN Dateien ableiten (echte Zahlen)
        svg_files = list(output_dir.glob("**/*.svg"))
        total_files = len(svg_files)
        unique_count = len({p.stem for p in svg_files})
        meta = {
            "id": set_id,
            "name": config.name,
            "icon_count": unique_count,
            "total_files": total_files,
            "failed": progress.failed,
            "styles": config.styles,
            "downloaded_at": datetime.now().isoformat(),
        }
        (output_dir / "meta.json").write_text(json.dumps(meta, indent=2))

        # Such-Index nach dem Download aktualisieren (blockiert die Loop nicht)
        try:
            await asyncio.to_thread(search_index.build)
        except Exception as e:
            logger.warning(f"Index-Refresh nach {set_id} fehlgeschlagen: {e}")

        progress.status = "completed"
        progress.message = f"{total_files} Dateien ({unique_count} Icons)"
        if progress.failed:
            progress.message += f", {progress.failed} fehlgeschlagen"
        logger.info(f"{set_id}: Abgeschlossen ({total_files} Dateien, "
                    f"{progress.failed} Fehler)")
        return {"success": True}


# Globale Instanz
_downloader = IconDownloader()


async def download_icon_set(set_id: str) -> dict:
    return await _downloader.download_icon_set(set_id)


def get_progress(set_id: str) -> dict:
    if set_id in _downloader.progress:
        return _downloader.progress[set_id].to_dict()
    return None
