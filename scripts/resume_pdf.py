#!/usr/bin/env python3
"""Render resume.md to a print-ready HTML page for the public site.

The master lives in the interview-prep repository; this script never edits it.
It reads the markdown, drops the phone number, and emits an HTML file styled to
match the site's typography, which Chromium then prints to PDF.

    python3 scripts/resume_pdf.py ../interview-prep-dono/resume/resume.md \
        --out build/resume.html
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

# The public copy carries email, LinkedIn and the site — never the phone.
PHONE_RE = re.compile(r"\s*·\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str) -> str:
    """Escape, then restore the only inline markup the resume uses."""
    out = html.escape(text, quote=False)
    return BOLD_RE.sub(r"<strong>\1</strong>", out)


def parse(md: str) -> list[dict]:
    """Turn the resume's fixed shape into an ordered list of blocks."""
    blocks: list[dict] = []
    bullets: list[str] = []

    def flush() -> None:
        nonlocal bullets
        if bullets:
            blocks.append({"kind": "bullets", "items": bullets})
            bullets = []

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("- "):
            bullets.append(line[2:].strip())
            continue
        flush()
        if line.startswith("### "):
            blocks.append({"kind": "company", "text": line[4:].strip()})
        elif line.startswith("## "):
            blocks.append({"kind": "section", "text": line[3:].strip()})
        elif line.startswith("# "):
            blocks.append({"kind": "name", "text": line[2:].strip()})
        else:
            blocks.append({"kind": "line", "text": line.strip()})
    flush()
    return blocks


def render(blocks: list[dict], fonts_href: str) -> str:
    body: list[str] = []
    header_lines = 0

    for block in blocks:
        kind = block["kind"]
        if kind == "name":
            body.append(f"<h1>{inline(block['text'])}</h1>")
        elif kind == "section":
            body.append(f"<h2>{inline(block['text'])}</h2>")
        elif kind == "company":
            text = block["text"]
            # "Uptake — Industrial AI … | Chicago, IL"
            name, _, location = text.partition("|")
            loc = f'<span class="loc">{inline(location.strip())}</span>' if location else ""
            body.append(f'<h3><span>{inline(name.strip())}</span>{loc}</h3>')
        elif kind == "bullets":
            items = "".join(f"<li>{inline(i)}</li>" for i in block["items"])
            body.append(f"<ul>{items}</ul>")
        else:
            text = block["text"]
            if header_lines < 2:
                cls = "tagline" if header_lines == 0 else "contact"
                body.append(f'<p class="{cls}">{inline(text)}</p>')
                header_lines += 1
            elif text.startswith("**") and "·" in text and re.search(r"\d{4}", text):
                role, _, when = text.partition("·")
                body.append(
                    f'<p class="role">{inline(role.strip())}'
                    f'<span class="when">{inline(when.strip())}</span></p>'
                )
            else:
                body.append(f"<p>{inline(text)}</p>")

    return TEMPLATE.replace("{{FONTS}}", fonts_href).replace("{{BODY}}", "\n".join(body))


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Dono Artyk — DevOps Engineer</title>
<link rel="stylesheet" href="{{FONTS}}">
<style>
  @page { size: Letter; margin: 0.45in 0.5in; }

  :root {
    --text:  #14181a;
    --soft:  #39413f;
    --muted: #6a726f;
    --green: #1f5138;
    --rule:  #d7d9d1;
  }

  * { margin: 0; box-sizing: border-box; }

  body {
    font-family: "Inter", -apple-system, Helvetica, Arial, sans-serif;
    font-size: 8.7pt;
    line-height: 1.33;
    color: var(--soft);
    -webkit-font-smoothing: antialiased;
  }

  h1 {
    font-family: "Newsreader", Georgia, serif;
    font-weight: 400;
    font-size: 22pt;
    line-height: 1;
    letter-spacing: -0.02em;
    color: var(--text);
    margin-bottom: 3pt;
  }

  .tagline { font-size: 9pt; color: var(--green); margin-bottom: 2pt; }
  .tagline strong { font-weight: 600; }

  .contact {
    font-family: "JetBrains Mono", monospace;
    font-size: 7.5pt;
    letter-spacing: 0.02em;
    color: var(--muted);
    padding-bottom: 5.5pt;
    border-bottom: 0.6pt solid var(--rule);
  }

  h2 {
    font-family: "JetBrains Mono", monospace;
    font-size: 7.3pt;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 8pt 0 3.8pt;
  }

  h3 {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10pt;
    font-family: "Newsreader", Georgia, serif;
    font-weight: 500;
    font-size: 10.6pt;
    letter-spacing: -0.01em;
    color: var(--text);
    margin-top: 6.2pt;
  }
  h3 .loc {
    font-family: "JetBrains Mono", monospace;
    font-size: 7.2pt;
    font-weight: 400;
    letter-spacing: 0.04em;
    color: var(--muted);
    white-space: nowrap;
  }

  .role {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10pt;
    margin: 3.5pt 0 2.4pt;
    color: var(--text);
  }
  .role strong { font-weight: 600; }
  .role .when {
    font-family: "JetBrains Mono", monospace;
    font-size: 7.2pt;
    letter-spacing: 0.04em;
    color: var(--muted);
    white-space: nowrap;
  }

  ul { list-style: none; padding: 0; }
  li {
    position: relative;
    padding-left: 10pt;
    margin-bottom: 2.05pt;
  }
  li::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.62em;
    width: 4.5pt;
    height: 0.6pt;
    background: var(--green);
  }

  p strong { color: var(--text); font-weight: 600; }
  h2 + p, p + p { margin-bottom: 2.2pt; }

  /* Never split a job across the page break. */
  h3, .role { break-after: avoid; }
  ul { break-inside: avoid; }
</style>
</head>
<body>
{{BODY}}
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=pathlib.Path, help="path to resume.md")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--fonts", default="../assets/fonts/fonts.css")
    args = ap.parse_args()

    md = args.source.read_text(encoding="utf-8")
    stripped, count = PHONE_RE.subn("", md)
    if count:
        print(f"removed {count} phone number(s) from the public copy")
    else:
        print("no phone number found — check the contact line", file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(parse(stripped), args.fonts), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
