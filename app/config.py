"""
Iconify v2.4.0 - Konfiguration
Icon-Sets deklarativ: jede Quelle über `source_type` (siehe app/services/sources.py).
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings

__version__ = "3.1.0"

ICONS_PATH = Path("/app/icons")


class IconSetConfig(BaseModel):
    """Konfiguration für ein Icon-Set"""
    id: str
    name: str
    metadata_url: str = ""
    svg_pattern: str = ""
    styles: list[str] = ["default"]
    website: str = ""
    icon_count: int = 0
    categories: list[str] = []

    # Quelle (Strategie in app/services/sources.py)
    source_type: str = "json_keys"          # json_keys | fontawesome_json | github_tree
    github_repo: Optional[str] = None        # "owner/repo" (für github_tree)
    github_branch: str = "main"
    github_tree_path: Optional[str] = None   # Unterpfad im Repo, z.B. "icons" / "svg/400"

    # Lizenz / Copyright
    license: str = "MIT"                     # menschenlesbar (Anzeige/Export)
    license_spdx: str = "MIT"                # SPDX-Kennung
    license_url: str = ""
    license_category: str = "permissive"     # permissive | attribution
    requires_attribution: bool = False

    # Webfont / Code-Generierung
    font_url: Optional[str] = None
    font_class_pattern: Optional[str] = None  # z.B. "ti ti-{name}"
    font_family: Optional[str] = None
    font_prefix: str = "icon"                 # Prefix für generierte Fonts


# Alle verfügbaren Icon-Sets
ICON_SETS: dict[str, IconSetConfig] = {
    "tabler": IconSetConfig(
        id="tabler",
        name="Tabler Icons",
        source_type="github_tree",
        github_repo="tabler/tabler-icons",
        github_branch="main",
        github_tree_path="icons",            # icons/outline/*.svg + icons/filled/*.svg
        styles=["outline", "filled"],
        license="MIT",
        license_spdx="MIT",
        license_url="https://github.com/tabler/tabler-icons/blob/main/LICENSE",
        license_category="permissive",
        website="https://tabler.io/icons",
        icon_count=5900,
        font_url="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css",
        font_class_pattern="ti ti-{name}",
        font_family="tabler-icons",
        font_prefix="ti",
    ),
    "lucide": IconSetConfig(
        id="lucide",
        name="Lucide Icons",
        source_type="json_keys",
        metadata_url="https://unpkg.com/lucide-static@latest/tags.json",
        svg_pattern="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg",
        styles=["default"],
        license="ISC",
        license_spdx="ISC",
        license_url="https://github.com/lucide-icons/lucide/blob/main/LICENSE",
        license_category="permissive",
        website="https://lucide.dev",
        icon_count=1600,
        font_prefix="lucide",
    ),
    "bootstrap": IconSetConfig(
        id="bootstrap",
        name="Bootstrap Icons",
        source_type="json_keys",
        metadata_url="https://raw.githubusercontent.com/twbs/icons/main/font/bootstrap-icons.json",
        svg_pattern="https://raw.githubusercontent.com/twbs/icons/main/icons/{name}.svg",
        styles=["default"],
        license="MIT",
        license_spdx="MIT",
        license_url="https://github.com/twbs/icons/blob/main/LICENSE",
        license_category="permissive",
        website="https://icons.getbootstrap.com",
        icon_count=2000,
        font_url="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
        font_class_pattern="bi bi-{name}",
        font_family="bootstrap-icons",
        font_prefix="bi",
    ),
    "fontawesome": IconSetConfig(
        id="fontawesome",
        name="Font Awesome Free",
        source_type="fontawesome_json",
        metadata_url="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/metadata/icons.json",
        svg_pattern="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/{style}/{name}.svg",
        styles=["solid", "regular", "brands"],
        license="CC BY 4.0 (Icons) / MIT (Code)",
        license_spdx="CC-BY-4.0",
        license_url="https://fontawesome.com/license/free",
        license_category="attribution",
        requires_attribution=True,
        website="https://fontawesome.com",
        icon_count=2000,
        font_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6/css/all.min.css",
        font_class_pattern="fa-{style} fa-{name}",
        font_family="Font Awesome 6 Free",
        font_prefix="fa",
    ),
    "heroicons": IconSetConfig(
        id="heroicons",
        name="Heroicons",
        source_type="github_tree",
        github_repo="tailwindlabs/heroicons",
        github_branch="master",
        github_tree_path="src",              # src/24/outline/*.svg etc. (verschachtelt)
        styles=["24/outline", "24/solid", "20/solid", "16/solid"],
        license="MIT",
        license_spdx="MIT",
        license_url="https://github.com/tailwindlabs/heroicons/blob/master/LICENSE",
        license_category="permissive",
        website="https://heroicons.com",
        icon_count=300,
        font_prefix="hero",
    ),
    "feather": IconSetConfig(
        id="feather",
        name="Feather Icons",
        source_type="json_keys",
        metadata_url="https://unpkg.com/feather-icons@latest/dist/icons.json",
        svg_pattern="https://raw.githubusercontent.com/feathericons/feather/main/icons/{name}.svg",
        styles=["default"],
        license="MIT",
        license_spdx="MIT",
        license_url="https://github.com/feathericons/feather/blob/main/LICENSE",
        license_category="permissive",
        website="https://feathericons.com",
        icon_count=287,
        font_prefix="feather",
    ),
    "remix": IconSetConfig(
        id="remix",
        name="Remix Icon",
        source_type="github_tree",
        github_repo="Remix-Design/RemixIcon",
        github_branch="master",
        github_tree_path="icons",            # icons/{Kategorie}/*.svg
        styles=["default"],
        license="Apache 2.0",
        license_spdx="Apache-2.0",
        license_url="https://github.com/Remix-Design/RemixIcon/blob/master/License",
        license_category="permissive",
        website="https://remixicon.com",
        icon_count=3000,
        font_url="https://cdn.jsdelivr.net/npm/remixicon@4/fonts/remixicon.css",
        font_class_pattern="ri-{name}",
        font_family="remixicon",
        font_prefix="ri",
    ),
    "phosphor": IconSetConfig(
        id="phosphor",
        name="Phosphor Icons",
        source_type="github_tree",
        github_repo="phosphor-icons/core",
        github_branch="main",
        github_tree_path="assets",           # assets/{style}/*.svg (alle 6 Styles)
        styles=["regular", "bold", "fill", "light", "thin", "duotone"],
        license="MIT",
        license_spdx="MIT",
        license_url="https://github.com/phosphor-icons/core/blob/main/LICENSE",
        license_category="permissive",
        website="https://phosphoricons.com",
        icon_count=1500,
        font_prefix="ph",
    ),
    "material-symbols": IconSetConfig(
        id="material-symbols",
        name="Material Symbols",
        source_type="github_tree",
        github_repo="marella/material-symbols",
        github_branch="main",
        github_tree_path="svg/400",          # svg/400/{outlined,rounded,sharp}/*.svg
        styles=["outlined", "rounded", "sharp"],
        license="Apache 2.0",
        license_spdx="Apache-2.0",
        license_url="https://github.com/google/material-design-icons/blob/master/LICENSE",
        license_category="permissive",
        website="https://fonts.google.com/icons",
        icon_count=3700,
        font_url="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined",
        font_class_pattern="material-symbols-{style}",
        font_family="Material Symbols Outlined",
        font_prefix="ms",
    ),
    "mdi": IconSetConfig(
        id="mdi",
        name="Material Design Icons",
        source_type="github_tree",
        github_repo="Templarian/MaterialDesign",
        github_branch="master",
        github_tree_path="svg",              # svg/*.svg (flach, ~7500)
        styles=["default"],
        license="Apache 2.0",
        license_spdx="Apache-2.0",
        license_url="https://github.com/Templarian/MaterialDesign/blob/master/LICENSE",
        license_category="permissive",
        website="https://pictogrammers.com/library/mdi/",
        icon_count=7500,
        font_url="https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css",
        font_class_pattern="mdi mdi-{name}",
        font_family="Material Design Icons",
        font_prefix="mdi",
    ),
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
    # Optionaler GitHub-Token für höheres API-Rate-Limit beim Import
    github_token: str = ""

    class Config:
        env_prefix = "ICONIFY_"


settings = Settings()
