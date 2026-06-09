"""
Iconify v2.5.0 - LLM/KI-API (LM-Studio, optional)
Konfiguration + Verbindungstest. Die eigentliche KI-Suche liegt als
/api/icons/ai-search in app/api/icons.py (liefert Icons).
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import llm

router = APIRouter()


class ConfigUpdate(BaseModel):
    base_url: str | None = None
    model: str | None = None
    enabled: bool | None = None
    timeout: int | None = None


@router.get("/config")
async def get_config():
    cfg = llm.load_config()
    return {"config": cfg, "status": await llm.check(cfg)}


@router.put("/config")
async def put_config(update: ConfigUpdate):
    cfg = llm.save_config(update.dict(exclude_none=True))
    return {"config": cfg, "status": await llm.check(cfg)}


@router.post("/test")
async def test_connection():
    return await llm.check()
