#!/usr/bin/env python3
"""Move blog posts from the old template onto the redesign shell (spec §6.5).

Keeps, unchanged: the <head> metadata (title, description, canonical, hreflang, JSON-LD) and
the article's content nodes with their data-en/data-zh pairs. Replaces the page chrome with
the shell markers and the .prose reading layout. Run once per post; a post already on the
new template is left alone.

Usage: /usr/bin/python3 tools/retemplate_posts.py blog/*.html
"""
import glob
import os
import re
import sys

import lxml.html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = ("breadcrumb", "share-section", "post-share", "post-cta", "post-nav", "related-posts")

DROP_HEAD = [
    r"\s*<!-- (Google Fonts|Font Awesome|Stylesheet|Site Styles|Google Analytics)[^>]*-->",
    r"\s*<link rel=\"preload\" as=\"style\"[^>]*>",
    r"\s*<noscript>.*?</noscript>",
    r"\s*<link rel=\"stylesheet\" href=\"(\.\./)?(css/style\.css|vendor/[^\"]*)\">",
    r"\s*<script async src=\"https://www\.googletagmanager\.com[^>]*></script>",
    r"\s*<script>\s*window\.dataLayer.*?</script>",
    r"\s*<meta name=\"theme-color\"[^>]*>",
]
ASSETS = """
  <link rel="preload" as="font" type="font/woff2" href="../vendor/fonts/overpass-900-latin.woff2" crossorigin>
  <link rel="stylesheet" href="../vendor/fonts/site-fonts.css">
  <link rel="stylesheet" href="../css/site.css">
  <meta name="theme-color" content="#22303A">"""
GA = """
  <!-- Google Analytics (config call lives in js/site.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ENGNTZ3PPC"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
  </script>
  <script src="../js/site.js" defer></script>
"""


def html_of(el):
    return lxml.html.tostring(el, encoding="unicode").strip()


def pubdates():
    """slug path -> datePublished, for gating next/previous links to scheduled posts."""
    out = {}
    for p in glob.glob(os.path.join(ROOT, "blog", "*.html")):
        src = open(p, encoding="utf-8").read()
        m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', src)
        if m:
            out["blog/" + os.path.basename(p)] = m.group(1)
    return out


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def pair(el, tag, cls=""):
    c = ' class="%s"' % cls if cls else ""
    a = "".join(' %s="%s"' % (k, esc(el.get(k))) for k in ("data-en", "data-zh") if el.get(k) is not None)
    return "<%s%s%s>%s</%s>" % (tag, c, a, esc(el.text_content().strip()), tag)


def retemplate(path):
    src = open(path, encoding="utf-8").read()
    if "<!-- shell:header -->" in src:
        return src
    head = src[src.index("<head>") + len("<head>"):src.index("</head>")]
    for pat in DROP_HEAD:
        head = re.sub(pat, "", head, flags=re.S)
    head = re.sub(r"(<title>.*?</title>)", lambda m: m.group(1) + ASSETS, head, count=1, flags=re.S)
    head = head.rstrip() + GA

    root = lxml.html.fromstring(src)
    hero = root.xpath('//section[contains(@class,"post-hero")]')[0]
    box = root.xpath('//section[contains(@class,"post-content")]/div[contains(@class,"container")]')[0]
    dates = pubdates()

    cat = hero.xpath('.//*[contains(@class,"post-category")]')[0]
    h1 = hero.xpath(".//h1")[0]
    # Meta items are either <span data-en>…</span> or <span><i/> <span data-en>…</span></span>.
    meta_bits = [pair(s if s.get("data-en") else s.xpath("./span")[0], "span")
                 for s in hero.xpath('.//*[contains(@class,"post-meta")]/span')
                 if s.get("data-en") or s.xpath("./span")]

    body = []
    for el in box:
        if not isinstance(el.tag, str) or any(c in (el.get("class") or "") for c in CHROME):
            continue
        cls = " ".join(c for c in (el.get("class") or "").split() if c != "fade-in")
        if cls:
            el.set("class", cls)
        elif el.get("class") is not None:
            del el.attrib["class"]
        body.append("        " + html_of(el))

    end = []
    share = box.xpath('.//div[contains(@class,"share-section") or contains(@class,"post-share")]')
    if share:
        label = share[0].xpath('.//*[contains(@class,"share-label")] | ./span[@data-en]')
        links = []
        for a in share[0].xpath(".//a"):
            name = (a.get("aria-label") or "").replace("Share on ", "") or "Share"
            links.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(a.get("href")), esc(name)))
        end.append('      <p class="share">%s %s</p>' % (pair(label[0], "span") if label else "<span>Share:</span>", " · ".join(links)))
    cta = box.xpath('.//div[contains(@class,"post-cta")]')
    if cta:
        c = cta[0]
        h3, p, a = c.xpath(".//h3")[0], c.xpath(".//p")[0], c.xpath(".//a")[0]
        end.append('      <aside class="chapter-cta">\n        %s\n        %s\n        <a class="btn" href="%s"%s>%s</a>\n      </aside>'
                   % (pair(h3, "h2"), pair(p, "p"), esc(a.get("href")),
                      "".join(' %s="%s"' % (k, esc(a.get(k))) for k in ("data-en", "data-zh") if a.get(k) is not None),
                      esc(a.text_content().strip())))
    nav = box.xpath('.//nav[contains(@class,"post-nav")]')
    if nav:
        links = []
        for a in nav[0].xpath(".//a"):
            target = os.path.normpath(os.path.join("blog", a.get("href"))).replace(os.sep, "/")
            label = a.xpath('.//*[contains(@class,"post-nav-label")]')[0]
            title = a.xpath('.//*[contains(@class,"post-nav-title")]')[0]
            kind = "prev" if "prev" in (a.get("class") or "") else "next"
            links.append('<a class="%s" href="%s" data-pubdate="%s">%s%s</a>'
                         % (kind, esc(a.get("href")), dates.get(target, ""), pair(label, "small"), pair(title, "b")))
        end.append('      <nav class="post-nav" aria-label="More posts">%s</nav>' % "".join(links))
    rel = box.xpath('.//div[contains(@class,"related-posts")]')
    if rel:
        h3 = rel[0].xpath(".//h3")[0]
        items = []
        for a in rel[0].xpath(".//a"):
            cat_el = a.xpath('.//*[contains(@class,"related-post-category")]')[0]
            title = a.xpath('.//*[contains(@class,"related-post-title")]')[0]
            items.append('<li><a href="%s">%s%s</a></li>' % (esc(a.get("href")), pair(cat_el, "small"), pair(title, "b")))
        end.append('      <div class="related">%s<ul>%s</ul></div>' % (pair(h3, "h2"), "".join(items)))

    page = """<!DOCTYPE html>
<html data-phase="prelaunch" lang="en">
<head>%s</head>
<body data-nav="writing">
<!-- shell:header -->
<!-- /shell:header -->

<main id="main" class="prose on-paper">
  <div class="measure">
    <article class="post">
      <header class="post-head">
        %s
        %s
        <p class="meta">%s</p>
      </header>
      <div class="post-body">
%s
      </div>
    </article>
%s
    <aside class="post-letter">
      <h2 data-en="Enjoyed this article?" data-zh="喜歡這篇文章嗎？">Enjoyed this article?</h2>
      <p data-en="Get weekly insights on leadership and strategy for direct selling, straight to your inbox." data-zh="每週收到直銷領導力與策略的洞見，直接寄到你的信箱。">Get weekly insights on leadership and strategy for direct selling, straight to your inbox.</p>
      <form class="field" action="https://app.kit.com/forms/9983575/subscriptions" method="post" data-ajax>
        <label class="sr" for="nl-em" data-en="Email address" data-zh="電子郵件">Email address</label>
        <input id="nl-em" type="email" name="email_address" placeholder="Your email" data-en="Your email" data-zh="你的電子郵件" autocomplete="email" required>
        <input type="hidden" name="tags" value="newsletter">
        <button type="submit" data-en="Subscribe" data-zh="訂閱">Subscribe</button>
      </form>
      <p class="form-ok" tabindex="-1" hidden data-en="Check your inbox to confirm. No spam, unsubscribe any time." data-zh="請到信箱確認訂閱。不發垃圾信，隨時可退訂。">Check your inbox to confirm. No spam, unsubscribe any time.</p>
    </aside>
  </div>
</main>

<!-- shell:footer -->
<!-- /shell:footer -->
</body>
</html>
""" % (head, pair(cat, "p", "kicker"), html_of(h1), " · ".join(meta_bits), "\n".join(body), "\n".join(end))
    return page


def main(paths):
    for p in paths:
        out = retemplate(p)
        open(p, "w", encoding="utf-8").write(out)
        print("retemplated", p)


if __name__ == "__main__":
    main(sys.argv[1:])
