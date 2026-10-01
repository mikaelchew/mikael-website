#!/usr/bin/env python3
"""Render the 13 chapters from data/chapters.json into the pages that list them.

One source of truth for chapter titles and one-liners (spec §5, §12):
  index.html  <!-- chapters:map -->  … <!-- /chapters:map -->   the map's chapter list
  book.html   <!-- chapters:book --> … <!-- /chapters:book -->  the book page's briefing cards
Copy carries data-en/data-zh so build_zh.py produces the Chinese pages.
Run first (see build_all.sh).
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGETS = {"map": "index.html", "book": "book.html"}


def load():
    with open(os.path.join(ROOT, "data", "chapters.json"), encoding="utf-8") as f:
        return json.load(f)


def _e(s):
    return html.escape(s, quote=True)


def _bi(tag, en, zh, cls="", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c}{extra} data-en="{_e(en)}" data-zh="{_e(zh)}">{_e(en)}</{tag}>'


def _part_head(i, part):
    roman = "I II III IV".split()[i]
    num = "一二三四"[i]
    en_label = "Part %s · %s" % (roman, part["en"])
    zh_label = "第%s部 · %s" % (num, part["zh"])
    zh_mark = '<span class="zh cjk-display" lang="zh-Hant" data-zh-only>%s</span>' % _e(part["zh"])
    return "<h3>" + _bi("span", en_label, zh_label) + zh_mark + "</h3>"


def render_map(data):
    """The map page's chapter list: one <ol class="chapters"> per part, waypoints in data-*."""
    out = ['<div class="parts">']
    for i, part in enumerate(data["parts"]):
        items = [c for c in data["chapters"] if c["part"] == i]
        out.append(f'<div class="part">{_part_head(i, part)}<ol class="chapters" start="{items[0]["n"]}">')
        for c in items:
            free = ""
            if c.get("free"):
                free = '<a class="free" href="chapter-1.html" data-en="Read Chapter 1 free" data-zh="免費試讀第一章">Read Chapter 1 free</a>'
            out.append(
                f'<li data-x="{c["x"]}" data-y="{c["y"]}" data-part="{c["part"]}"{" data-free" if c.get("free") else ""}>'
                f'<button class="ch" type="button" data-i="{c["n"] - 1}"><span class="n num">{c["n"]:02d}</span>'
                f'{_bi("b", c["en"], c["zh"])}'
                f'{_bi("span", c["zh"], c["en"], cls="alt cjk-display")}'
                f'{_bi("p", c["line_en"], c["line_zh"])}</button>{free}</li>')
        out.append("</ol></div>")
    out.append("</div>")
    return "\n".join(out)


def render_book(data):
    """The book page's chapter section: briefing cards grouped by part."""
    out = ['<div class="parts">']
    for i, part in enumerate(data["parts"]):
        out.append(f'<div class="part">{_part_head(i, part)}')
        for c in (c for c in data["chapters"] if c["part"] == i):
            free = ""
            if c.get("free"):
                free = ('<a class="free has-seal" href="chapter-1.html"><span data-en="Read Chapter 1 free" data-zh="免費試讀第一章">Read Chapter 1 free</span>'
                        '<svg class="seal seal-sm" viewBox="0 0 100 100" aria-hidden="true" data-stamp><use href="#seal-free"/></svg></a>')
            out.append(
                f'<article class="brief" id="ch-{c["n"]}"><span class="n num">{c["n"]:02d}</span>'
                f'{_bi("h3", c["en"], c["zh"])}'
                f'{_bi("div", c["zh"], c["en"], cls="zh alt cjk-display")}'
                f'{_bi("p", c["line_en"], c["line_zh"])}{free}</article>')
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def inject(page_html, name, block):
    start, end = f"<!-- chapters:{name} -->", f"<!-- /chapters:{name} -->"
    i, j = page_html.find(start), page_html.find(end)
    if i == -1 or j == -1 or j < i:
        return page_html
    return page_html[:i + len(start)] + "\n" + block + "\n" + page_html[j:]


def main():
    data = load()
    renderers = {"map": render_map, "book": render_book}
    for name, page in TARGETS.items():
        path = os.path.join(ROOT, page)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        out = inject(src, name, renderers[name](data))
        if out != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"build_chapters: {page} updated")


if __name__ == "__main__":
    main()
