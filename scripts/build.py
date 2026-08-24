#!/usr/bin/env python3
"""Render index.html from data/content.json.

Everything on the site comes from data/content.json. Edit that file, run this
script, and commit both it and the regenerated index.html. CI re-runs this and
fails if the committed index.html does not match — so the two cannot drift.

Standard library only: no dependencies, no package manager, no build tooling.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "data" / "content.json"
OUTPUT = ROOT / "index.html"

ALLOWED_INLINE = ("em",)


def esc(value: str) -> str:
    """Escape text, but keep the handful of inline tags we allow in content."""
    out = html.escape(str(value), quote=True)
    for tag in ALLOWED_INLINE:
        out = out.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return out


def attr(value: str) -> str:
    return html.escape(str(value), quote=True)


# --- YAML highlighting -----------------------------------------------------
KEY_RE = re.compile(r"^(\s*-?\s*)([A-Za-z0-9_.\-/]+)(:)")
# Quotes are already HTML-escaped by the time this runs, so it can only ever
# match content — never the quotes inside the markup this function emits.
STR_RE = re.compile(r"(&quot;.*?&quot;)")


def _strings(escaped: str) -> str:
    return STR_RE.sub(lambda m: f'<span class="s">{m.group(1)}</span>', escaped)


def highlight(line: str) -> str:
    """Minimal YAML colouring: keys, quoted strings, trailing comments."""
    comment = ""
    hash_at = line.find("#")
    if hash_at != -1 and line.count('"') % 2 == 0:
        comment = line[hash_at:]
        line = line[:hash_at]

    match = KEY_RE.match(line)
    if match:
        lead, key, colon = match.groups()
        rest = line[match.end():]
        out = f'{esc(lead)}<span class="k">{esc(key)}</span>{colon}{_strings(esc(rest))}'
    else:
        out = _strings(esc(line))

    if comment:
        out += f'<span class="c">{esc(comment)}</span>'
    return out or "&nbsp;"


# --- Fragments -------------------------------------------------------------
def sep_join(items, cls="sep", char="·", nowrap=False):
    """Join with a separator that never ends a line: the break can happen in
    the space before the dot, and a non-breaking space ties the dot to the
    item that follows it. With nowrap, each item also stays whole."""
    glue = f' <span class="{cls}">{char}</span>&nbsp;'
    parts = [
        f'<span class="nb">{esc(i)}</span>' if nowrap else esc(i)
        for i in items
    ]
    return glue.join(parts)


def section_head(num: str, title: str) -> str:
    return (
        '<div class="section-head reveal">'
        f'<span class="eyebrow">{esc(num)}</span>'
        f"<h2>{esc(title)}</h2>"
        "</div>"
    )


def figure(photo: dict, extra_class: str = "", placeholder: str = "photo") -> str:
    cls = f"figure {extra_class}".strip()
    caption = photo.get("caption")
    cap = f"<figcaption>{esc(caption)}</figcaption>" if caption else ""
    return (
        f'<figure class="{cls}">'
        f'<div class="frame" data-placeholder="{attr(placeholder)}">'
        f'<img src="{attr(photo["src"])}" alt="{attr(photo["alt"])}" loading="lazy" decoding="async">'
        "</div>"
        f"{cap}"
        "</figure>"
    )


ICON_ARROW = (
    '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" '
    'aria-hidden="true"><path d="M4 10h11M11 5l5 5-5 5" stroke-linecap="round" '
    'stroke-linejoin="round"/></svg>'
)


def font_preloads() -> str:
    """Preload the two faces that draw the first screen, by whatever hashed
    filename scripts/fetch_fonts.py last wrote."""
    fonts = ROOT / "assets" / "fonts"
    links = []
    for prefix in ("inter-", "newsreader-400-normal"):
        match = sorted(fonts.glob(f"{prefix}*.woff2"))
        if match:
            href = f"assets/fonts/{match[0].name}"
            links.append(
                f'<link rel="preload" href="{href}" as="font" type="font/woff2" crossorigin>'
            )
    return "\n".join(links)


def build(data: dict) -> str:
    meta = data["meta"]
    preloads = font_preloads()
    hero = data["hero"]
    contact = data["contact"]
    about = data["about"]

    nav_links = "".join(
        f'<a href="{attr(item["href"])}">{esc(item["label"])}</a>' for item in data["nav"]
    )

    hero_meta_items = [hero["location"], *hero["availability"]]
    # Laid out as flex items with spacing rather than "·" separators, so a
    # wrap can never strand a separator at the start of a line.
    hero_meta = "".join(
        f'<span class="nb">{esc(item)}</span>' for item in hero_meta_items
    )

    hero_intro = "".join(f"<p>{esc(p)}</p>" for p in hero["intro"])

    hero_actions = "".join(
        f'<a class="btn btn-{link["kind"]}" href="{attr(link["href"])}">{esc(link["label"])}{ICON_ARROW}</a>'
        for link in hero["links"]
    )

    metrics = "".join(
        '<div class="metric">'
        f'<span class="metric-value">{esc(m["value"])}</span>'
        f'<span class="metric-label">{esc(m["label"])}</span>'
        "</div>"
        for m in hero["metrics"]
    )

    roles = "".join(
        '<article class="role reveal">'
        '<div class="role-head">'
        '<div class="role-title">'
        f'<h3 class="role-company">{esc(r["company"])}</h3>'
        '<span class="role-dash">/</span>'
        f'<span class="role-role">{esc(r["role"])}</span>'
        "</div>"
        f'<p class="role-when">{esc(r["period"])}<span class="sep">·</span>{esc(r["location"])}</p>'
        "</div>"
        '<ul class="bullets">'
        + "".join(f"<li>{esc(b)}</li>" for b in r["bullets"])
        + "</ul>"
        "</article>"
        for r in data["experience"]
    )

    projects = ""
    for project in data["projects"]:
        code = project["code"]
        code_lines = "\n".join(highlight(line) for line in code["lines"])
        projects += (
            '<article class="project reveal">'
            '<div class="project-grid">'
            '<div class="project-code">'
            f'<span class="code-file">{esc(code["title"])}</span>'
            '<div class="code">'
            f"<pre><code>{code_lines}</code></pre>"
            "</div>"
            "</div>"
            "<div>"
            f'<h3>{esc(project["name"])}</h3>'
            f'<p class="project-problem">{esc(project["problem"])}</p>'
            '<ul class="bullets">'
            + "".join(f"<li>{esc(b)}</li>" for b in project["bullets"])
            + "</ul>"
            f'<p class="tech-line">{sep_join(project["tech"])}</p>'
            "</div>"
            "</div>"
            "</article>"
        )

    stack_groups = "".join(
        '<div class="stack-group">'
        f'<h3>{esc(group["name"])}</h3>'
        "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in group["items"]) + "</ul>"
        "</div>"
        for group in data["stack"]["groups"]
    )

    certs = sep_join(data["stack"]["certifications"], nowrap=True)

    about_prose = "".join(f"<p>{esc(p)}</p>" for p in about["paragraphs"])
    portrait = figure(about["portrait"], "portrait", "photo")
    hero_photo = figure(hero["photo"], "hero-photo", "portrait")
    photos = "".join(figure(p, "", "photo") for p in about["photos"])

    year = "2026"
    canonical = meta["site_url"].rstrip("/") + "/"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta["name"])} — {esc(meta["title"])}</title>
<meta name="description" content="{attr(meta["description"])}">
<meta name="author" content="{attr(meta["name"])}">
<link rel="canonical" href="{attr(canonical)}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{attr(meta["name"])}">
<meta property="og:title" content="{attr(meta["name"])} — {attr(meta["title"])}">
<meta property="og:description" content="{attr(meta["og_description"])}">
<meta property="og:url" content="{attr(canonical)}">
<meta property="og:image" content="{attr(canonical)}assets/images/og-preview.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{attr(meta["name"])} — {attr(meta["title"])}">
<meta name="twitter:description" content="{attr(meta["og_description"])}">
<meta name="twitter:image" content="{attr(canonical)}assets/images/og-preview.png">

<link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#f5f5f2">

{preloads}
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/css/style.css">

<script>
  /* Applied before paint so a dark-theme reader never sees a light flash. */
  (function () {{
    try {{
      var saved = localStorage.getItem("theme");
      if (saved === "dark" || saved === "light") {{
        document.documentElement.setAttribute("data-theme", saved);
      }}
    }} catch (e) {{}}
  }})();
</script>
</head>

<body id="top">
<a class="skip-link" href="#main">Skip to content</a>

<header class="nav" id="nav">
  <div class="wrap nav-inner">
    <a class="nav-name" href="#top">{esc(meta["name"])}</a>
    <nav class="nav-links" id="nav-links" aria-label="Sections">{nav_links}</nav>
    <div class="nav-actions">
      <button class="icon-btn theme-toggle" id="theme-toggle" type="button" aria-label="Switch between light and dark theme">
        <svg class="icon-sun" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10" cy="10" r="3.6"/><path d="M10 1.6v2.2M10 16.2v2.2M18.4 10h-2.2M3.8 10H1.6M15.9 4.1l-1.6 1.6M5.7 14.3l-1.6 1.6M15.9 15.9l-1.6-1.6M5.7 5.7L4.1 4.1" stroke-linecap="round"/></svg>
        <svg class="icon-moon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M17.3 13.3A8 8 0 016.7 2.7a8 8 0 1010.6 10.6z"/></svg>
      </button>
      <button class="icon-btn nav-toggle" id="nav-toggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="nav-links">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M3 6h14M3 10h14M3 14h14" stroke-linecap="round"/></svg>
      </button>
    </div>
  </div>
</header>

<main id="main">

  <section class="hero wrap">
    <div class="hero-grid">
      <div class="hero-lead">
        <h1>{esc(hero["name"])}</h1>
        <p class="hero-role">{esc(hero["eyebrow"])}</p>
      </div>
      {hero_photo}
      <div class="hero-body">
        <p class="hero-meta">{hero_meta}</p>
        <div class="hero-intro">{hero_intro}</div>
        <div class="hero-actions">{hero_actions}</div>
      </div>
    </div>
    <div class="metrics">{metrics}</div>
  </section>

  <section class="section" id="experience">
    <div class="wrap">
      {section_head("01", "Experience")}
      {roles}
    </div>
  </section>

  <section class="section" id="projects">
    <div class="wrap">
      {section_head("02", "Selected work")}
      {projects}
    </div>
  </section>

  <section class="section" id="stack">
    <div class="wrap">
      {section_head("03", "Core stack")}
      <div class="stack-grid reveal">{stack_groups}</div>
      <p class="stack-ai reveal">{esc(data["stack"]["ai_line"])}</p>
      <p class="certs reveal"><span class="certs-label">Certified</span>{certs}</p>
    </div>
  </section>

  <section class="section" id="about">
    <div class="wrap">
      {section_head("04", esc(about["heading"]))}
      <div class="about-top reveal">
        <div class="about-prose">{about_prose}</div>
        {portrait}
      </div>
      <div class="photo-grid reveal">{photos}</div>
    </div>
  </section>

  <section class="section" id="contact">
    <div class="wrap">
      <div class="reveal">
        {section_head("05", esc(contact["heading"]))}
        <p class="contact-line">{esc(contact["line"])}</p>
        <div class="contact-list">
          <div class="contact-item">
            <span class="label">Email</span>
            <a href="mailto:{attr(contact["email"])}">{esc(contact["email"])}</a>
          </div>
          <div class="contact-item">
            <span class="label">LinkedIn</span>
            <a href="{attr(contact["linkedin"])}" rel="me noopener" target="_blank">{esc(contact["linkedin_label"])}</a>
          </div>
          <div class="contact-item">
            <span class="label">Résumé</span>
            <a href="{attr(contact["resume"]["href"])}" download>{esc(contact["resume"]["label"])}</a>
          </div>
        </div>
      </div>
    </div>
  </section>

</main>

<footer class="footer">
  <div class="wrap footer-inner">
    <span>{esc(meta["name"])} — {esc(meta["title"])} · {esc(hero["location"])}</span>
    <span>© {year} · Built as a static page, deployed from git</span>
  </div>
</footer>

<button class="icon-btn to-top" id="to-top" type="button" aria-label="Back to top">
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M10 16V5M5 10l5-5 5 5" stroke-linecap="round" stroke-linejoin="round"/></svg>
</button>

<script src="assets/js/main.js" defer></script>
</body>
</html>
"""


def main() -> int:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    rendered = build(data)

    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print("index.html is out of date with data/content.json.", file=sys.stderr)
            print("Run: python3 scripts/build.py", file=sys.stderr)
            return 1
        print("index.html is up to date with data/content.json.")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(rendered):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
