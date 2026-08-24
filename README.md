# artdono.github.io

My personal site — a single scrolling page at **https://artdono.github.io**.

Static HTML, CSS and a little vanilla JavaScript. No framework, no npm, no build
tooling to keep alive. The page is plain HTML by the time it reaches a browser,
so it renders with JavaScript disabled and needs no third-party request to draw
itself — the fonts are self-hosted too.

```
data/content.json      all of the site's content lives here
scripts/build.py       renders index.html from that file
index.html             generated - do not edit by hand
assets/css/style.css   the whole design
assets/js/main.js      theme toggle, mobile nav, scroll spy - nothing essential
assets/fonts/          self-hosted woff2 (Archivo, Newsreader, JetBrains Mono)
assets/images/         photos - see assets/images/README.md
```

## Changing the content

Edit `data/content.json`, then rebuild:

```bash
python3 scripts/build.py
```

Commit both the JSON and the regenerated `index.html`. CI re-runs the build and
fails if the two have drifted, so the page can never quietly go stale.

## Adding photos

Drop files into `assets/images/` using the names in
[`assets/images/README.md`](assets/images/README.md). Nothing else to change —
a photo that is not there yet renders as a neutral placeholder rather than a
broken image, so the page is never broken mid-edit.

## Running it locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Open it over HTTP rather than double-clicking `index.html`; browsers refuse to
load fonts over `file://`.

## Checks

```bash
python3 scripts/build.py --check   # index.html matches content.json
python3 scripts/check_links.py     # every link and asset resolves
```

Both run in CI on every push to `main`, and the site deploys to GitHub Pages
only after they pass.

## Regenerating the résumé PDF

`assets/docs/dono-artyk-resume.pdf` is generated from the résumé master in the
interview-prep repository — this repo never holds a second copy of that text.
The generator strips the phone number, so the public PDF carries email,
LinkedIn and this site, and nothing else.

```bash
python3 scripts/resume_pdf.py ../interview-prep-dono/resume/resume.md \
    --out build/resume.html
# then print build/resume.html to PDF at Letter size with background graphics on
```

Check it still fits on one page before committing. The layout is tuned to about
94% of a page, so a couple of extra lines are fine and a new job is not.

## Deployment

GitHub Actions builds, verifies and publishes to GitHub Pages on every push to
`main` — see [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).
Pages must be set to **Source: GitHub Actions** in the repository settings.

## Fonts

Archivo, Newsreader and JetBrains Mono, all under the SIL Open Font License 1.1.
Latin subset only, ~200KB total, committed to the repository. Re-download them
with `scripts/fetch-fonts.sh` if the typefaces ever change.
