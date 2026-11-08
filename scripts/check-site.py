#!/usr/bin/env python3
"""Check static-site links, metadata, licensed assets and source-backed counts."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ORIGIN = "https://tmux-popups.subcult.tv"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path, self.ids, self.urls, self.tags = path, set(), [], []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"Duplicate ID: {self.path}:{attrs['id']}"
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.urls.append(attrs[key])


def local_path(page, value):
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return None
    path = (SITE / unquote(parts.path).lstrip("/") if parts.path.startswith("/")
            else page.parent / unquote(parts.path)) if parts.path else page
    path = path.resolve()
    assert path.is_relative_to(SITE), f"Site link escapes root: {value}"
    if path.is_dir():
        path /= "index.html"
    return path, unquote(parts.fragment)


def main():
    pages = {path.resolve(): Page(path) for path in SITE.rglob("*.html")}
    assert len(pages) == 3, "Expected landing, docs and 404 pages"
    links = set()
    for path, page in pages.items():
        tags = page.tags
        assert any(tag == "html" and attrs.get("lang") == "en" for tag, attrs in tags)
        assert sum(tag == "h1" for tag, _ in tags) == 1, f"Missing/duplicate h1: {path}"
        assert any(tag == "meta" and attrs.get("name") == "viewport" for tag, attrs in tags)
        for value in page.urls:
            links.add(value)
            assert not value.startswith(("javascript:", "http:")), f"Unsafe URL: {value}"
            local = local_path(path, value)
            if local:
                target, fragment = local
                assert target.is_file(), f"Broken local link: {path} -> {value}"
                if fragment:
                    assert target in pages and fragment in pages[target].ids, f"Missing anchor: {value}"
        if path.name == "404.html":
            assert any(a.get("name") == "robots" and a.get("content") == "noindex" for _, a in tags)
            assert not any("support" in value for value in page.urls), "No support ask on 404"
            continue
        suffix = "/docs/" if path.parent.name == "docs" else "/"
        assert any(a.get("rel") == "canonical" and a.get("href") == ORIGIN + suffix for _, a in tags)
        for name in ("og:title", "og:description", "og:url", "og:image", "og:image:alt"):
            assert any(a.get("property") == name and a.get("content") for _, a in tags), name
        assert any(a.get("name") == "description" and a.get("content") for _, a in tags)
        assert any(a.get("name") == "twitter:card" and a.get("content") == "summary_large_image" for _, a in tags)
    css = (SITE / "style.css").read_text()
    for value in re.findall(r'url\("([^"]+)"\)', css):
        target, _ = local_path(SITE / "style.css", value)
        assert target.is_file(), value
    assert ":focus-visible" in css
    receipt = json.loads((ROOT / "docs/site-brand.json").read_text())
    selected = set()
    for item in receipt["files"]:
        target = ROOT / item["target"]
        selected.add(target.resolve())
        assert hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"], item["target"]
        if item["transform"] == "copy":
            assert item["sha256"] == item["source_sha256"], "Copy differs from Studio"
        if target.suffix == ".woff2":
            assert target.read_bytes()[:4] == b"wOF2", f"Invalid WOFF2: {target}"
    for folder in ("assets", "fonts"):
        assert {p.resolve() for p in (SITE / folder).iterdir()} <= selected, f"Unselected public {folder} asset"
    png = (SITE / "assets/og.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", png[16:24]) == (1200, 630)
    for license_name in ("sans", "condensed", "mono"):
        assert "SIL OPEN FONT LICENSE Version 1.1" in (SITE / f"fonts/{license_name}-OFL.txt").read_text()
    rows = [line.split("\t") for line in (ROOT / "popups.tsv").read_text().splitlines() if line and not line.startswith("#")]
    assert len(rows) == 25 and {row[0] for row in rows if row[9] == "on"} == {"help", "shell", "notes", "timer", "keys"}, "Refresh site coverage claims after registry changes"
    sitemap = ET.parse(SITE / "sitemap.xml")
    assert {node.text for node in sitemap.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")} == {ORIGIN + "/", ORIGIN + "/docs/"}
    assert f"Sitemap: {ORIGIN}/sitemap.xml" in (SITE / "robots.txt").read_text()
    print(f"PASS: {len(pages)} pages, {len(links)} unique links, {len(selected)} selected assets, registry claims and sitemap")


if __name__ == "__main__":
    main()
