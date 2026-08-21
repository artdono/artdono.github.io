#!/usr/bin/env python3
"""Verify every link and asset reference in index.html resolves.

Checks that local files exist, that every in-page anchor points at a real id,
and that external links are well-formed. External URLs are not fetched: this
check must be deterministic, and sites like LinkedIn refuse automated requests.
"""

from __future__ import annotations

import json
import pathlib
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
CONTENT = ROOT / "data" / "content.json"


def pending_photos() -> set[str]:
    """Photo paths the owner has declared but may not have added yet.

    The page renders a deliberate placeholder for these, so a missing file is
    a reminder rather than a broken site. Everything else must resolve.
    """
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    about = data["about"]
    return {about["portrait"]["src"]} | {photo["src"] for photo in about["photos"]}


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data and data["id"]:
            self.ids.add(data["id"])
        for name in ("href", "src"):
            value = data.get(name)
            if value:
                self.refs.append((tag, value))


def main() -> int:
    parser = Collector()
    parser.feed(PAGE.read_text(encoding="utf-8"))

    optional = pending_photos()
    errors: list[str] = []
    pending: list[str] = []
    local = anchors = external = 0

    for tag, ref in parser.refs:
        if ref.startswith(("mailto:", "tel:", "data:")):
            continue

        if ref.startswith("#"):
            anchors += 1
            target = ref[1:]
            if target and target not in parser.ids:
                errors.append(f"<{tag}> anchor {ref} has no matching id")
            continue

        parsed = urlparse(ref)
        if parsed.scheme in ("http", "https"):
            external += 1
            if not parsed.netloc:
                errors.append(f"<{tag}> external link is malformed: {ref}")
            continue
        if parsed.scheme:
            errors.append(f"<{tag}> unexpected URL scheme: {ref}")
            continue

        local += 1
        path = (ROOT / unquote(parsed.path)).resolve()
        if not str(path).startswith(str(ROOT)):
            errors.append(f"<{tag}> path escapes the site root: {ref}")
        elif not path.exists():
            if ref in optional:
                pending.append(ref)
            else:
                errors.append(f"<{tag}> missing local file: {ref}")

    for ref in pending:
        print(f"PENDING  photo not added yet, placeholder shown: {ref}")

    for error in errors:
        print(f"FAIL  {error}", file=sys.stderr)

    print(f"checked {local} local files, {anchors} anchors, {external} external links")
    if errors:
        print(f"{len(errors)} broken reference(s)", file=sys.stderr)
        return 1
    print("all references resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
