# Iconify

Selbstgehosteter **Icon-Manager & Icon-Font-Generator**. Durchsucht und verwaltet
populäre Open-Source-Icon-Sets lokal, erzeugt daraus eigene Icon-Fonts und liefert
fertige Code-Snippets (SVG / IMG / Webfont) – ohne externe CDN-Abhängigkeit zur Laufzeit.

> Die Icons werden **nicht** mit dem Repository ausgeliefert. Jede Installation
> stößt den Import der gewünschten Sets selbst an (siehe „Nutzung"). So bleibt das
> Repo schlank und jede:r lädt nur, was gebraucht wird.

## Features

- **10 kuratierte Icon-Sets** (Tabler, Lucide, Bootstrap, Font Awesome Free, Heroicons,
  Feather, Remix, Phosphor, Material Symbols, Material Design Icons)
- **Import on-demand** direkt aus den Originalquellen (GitHub / CDN), vollständig
  (kein 1000-Icon-Limit), mit Live-Fortschritt
- **Lizenz-Transparenz**: Lizenz-Badge je Set, Filter nach Lizenz (frei nutzbar /
  Namensnennung nötig) und Attributions-Hinweis beim Export
- **Suche** mit Style-Filtern, Lazy-Loading
- **Eigene Sets** anlegen und per Drag & Drop mit eigenen SVGs befüllen
- **Icon-Font-Generator** (WOFF2/WOFF/TTF + CSS + Cheatsheet, inkl. `ATTRIBUTION.txt`)
- **Code-Snippets** pro Icon (Inline-SVG, IMG, Webfont-Klasse, CSS)
- Hell/Dunkel-Theme, deutschsprachige Oberfläche

## Schnellstart

Voraussetzung: Docker + Docker Compose.

```bash
git clone git@github.com:HalloWelt42/Iconify.git
cd Iconify
docker compose up -d --build
```

Dann im Browser öffnen: **http://localhost:8766**

## Nutzung

1. In der Seitenleiste unter **„Verfügbar"** ein Set auswählen und auf **↓** klicken –
   das Set wird heruntergeladen (Fortschritt wird angezeigt).
2. Icons durchsuchen, ein Icon anklicken → Vorschau, Größe/Farbe, Code-Snippets.
3. Über das Sammlungs-Symbol Icons sammeln und einen **eigenen Icon-Font** erzeugen.
4. Eigene Sets über **+** anlegen und SVGs per Drag & Drop hinzufügen.

## Konfiguration

Einstellungen über Umgebungsvariablen (Prefix `ICONIFY_`). Vorlage: [`.env.example`](.env.example).

| Variable | Default | Zweck |
|---|---|---|
| `ICONIFY_PORT` | `8766` | HTTP-Port |
| `ICONIFY_MAX_CONCURRENT_DOWNLOADS` | `20` | parallele Downloads beim Import |
| `ICONIFY_GITHUB_TOKEN` | – | optional: höheres GitHub-API-Rate-Limit beim Import |

## Icon-Sets & Lizenzen

Iconify selbst steht unter der **MIT-Lizenz** (siehe [`LICENSE`](LICENSE)). Die importierten
Icons unterliegen den Lizenzen ihrer jeweiligen Projekte:

| Set | Lizenz (SPDX) |
|---|---|
| Tabler Icons | MIT |
| Lucide | ISC |
| Bootstrap Icons | MIT |
| Font Awesome Free | CC-BY-4.0 (Icons) – **Namensnennung nötig** |
| Heroicons | MIT |
| Feather | MIT |
| Remix Icon | Apache-2.0 |
| Phosphor | MIT |
| Material Symbols | Apache-2.0 |
| Material Design Icons | Apache-2.0 |

Beim Font-Export wird automatisch eine `ATTRIBUTION.txt` mit den passenden Lizenz-
und Quellenhinweisen erzeugt.

## Entwicklung

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest        # Tests
bash .githooks/install.sh          # Git-Hooks aktivieren
```

- Backend: FastAPI (`app/`), Icon-Quellen als Strategie-Muster (`app/services/sources.py`)
- Frontend: Single-Page Vanilla-JS (`app/static/`), kein Build-Schritt
- Daten: SVG-Dateien unter `icons/<set>/…`, Metadaten als `meta.json`
- Branch: `dev`

## Lizenz

[MIT](LICENSE) © HalloWelt42
