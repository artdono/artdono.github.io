#!/usr/bin/env bash
# Re-download the self-hosted web fonts (latin subset only) into assets/fonts/.
# Only needed if the type choices in style.css change — the files are committed.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/fetch_fonts.py
