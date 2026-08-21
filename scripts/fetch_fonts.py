#!/usr/bin/env python3
"""Download the site's web fonts from Google Fonts and self-host them.

Self-hosting means a visitor's browser never contacts a third party to render
this page. Latin subset only; the site's content is English.
"""

import hashlib
import pathlib
import re
import urllib.request

QUERY = (
    "https://fonts.googleapis.com/css2"
    "?family=Archivo:wdth,wght@75..100,400..800"          # variable: needs the width axis
    "&family=Newsreader:ital,wght@0,400;0,500;1,400"       # static instances: much smaller
    "&family=JetBrains+Mono:wght@400;500"
    "&display=swap"
)
KEEP_SUBSETS = {"latin"}
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "fonts"

opener = urllib.request.build_opener()
opener.addheaders = [
    (
        "User-Agent",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36",
    )
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    css = opener.open(QUERY, timeout=60).read().decode()

    blocks = re.findall(r"/\*\s*([a-z0-9\-\[\]]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
    seen: dict[str, str] = {}
    pieces: list[str] = []
    total = 0

    for subset, block in blocks:
        if subset not in KEEP_SUBSETS:
            continue
        url = re.search(r"url\((https://fonts\.gstatic\.com[^)]+)\)", block).group(1)
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1).lower().replace(" ", "-")
        style = "italic" if "font-style: italic" in block else "normal"
        weight = re.search(r"font-weight:\s*([^;]+);", block).group(1).strip().replace(" ", "-")

        if url not in seen:
            name = f"{family}-{weight}-{style}-{hashlib.sha1(url.encode()).hexdigest()[:6]}.woff2"
            data = opener.open(url, timeout=60).read()
            (OUT / name).write_bytes(data)
            seen[url] = name
            total += len(data)

        pieces.append(block.replace(url, seen[url]))

    header = (
        "/* Self-hosted web fonts - no third-party request when the page loads.\n"
        "   Archivo, Newsreader and JetBrains Mono are all SIL OFL 1.1 licensed.\n"
        "   Regenerate with scripts/fetch-fonts.sh. Latin subset only. */\n\n"
    )
    (OUT / "fonts.css").write_text(header + "\n\n".join(pieces) + "\n")
    print(f"{len(seen)} font files, {total / 1024:.0f} KB")


if __name__ == "__main__":
    main()
