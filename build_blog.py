#!/usr/bin/env python3
"""Render the Writing index (blog.html) from data/posts.json.

Each post is one entry in data/posts.json (newest first is not required; the list is sorted
by date here). Posts dated in the future are written into the index too; js/site.js hides
them until their date, so a scheduled post appears on its day without a rebuild.

Usage: /usr/bin/python3 build_blog.py      (run before build_shell.py and build_zh.py)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
START, END = "<!-- blog:index -->", "<!-- /blog:index -->"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def bi(tag, en, zh, cls="", extra=""):
    c = ' class="%s"' % cls if cls else ""
    return '<%s%s%s data-en="%s" data-zh="%s">%s</%s>' % (tag, c, extra, esc(en), esc(zh), esc(en), tag)


def load():
    with open(os.path.join(ROOT, "data", "posts.json"), encoding="utf-8") as f:
        posts = json.load(f)
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def render(posts):
    rows = []
    for p in posts:
        y, m, d = p["date"].split("-")
        href = "blog/%s.html" % p["slug"]
        rows.append(
            '  <li class="dispatch" data-category="%s" data-pubdate="%s">\n'
            '    <time class="d num" datetime="%s">%s.%s.%s</time>\n'
            '    <div>\n'
            '      %s\n'
            '      <h2><a href="%s" data-en="%s" data-zh="%s">%s</a></h2>\n'
            '      %s\n'
            '      %s\n'
            '    </div>\n'
            '  </li>'
            % (p["category"], p["date"], p["date"], d, m, y,
               bi("small", p["category_en"], p["category_zh"], "cat"),
               href, esc(p["title_en"]), esc(p["title_zh"]), esc(p["title_en"]),
               bi("p", p["excerpt_en"], p["excerpt_zh"]),
               bi("span", p["read_en"], p["read_zh"], "rt")))
    return '<ol class="dispatches">\n%s\n</ol>' % "\n".join(rows)


def inject(html, block):
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pat.search(html):
        raise SystemExit("blog.html has no %s marker" % START)
    return pat.sub(lambda m: START + "\n" + block + "\n" + END, html)


def main():
    path = os.path.join(ROOT, "blog.html")
    html = open(path, encoding="utf-8").read()
    out = inject(html, render(load()))
    if out != html:
        open(path, "w", encoding="utf-8").write(out)
    print("build_blog: %d posts in the index" % len(load()))


if __name__ == "__main__":
    main()
