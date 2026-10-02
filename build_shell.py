#!/usr/bin/env python3
"""Keep every page's shared chrome and launch phase in sync.

- Sets <html data-phase> on every EN page (root + blog/, generated chapter-1 included)
  from data/site.json — the one launch flag. build_zh.py carries it into /zh/.
- On pages that carry the markers, replaces the text between
  <!-- shell:header --> … <!-- /shell:header --> and <!-- shell:footer --> … <!-- /shell:footer -->
  with partials/header.html and partials/footer.html, and marks the current nav item
  from <body data-nav="…">. Pages without markers are left as they are (old design).

Run after build_chapter.py and before build_zh.py (see build_all.sh).
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
MARKERS = {
    "header": ("<!-- shell:header -->", "<!-- /shell:header -->"),
    "footer": ("<!-- shell:footer -->", "<!-- /shell:footer -->"),
}


def _partial(name):
    with open(os.path.join(ROOT, "partials", name + ".html"), encoding="utf-8") as f:
        return f.read().strip()


def _render(name, page, nav):
    prefix = "../" * page.count("/")
    lang_href = prefix + ("zh/" if page == "index.html" else "zh/" + page)
    if page == "404.html":
        # GitHub Pages serves the 404 page at whatever URL was missed, so its links must
        # not depend on the folder. build_zh.py maps them to /zh/ for the Chinese 404.
        prefix, lang_href = "/", "/zh/404.html"
    out = _partial(name).replace("{{R}}", prefix).replace("{{LANG_HREF}}", lang_href)
    if nav and name == "header":
        out = out.replace(f'data-nav="{nav}"', f'data-nav="{nav}" aria-current="page"', 1)
    return out


def _set_attr(html, name, value):
    m = re.search(r"<html\b[^>]*>", html)
    if not m:
        return html
    tag = re.sub(r'\s+%s="[^"]*"' % name, "", m.group(0))
    tag = tag.replace("<html", '<html %s="%s"' % (name, value), 1)
    return html[:m.start()] + tag + html[m.end():]


def _set_phase(html, phase):
    return _set_attr(html, "data-phase", phase)


def apply(html, page, phase, english=None):
    """Return html with the launch phase (and English-edition state) set and, if marked, the shell injected."""
    html = _set_phase(html, phase)
    if english is not None:
        html = _set_attr(html, "data-english", english)
    m = re.search(r'<body\b[^>]*\bdata-nav="([^"]*)"', html)
    nav = m.group(1) if m else ""
    for name, (start, end) in MARKERS.items():
        i, j = html.find(start), html.find(end)
        if i == -1 or j == -1 or j < i:
            continue
        html = html[:i + len(start)] + "\n" + _render(name, page, nav) + "\n" + html[j:]
    return html


def phase():
    with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as f:
        value = json.load(f)["phase"]
    if value not in ("prelaunch", "launched"):
        raise SystemExit(f'data/site.json phase must be "prelaunch" or "launched", got {value!r}')
    return value


ENGLISH_STATES = ("off", "preorder", "live")


def english():
    """English edition state: off (hidden), preorder (Kindle pre-order only), live (direct sale + Kindle).
    Only set "live" once the delivery script sends English buyers the English files."""
    with open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8") as f:
        value = json.load(f).get("english", "off")
    if value not in ENGLISH_STATES:
        raise SystemExit(f'data/site.json english must be one of {ENGLISH_STATES}, got {value!r}')
    return value


def main():
    ph, en = phase(), english()
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "blog", "*.html")))
    written = 0
    for path in pages:
        page = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        out = apply(src, page, ph, en)
        if out != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            written += 1
    print(f"build_shell: phase={ph}, english={en}, {written} pages updated")
    return written


if __name__ == "__main__":
    main()
