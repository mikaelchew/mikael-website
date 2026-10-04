#!/usr/bin/env python3
"""Render the LinkedIn recommendations in data/testimonials.json into every page that has
<!-- quotes:all --> … <!-- /quotes:all --> markers (homepage, About). Quotes are real and
word-for-word; never add, trim or invent one here, and never add star ratings.

Usage: /usr/bin/python3 build_quotes.py      (run before build_shell.py and build_zh.py)
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
START, END = "<!-- quotes:all -->", "<!-- /quotes:all -->"


def attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(quotes):
    items = []
    for q in quotes:
        items.append(
            '      <article class="c"><blockquote data-en="%s" data-zh="%s">%s</blockquote>\n'
            '        <footer><b>%s</b><span data-en="%s" data-zh="%s">%s</span></footer></article>'
            % (attr(q["en"]), attr(q["zh"]), esc(q["en"]), esc(q["name"]),
               attr(q["role_en"]), attr(q["role_zh"]), esc(q["role_en"])))
    # one row: js/site.js moves it right-to-left as the page scrolls; swipe or arrow keys to browse
    return ('    <div class="c-rail" tabindex="0" role="region" aria-label="Recommendations from LinkedIn" '
            'data-aria-zh="來自 LinkedIn 的推薦">\n    <div class="c-grid all">\n%s\n    </div>\n    </div>' % "\n".join(items))


def main():
    with open(os.path.join(ROOT, "data", "testimonials.json"), encoding="utf-8") as f:
        block = render(json.load(f))
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    n = 0
    for path in glob.glob(os.path.join(ROOT, "*.html")):
        html = open(path, encoding="utf-8").read()
        if START not in html:
            continue
        out = pat.sub(lambda m: START + "\n" + block + "\n    " + END, html)
        if out != html:
            open(path, "w", encoding="utf-8").write(out)
        n += 1
    print("build_quotes: %d pages" % n)


if __name__ == "__main__":
    main()
