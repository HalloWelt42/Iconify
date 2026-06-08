"""
Iconify v2.3.0 - Self-hosted Icon Font Manager
Mit Custom Font Generator und eigenen Icon-Sets
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pathlib import Path
import logging

from app.config import settings, __version__, ICONS_PATH
from app.api import sets, icons, font, custom

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Iconify", version=__version__)

# API Routes
app.include_router(sets.router, prefix="/api/sets", tags=["sets"])
app.include_router(icons.router, prefix="/api/icons", tags=["icons"])
app.include_router(font.router, prefix="/api/font", tags=["font"])
app.include_router(custom.router, prefix="/api/custom", tags=["custom"])

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/icons", StaticFiles(directory=str(ICONS_PATH)), name="icons")

# Temp directory für Font-Downloads
TEMP_PATH = Path("/app/temp")
TEMP_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    return FileResponse("app/static/index.html")


@app.get("/favicon.ico")
async def favicon():
    # Einfaches SVG Favicon
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect fill="#4f46e5" width="100" height="100" rx="20"/>
        <text x="50" y="72" text-anchor="middle" fill="white" font-size="60" font-family="system-ui">◆</text>
    </svg>'''
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": __version__}


@app.on_event("startup")
async def startup():
    ICONS_PATH.mkdir(parents=True, exist_ok=True)
    logger.info(f"🎨 Iconify v{__version__} gestartet")
    logger.info(f"📁 Icons: {ICONS_PATH}")
    logger.info(f"🌐 http://0.0.0.0:{settings.port}")
