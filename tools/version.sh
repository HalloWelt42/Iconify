#!/usr/bin/env bash
# Einzige Quelle der Version: version.json im Projektwurzelverzeichnis.
# Aufruf: tools/version.sh [patch|minor|major|id]
#   patch  -> +0.0.1   minor -> +0.1.0   major -> +1.0.0   id -> nur neue Build-Kennung
set -euo pipefail
cd "$(dirname "$0")/.."
teil="${1:-patch}"

python3 - "$teil" <<'PY'
import json, pathlib, secrets, sys

teil = sys.argv[1]
pfad = pathlib.Path("version.json")
daten = json.loads(pfad.read_text(encoding="utf-8"))
gross, mittel, klein = (int(x) for x in daten["version"].split("."))

if teil == "major":
    gross, mittel, klein = gross + 1, 0, 0
elif teil == "minor":
    mittel, klein = mittel + 1, 0
elif teil == "patch":
    klein += 1
elif teil != "id":
    raise SystemExit(f"Unbekannter Teil: {teil} (patch|minor|major|id)")

version = f"{gross}.{mittel}.{klein}"
kennung = secrets.token_hex(3)
pfad.write_text(
    json.dumps({"version": version, "id": kennung, "voll": f"v{version}-{kennung}"}, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"v{version}-{kennung}")
PY
