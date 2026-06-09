"""
Tests für den In-Memory-Such-Index (app/services/search_index.py).
Baut den Index aus einem Temp-Icon-Baum und prüft Scope-/Lizenz-/Style-Filter.
"""
import app.services.search_index as si


def _tree(tmp_path):
    (tmp_path / "tabler" / "outline").mkdir(parents=True)
    (tmp_path / "tabler" / "outline" / "home.svg").write_text("<svg/>")
    (tmp_path / "tabler" / "filled").mkdir(parents=True)
    (tmp_path / "tabler" / "filled" / "home.svg").write_text("<svg/>")
    (tmp_path / "fontawesome" / "solid").mkdir(parents=True)
    (tmp_path / "fontawesome" / "solid" / "house.svg").write_text("<svg/>")
    custom = tmp_path / "custom-meins"
    custom.mkdir()
    (custom / "logo.svg").write_text("<svg/>")
    (tmp_path / "_custom_sets.json").write_text('{"custom-meins": {"name": "Meins", "license": "Custom"}}')


def _setup(tmp_path, monkeypatch):
    _tree(tmp_path)
    monkeypatch.setattr(si, "ICONS_PATH", tmp_path)
    monkeypatch.setattr(si, "CUSTOM_FILE", tmp_path / "_custom_sets.json")
    si._conn = None
    si.build()


def test_global_scope_finds_across_sets(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    r = si.search(query="ho", scope="all")
    names = {(i["set_id"], i["name"]) for i in r["icons"]}
    assert ("tabler", "home") in names
    assert ("fontawesome", "house") in names


def test_set_scope_with_style(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    r = si.search(scope="set", set_id="tabler", style="filled")
    assert r["total"] == 1
    assert all(i["style"] == "filled" for i in r["icons"])


def test_dedupe_by_name_without_style(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    # tabler/home gibt es als outline + filled -> ohne Style-Filter nur einmal
    r = si.search(scope="set", set_id="tabler")
    assert sum(1 for i in r["icons"] if i["name"] == "home") == 1


def test_custom_scope_and_license_without(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    assert any(i["name"] == "logo" for i in si.search(scope="custom")["icons"])
    # Custom = license_category "none" -> Filter "without" findet es
    r = si.search(scope="all", license="without")
    assert any(i["set_id"] == "custom-meins" for i in r["icons"])
    # fontawesome ist attribution
    r = si.search(scope="all", license="attribution")
    assert all(i["set_id"] == "fontawesome" for i in r["icons"])
