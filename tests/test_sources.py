"""
Charakterisierungs-/Vertragstests für die Icon-Quellen (app/services/sources.py).

Wichtigster Vertrag: die erzeugte On-Disk-Pfadstruktur unter icons/{set_id}/...
(flach | {style}/ | verschachtelt 24/outline/ | {category}/). catalog.search_icons,
api/icons.py und fontgen.py leiten Style/Fundort NUR aus diesen Pfaden ab — ändert sich
die Pfadlogik, brechen Suche, Auslieferung und Font-Generierung.
"""
from pathlib import Path

import aiohttp
from aioresponses import aioresponses

from app.config import IconSetConfig
from app.services.sources import create_source


def _cfg(**kw) -> IconSetConfig:
    base = dict(id="x", name="X", metadata_url="", svg_pattern="")
    base.update(kw)
    return IconSetConfig(**base)


# --------------------------------------------------------------------------- #
# Pfad-Vertrag (target_path) — das Sicherheitsnetz für den Refactor
# --------------------------------------------------------------------------- #

def test_target_path_flat():
    src = create_source(_cfg(source_type="json_keys", styles=["default"]))
    assert src.target_path(Path("/o"), {"name": "home"}) == Path("/o/home.svg")


def test_target_path_style_dir():
    src = create_source(_cfg(source_type="fontawesome_json",
                             styles=["solid", "regular", "brands"]))
    assert src.target_path(Path("/o"), {"name": "github", "style": "brands"}) == \
        Path("/o/brands/github.svg")


def test_target_path_nested_style():
    # heroicons-artiger Stil "24/outline" muss zu zwei Ebenen werden
    src = create_source(_cfg(source_type="json_keys", styles=["24/outline", "24/solid"]))
    assert src.target_path(Path("/o"), {"name": "inbox", "style": "24/outline"}) == \
        Path("/o/24/outline/inbox.svg")


def test_target_path_category():
    src = create_source(_cfg(source_type="json_keys", styles=["default"]))
    assert src.target_path(Path("/o"), {"name": "battery", "category": "Device"}) == \
        Path("/o/Device/battery.svg")


# --------------------------------------------------------------------------- #
# JSON-Quellen
# --------------------------------------------------------------------------- #

async def test_json_keys_list_and_url():
    cfg = _cfg(id="lucide", source_type="json_keys", styles=["default"],
               metadata_url="https://meta.test/tags.json",
               svg_pattern="https://raw.test/icons/{name}.svg")
    src = create_source(cfg)
    with aioresponses() as m:
        m.get("https://meta.test/tags.json", payload={"home": [], "user": [], "star": []})
        async with aiohttp.ClientSession() as s:
            icons = await src.fetch_icon_list(s)
    assert sorted(i["name"] for i in icons) == ["home", "star", "user"]
    assert src.source_url({"name": "home"}) == "https://raw.test/icons/home.svg"


async def test_fontawesome_style_filtering():
    cfg = _cfg(id="fontawesome", source_type="fontawesome_json",
               styles=["solid", "regular", "brands"],
               metadata_url="https://meta.test/icons.json",
               svg_pattern="https://raw.test/svgs/{style}/{name}.svg")
    src = create_source(cfg)
    data = {
        "star": {"styles": ["solid", "regular"]},
        "github": {"styles": ["brands"]},
        "ghost": {"styles": ["thin"]},  # 'thin' nicht in config.styles -> verworfen
    }
    with aioresponses() as m:
        m.get("https://meta.test/icons.json", payload=data)
        async with aiohttp.ClientSession() as s:
            icons = await src.fetch_icon_list(s)
    got = sorted((i["name"], i["style"]) for i in icons)
    assert got == [("github", "brands"), ("star", "regular"), ("star", "solid")]
    assert src.source_url({"name": "github", "style": "brands"}) == \
        "https://raw.test/svgs/brands/github.svg"


# --------------------------------------------------------------------------- #
# GitHub-Trees-Quelle (ersetzt das 1000er-gekappte Contents-API-Listing)
# --------------------------------------------------------------------------- #

async def test_github_tree_single_segment():
    # tabler-/heroicons-artig: tree_path mit einem Segment
    cfg = _cfg(id="tabler", source_type="github_tree",
               github_repo="test/repo", github_branch="main", github_tree_path="icons",
               styles=["outline", "filled"])
    src = create_source(cfg)
    api = "https://api.github.com/repos/test/repo/git/trees"
    with aioresponses() as m:
        m.get(f"{api}/main", payload={"sha": "ROOT", "tree": [
            {"path": "icons", "type": "tree", "sha": "ICONS"},
            {"path": "README.md", "type": "blob"},
        ]})
        m.get(f"{api}/ICONS?recursive=1", payload={"sha": "ICONS", "truncated": False, "tree": [
            {"path": "outline/home.svg", "type": "blob"},
            {"path": "filled/home.svg", "type": "blob"},
            {"path": "outline", "type": "tree"},
            {"path": "_index.json", "type": "blob"},
        ]})
        async with aiohttp.ClientSession() as s:
            icons = await src.fetch_icon_list(s)
    # Nur .svg-Blobs, beide Styles erfasst
    rels = sorted(i["rel"] for i in icons)
    assert rels == ["filled/home.svg", "outline/home.svg"]
    assert all(i["name"] == "home" for i in icons)
    # Pfad spiegelt die Unterstruktur, URL zeigt auf raw mit tree_path-Prefix
    icon = next(i for i in icons if i["rel"] == "outline/home.svg")
    assert src.target_path(Path("/o"), icon) == Path("/o/outline/home.svg")
    assert src.source_url(icon) == \
        "https://raw.githubusercontent.com/test/repo/main/icons/outline/home.svg"


async def test_github_tree_two_segments():
    # material-symbols-artig: tree_path "svg/400" muss durch zwei Ebenen gelaufen werden
    cfg = _cfg(id="material-symbols", source_type="github_tree",
               github_repo="m/ms", github_branch="main", github_tree_path="svg/400",
               styles=["outlined", "rounded", "sharp"])
    src = create_source(cfg)
    api = "https://api.github.com/repos/m/ms/git/trees"
    with aioresponses() as m:
        m.get(f"{api}/main", payload={"sha": "ROOT", "tree": [
            {"path": "svg", "type": "tree", "sha": "SVG"}]})
        m.get(f"{api}/SVG", payload={"sha": "SVG", "tree": [
            {"path": "400", "type": "tree", "sha": "W400"},
            {"path": "100", "type": "tree", "sha": "W100"}]})
        m.get(f"{api}/W400?recursive=1", payload={"sha": "W400", "truncated": False, "tree": [
            {"path": "outlined/gif-box.svg", "type": "blob"},
            {"path": "rounded/gif-box.svg", "type": "blob"},
            {"path": "sharp/gif-box.svg", "type": "blob"}]})
        async with aiohttp.ClientSession() as s:
            icons = await src.fetch_icon_list(s)
    assert len(icons) == 3
    icon = next(i for i in icons if i["rel"] == "rounded/gif-box.svg")
    # Bindestrich im Namen bleibt erhalten (kein Underscore-Mapping mehr nötig)
    assert icon["name"] == "gif-box"
    assert src.target_path(Path("/o"), icon) == Path("/o/rounded/gif-box.svg")
    assert src.source_url(icon) == \
        "https://raw.githubusercontent.com/m/ms/main/svg/400/rounded/gif-box.svg"


async def test_github_tree_missing_path_returns_empty():
    cfg = _cfg(id="x", source_type="github_tree", github_repo="test/repo",
               github_branch="main", github_tree_path="icons", styles=["default"])
    src = create_source(cfg)
    api = "https://api.github.com/repos/test/repo/git/trees"
    with aioresponses() as m:
        m.get(f"{api}/main", payload={"sha": "ROOT", "tree": [
            {"path": "src", "type": "tree", "sha": "SRC"}]})  # kein 'icons'
        async with aiohttp.ClientSession() as s:
            icons = await src.fetch_icon_list(s)
    assert icons == []
