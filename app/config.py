"""
Iconify v2.2.0 - Konfiguration
Mit Material Design Icons und Original-Font-Prefixes
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings

__version__ = "2.3.1"

ICONS_PATH = Path("/app/icons")


class IconSetConfig(BaseModel):
    """Konfiguration für ein Icon-Set"""
    id: str
    name: str
    metadata_url: str
    svg_pattern: str
    styles: list[str] = ["default"]
    license: str = "MIT"
    website: str = ""
    icon_count: int = 0
    font_url: Optional[str] = None
    github_contents_url: Optional[str] = None
    categories: list[str] = []
    # Font-Code Generierung
    font_class_pattern: Optional[str] = None  # z.B. "ti ti-{name}"
    font_family: Optional[str] = None
    # Original Font-Prefix für Custom Font Generation
    font_prefix: str = "icon"  # Standard-Prefix für generierte Fonts


# Alle verfügbaren Icon-Sets
ICON_SETS: dict[str, IconSetConfig] = {
    "tabler": IconSetConfig(
        id="tabler",
        name="Tabler Icons",
        metadata_url="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons.json",
        svg_pattern="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/icons/{style}/{name}.svg",
        styles=["outline", "filled"],
        license="MIT",
        website="https://tabler-icons.io",
        icon_count=5963,
        font_url="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css",
        font_class_pattern="ti ti-{name}",
        font_family="tabler-icons",
        font_prefix="ti"
    ),
    "lucide": IconSetConfig(
        id="lucide",
        name="Lucide Icons",
        metadata_url="https://unpkg.com/lucide-static@latest/tags.json",
        svg_pattern="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg",
        styles=["default"],
        license="ISC",
        website="https://lucide.dev",
        icon_count=1500,
        font_prefix="lucide"
    ),
    "bootstrap": IconSetConfig(
        id="bootstrap",
        name="Bootstrap Icons",
        metadata_url="https://raw.githubusercontent.com/twbs/icons/main/font/bootstrap-icons.json",
        svg_pattern="https://raw.githubusercontent.com/twbs/icons/main/icons/{name}.svg",
        styles=["default"],
        license="MIT",
        website="https://icons.getbootstrap.com",
        icon_count=2000,
        font_url="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
        font_class_pattern="bi bi-{name}",
        font_family="bootstrap-icons",
        font_prefix="bi"
    ),
    "fontawesome": IconSetConfig(
        id="fontawesome",
        name="Font Awesome Free",
        metadata_url="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/metadata/icons.json",
        svg_pattern="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/{style}/{name}.svg",
        styles=["solid", "regular", "brands"],
        license="CC BY 4.0 / MIT",
        website="https://fontawesome.com",
        icon_count=2000,
        font_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6/css/all.min.css",
        font_class_pattern="fa-{style} fa-{name}",
        font_family="Font Awesome 6 Free",
        font_prefix="fa"
    ),
    "heroicons": IconSetConfig(
        id="heroicons",
        name="Heroicons",
        metadata_url="",
        svg_pattern="https://raw.githubusercontent.com/tailwindlabs/heroicons/master/src/{style}/{name}.svg",
        styles=["24/outline", "24/solid", "20/solid"],
        license="MIT",
        website="https://heroicons.com",
        icon_count=300,
        github_contents_url="https://api.github.com/repos/tailwindlabs/heroicons/contents/src/24/outline",
        font_prefix="hero"
    ),
    "feather": IconSetConfig(
        id="feather",
        name="Feather Icons",
        metadata_url="https://unpkg.com/feather-icons@latest/dist/icons.json",
        svg_pattern="https://raw.githubusercontent.com/feathericons/feather/main/icons/{name}.svg",
        styles=["default"],
        license="MIT",
        website="https://feathericons.com",
        icon_count=287,
        font_prefix="feather"
    ),
    "remix": IconSetConfig(
        id="remix",
        name="Remix Icon",
        metadata_url="",
        svg_pattern="https://raw.githubusercontent.com/Remix-Design/RemixIcon/master/icons/{category}/{name}.svg",
        styles=["default"],
        license="Apache 2.0",
        website="https://remixicon.com",
        icon_count=3100,
        font_url="https://cdn.jsdelivr.net/npm/remixicon@4/fonts/remixicon.css",
        font_class_pattern="ri-{name}",
        font_family="remixicon",
        font_prefix="ri"
    ),
    "phosphor": IconSetConfig(
        id="phosphor",
        name="Phosphor Icons",
        metadata_url="",
        svg_pattern="https://raw.githubusercontent.com/phosphor-icons/core/main/assets/{style}/{name}.svg",
        styles=["regular", "bold", "fill", "light", "thin", "duotone"],
        license="MIT",
        website="https://phosphoricons.com",
        icon_count=1248,
        github_contents_url="https://api.github.com/repos/phosphor-icons/core/contents/assets/regular",
        font_prefix="ph"
    ),
    "material-symbols": IconSetConfig(
        id="material-symbols",
        name="Material Symbols",
        metadata_url="https://cdn.jsdelivr.net/npm/@iconify-json/material-symbols/icons.json",
        svg_pattern="https://fonts.gstatic.com/s/i/short-term/release/materialsymbols{style}/{name}/default/48px.svg",
        styles=["outlined", "rounded", "sharp"],
        license="Apache 2.0",
        website="https://fonts.google.com/icons",
        icon_count=3200,
        font_url="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined",
        font_class_pattern="material-symbols-{style}",
        font_family="Material Symbols Outlined",
        font_prefix="ms"
    ),
    "mdi": IconSetConfig(
        id="mdi",
        name="Material Design Icons",
        metadata_url="",
        svg_pattern="https://raw.githubusercontent.com/Templarian/MaterialDesign/master/svg/{name}.svg",
        styles=["default"],
        license="Apache 2.0 / MIT",
        website="https://materialdesignicons.com",
        icon_count=7500,
        github_contents_url="https://api.github.com/repos/Templarian/MaterialDesign/contents/svg",
        font_url="https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css",
        font_class_pattern="mdi mdi-{name}",
        font_family="Material Design Icons",
        font_prefix="mdi"
    )
}


class Settings(BaseSettings):
    """App-Einstellungen"""
    host: str = "0.0.0.0"
    port: int = 8766
    debug: bool = False
    max_concurrent_downloads: int = 20
    download_timeout: int = 120
    connect_timeout: int = 15
    read_timeout: int = 90
    metadata_timeout: int = 180
    
    class Config:
        env_prefix = "ICONIFY_"


settings = Settings()
