#!/usr/bin/env python3
"""Render blog posts written as sources in content/posts/<slug>.json.

Each source holds the post's metadata and its body as bilingual blocks:
  ["h2", en, zh]  ["p", en, zh]  ["quote", en, zh, cite_en, cite_zh]  ["ul", [[en, zh], ...]]
Inline <strong>/<em> are allowed in en/zh text.

For every source this writes blog/<slug>.html (same template as the converted posts),
upserts the post into data/posts.json (which build_blog.py turns into the index), links
previous/next neighbours by date, and adds the post to sitemap.xml and, once its date has
come, to feed.xml. Posts dated in the future are hidden on the site by js/site.js.

Usage: /usr/bin/python3 build_posts.py      (run before build_blog.py)
"""
import datetime
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.mikaelchew.com"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;")


def bi(tag, en, zh, cls=""):
    """An element whose visible text is en; build_zh.py swaps in zh. Inline tags allowed."""
    c = ' class="%s"' % cls if cls else ""
    return '<%s%s data-en="%s" data-zh="%s">%s</%s>' % (tag, c, attr(en), attr(zh), en, tag)


def load_sources():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "content", "posts", "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def load_index():
    with open(os.path.join(ROOT, "data", "posts.json"), encoding="utf-8") as f:
        return json.load(f)


def body_html(blocks):
    out = []
    for b in blocks:
        kind = b[0]
        if kind in ("h2", "p"):
            out.append(bi(kind, b[1], b[2]))
        elif kind == "quote":
            out.append('<blockquote data-en="%s" data-zh="%s">%s</blockquote>'
                       % (attr(b[1] + " — " + b[3]), attr(b[2] + "　" + b[4]), b[1] + " — " + b[3]))
        elif kind == "ul":
            out.append("<ul>" + "".join(bi("li", en, zh) for en, zh in b[1]) + "</ul>")
        else:
            raise SystemExit("unknown block type %r" % kind)
    return "\n".join("        " + x for x in out)


def words(s):
    text = " ".join(x for b in s["blocks"] for x in (b[1:2] if b[0] != "ul" else [en for en, _ in b[1]]))
    return len(re.sub(r"<[^>]+>", "", text).split())


def render(s, prev, nxt):
    url = "%s/blog/%s.html" % (SITE, s["slug"])
    image = "%s/images/book-social-card.jpg" % SITE
    d = datetime.date.fromisoformat(s["date"])
    date_en = d.strftime("%B %-d, %Y")
    date_zh = "%d年%d月%d日" % (d.year, d.month, d.day)
    posting = {
        "@context": "https://schema.org", "@type": "BlogPosting", "headline": s["title_en"],
        "description": s["description_en"], "image": image, "datePublished": s["date"],
        "dateModified": s["date"], "wordCount": words(s), "inLanguage": "en",
        "articleSection": s["category_en"].title(), "keywords": s["keywords"], "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Person", "name": "Mikael Chew", "url": SITE + "/about.html"},
        "publisher": {"@type": "Organization", "name": "Mikael Chew",
                      "logo": {"@type": "ImageObject", "url": SITE + "/apple-touch-icon.png"}},
    }
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog.html"},
        {"@type": "ListItem", "position": 3, "name": s["short_en"], "item": url}]}
    nav = []
    if prev:
        nav.append('<a class="prev" href="%s.html" data-pubdate="%s">%s%s</a>'
                   % (prev["slug"], prev["date"], bi("small", "&larr; Previous", "&larr; 上一篇"), bi("b", esc(prev["title_en"]), esc(prev["title_zh"]))))
    if nxt:
        nav.append('<a class="next" href="%s.html" data-pubdate="%s">%s%s</a>'
                   % (nxt["slug"], nxt["date"], bi("small", "Next &rarr;", "下一篇 &rarr;"), bi("b", esc(nxt["title_en"]), esc(nxt["title_zh"]))))
    share_text = "%s%%20%s" % (re.sub(r"[^A-Za-z0-9]+", "%20", s["short_en"]).strip("%20"), url)
    cta = s["cta"]
    return """<!DOCTYPE html>
<html data-phase="prelaunch" lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="google-site-verification" content="embeCp3FnhQSbE8YajaqByuuUis1O6FDwtC7frU03mU" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" data-zh="{desc_zh}" content="{desc_en}">
  <meta name="keywords" content="{keywords}">
  <meta name="author" content="Mikael Chew">
  <meta property="og:title" content="{title_en_a} — Mikael Chew">
  <meta property="og:description" content="{desc_en}">
  <meta property="og:image" content="{image}">
  <meta property="og:url" content="{url}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="en_US">
  <meta property="og:locale:alternate" content="zh_TW">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_en_a} — Mikael Chew">
  <meta name="twitter:description" content="{desc_en}">
  <meta name="twitter:image" content="{image}">
  <title>{short_en} — Mikael Chew</title>
  <link rel="preload" as="font" type="font/woff2" href="../vendor/fonts/overpass-900-latin.woff2" crossorigin>
  <link rel="stylesheet" href="../vendor/fonts/site-fonts.css">
  <link rel="stylesheet" href="../css/site.css">
  <meta name="theme-color" content="#22303A">
  <link rel="icon" type="image/svg+xml" href="../favicon.svg">
  <link rel="icon" type="image/png" href="../favicon.png">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png">
  <link rel="manifest" href="../site.webmanifest">
  <link rel="alternate" type="application/rss+xml" title="Mikael Chew Blog" href="https://www.mikaelchew.com/feed.xml">
  <script type="application/ld+json">
{posting}
  </script>
  <script type="application/ld+json">
  {crumbs}
  </script>
  <link rel="canonical" href="{url}">
  <link rel="alternate" hreflang="en" href="{url}">
  <link rel="alternate" hreflang="zh-Hant" href="{zh_url}">
  <link rel="alternate" hreflang="x-default" href="{url}">
  <!-- Google Analytics (config call lives in js/site.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ENGNTZ3PPC"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
  </script>
  <script src="../js/site.js" defer></script>
</head>
<body data-nav="writing">
<!-- generated by build_posts.py from content/posts/{slug}.json — edit the source, not this file -->
<!-- shell:header -->
<!-- /shell:header -->

<main id="main" class="prose on-paper">
  <div class="measure">
    <article class="post">
      <header class="post-head">
        {cat}
        {h1}
        <p class="meta"><span data-en="Mikael Chew" data-zh="Mikael Chew">Mikael Chew</span> · <span data-en="{date_en}" data-zh="{date_zh}">{date_en}</span> · {read}</p>
      </header>
      <div class="post-body">
{body}
      </div>
    </article>
      <p class="share"><span data-en="Share this article:" data-zh="分享這篇文章：">Share this article:</span> <a href="https://www.linkedin.com/sharing/share-offsite/?url={url}" target="_blank" rel="noopener">LinkedIn</a> · <a href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener">Facebook</a> · <a href="https://api.whatsapp.com/send?text={share_text}" target="_blank" rel="noopener">WhatsApp</a></p>
      <aside class="chapter-cta">
        {cta_h}
        {cta_p}
        <a class="btn" href="{cta_href}" data-en="{cta_label_en}" data-zh="{cta_label_zh}">{cta_label_en}</a>
      </aside>
      <nav class="post-nav" aria-label="More posts">{nav}</nav>
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
""".format(
        desc_zh=attr(s["description_zh"]), desc_en=attr(s["description_en"]), keywords=attr(s["keywords"]),
        title_en_a=attr(s["title_en"]), image=image, url=url, zh_url="%s/zh/blog/%s.html" % (SITE, s["slug"]),
        short_en=esc(s["short_en"]), posting=json.dumps(posting, ensure_ascii=False),
        crumbs=json.dumps(crumbs, ensure_ascii=False), slug=s["slug"],
        cat=bi("p", esc(s["category_en"]), esc(s["category_zh"]), "kicker"),
        h1=bi("h1", esc(s["title_en"]), esc(s["title_zh"])),
        date_en=date_en, date_zh=date_zh, read=bi("span", s["read_en"] + " read", s["read_zh"] + "閱讀"),
        body=body_html(s["blocks"]), share_text=share_text,
        cta_h=bi("h2", cta["h_en"], cta["h_zh"]), cta_p=bi("p", cta["p_en"], cta["p_zh"]),
        cta_href=cta["href"], cta_label_en=attr(cta["label_en"]), cta_label_zh=attr(cta["label_zh"]),
        nav="".join(nav))


INDEX_KEYS = ("slug", "date", "category", "category_en", "category_zh", "title_en", "title_zh",
              "excerpt_en", "excerpt_zh", "read_en", "read_zh")


def upsert_index(index, sources):
    by_slug = {p["slug"]: p for p in index}
    for s in sources:
        by_slug[s["slug"]] = {k: s[k] for k in INDEX_KEYS}
    return sorted(by_slug.values(), key=lambda p: p["date"], reverse=True)


def link_previous_latest(order, sources):
    """Give the newest pre-existing post a 'Next' link to the first new post."""
    new = {s["slug"] for s in sources}
    for i, p in enumerate(order[:-1]):
        if p["slug"] not in new and order[i + 1]["slug"] in new:
            path = os.path.join(ROOT, "blog", p["slug"] + ".html")
            html = open(path, encoding="utf-8").read()
            nxt = order[i + 1]
            link = ('<a class="next" href="%s.html" data-pubdate="%s">%s%s</a>'
                    % (nxt["slug"], nxt["date"], bi("small", "Next &rarr;", "下一篇 &rarr;"),
                       bi("b", esc(nxt["title_en"]), esc(nxt["title_zh"]))))
            out = re.sub(r'<a class="next"[^>]*>.*?</a>(?=</nav>)', "", html)
            out = out.replace('</nav>\n      <div class="related">', link + '</nav>\n      <div class="related">', 1)
            if out != html:
                open(path, "w", encoding="utf-8").write(out)


def update_sitemap(sources):
    path = os.path.join(ROOT, "sitemap.xml")
    xml = open(path, encoding="utf-8").read()
    add = []
    for s in sources:
        en, zh = "%s/blog/%s.html" % (SITE, s["slug"]), "%s/zh/blog/%s.html" % (SITE, s["slug"])
        if "<loc>%s</loc>" % en in xml:
            continue
        alts = ('    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
                '    <xhtml:link rel="alternate" hreflang="zh-Hant" href="%s"/>\n'
                '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n' % (en, zh, en))
        for loc in (en, zh):
            add.append("  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n    <changefreq>yearly</changefreq>\n"
                       "    <priority>0.7</priority>\n  </url>\n" % (loc, alts, s["date"]))
    if add:
        xml = xml.replace("</urlset>", "".join(add) + "</urlset>")
        open(path, "w", encoding="utf-8").write(xml)


def update_feed(sources, today):
    path = os.path.join(ROOT, "feed.xml")
    xml = open(path, encoding="utf-8").read()
    items = []
    for s in sorted(sources, key=lambda s: s["date"]):
        url = "%s/blog/%s.html" % (SITE, s["slug"])
        if "<guid>%s</guid>" % url in xml or datetime.date.fromisoformat(s["date"]) > today:
            continue
        stamp = datetime.date.fromisoformat(s["date"]).strftime("%a, %d %b %Y 10:00:00 +0800")
        items.insert(0, "    <item>\n      <title>%s</title>\n      <link>%s</link>\n      <description>%s</description>\n"
                        "      <pubDate>%s</pubDate>\n      <guid>%s</guid>\n    </item>\n\n"
                     % (esc(s["title_en"]), url, esc(s["excerpt_en"]), stamp, url))
        xml = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "<lastBuildDate>%s</lastBuildDate>" % stamp, xml)
    if items:
        xml = xml.replace("    <item>", "".join(items) + "    <item>", 1)
        open(path, "w", encoding="utf-8").write(xml)


def main():
    sources = load_sources()
    index = upsert_index(load_index(), sources)
    with open(os.path.join(ROOT, "data", "posts.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
        f.write("\n")
    order = sorted(index, key=lambda p: p["date"])
    slugs = [p["slug"] for p in order]
    for s in sources:
        i = slugs.index(s["slug"])
        prev = order[i - 1] if i > 0 else None
        nxt = order[i + 1] if i + 1 < len(order) else None
        with open(os.path.join(ROOT, "blog", s["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(render(s, prev, nxt))
    link_previous_latest(order, sources)
    update_sitemap(sources)
    update_feed(sources, datetime.date.today())
    print("build_posts: %d sources rendered" % len(sources))


if __name__ == "__main__":
    main()
