"""Shared helpers for the site test suites. Paths are relative to the repo root."""
import glob
import os

import lxml.html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = {"chapter-1.html"}


def _rel(paths):
    return sorted(os.path.relpath(p, ROOT) for p in paths)


def en_pages():
    """Hand-written English pages: root *.html and blog/*.html (generated pages excluded)."""
    pages = glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "blog", "*.html"))
    return [p for p in _rel(pages) if os.path.basename(p) not in GENERATED]


def zh_pages():
    """Generated Traditional Chinese pages under zh/."""
    return _rel(glob.glob(os.path.join(ROOT, "zh", "*.html")) + glob.glob(os.path.join(ROOT, "zh", "blog", "*.html")))


def doc(path):
    """Parse a page (repo-relative path) and return its <html> element."""
    return lxml.html.parse(os.path.join(ROOT, path)).getroot()


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()
