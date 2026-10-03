#!/usr/bin/env python3
"""Generate baked, indexable Traditional-Chinese pages under /zh/ from the EN pages."""
import os, glob, re
import lxml.html
from lxml.html import tostring

ROOT = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "https://www.mikaelchew.com"

# Curated zh title/description for pages without a clean H1 source
OVERRIDES = {
 "index.html": ("Mikael Chew — 作家 · 導師 · The Long Game 主持人",
                "Mikael Chew：作家、導師、播客《The Long Game》主持人。23 年直銷資歷，從前線走到企業管理，幫助領袖以正道致勝。"),
 "404.html": ("找不到頁面 — Mikael Chew",
              "抱歉，這個頁面不存在。回到首頁繼續瀏覽 Mikael Chew 的內容。"),
 "refund-policy.html": ("退款政策 — Mikael Chew",
                  "在 mikaelchew.com 購買電子書《直銷孫子兵法之不戰而勝》的退款政策。"),
 "privacy.html": ("隱私政策 — Mikael Chew",
                  "mikaelchew.com 的隱私政策：我們如何收集、使用和保護你的個人資料。"),
}

def en_url(relpath):
    if relpath == "index.html": return DOMAIN + "/"
    return DOMAIN + "/" + relpath

def zh_url(relpath):
    if relpath == "index.html": return DOMAIN + "/zh/"
    return DOMAIN + "/zh/" + relpath

def is_relative(u):
    if not u: return False
    return not re.match(r'^(https?:)?//|^#|^mailto:|^tel:|^data:|^/', u)

def page_link(u):
    base = u.split('#')[0]
    return is_relative(u) and base.endswith('.html')

def asset_link(u):
    if not is_relative(u): return False
    if u.startswith('#'): return False
    if page_link(u): return False
    return True

def bump(u):
    """prepend ../ to a relative asset url"""
    return '../' + u

def rewrite_srcset(val):
    out=[]
    for part in val.split(','):
        part=part.strip()
        if not part: continue
        bits=part.split()
        url=bits[0]
        if asset_link(url):
            bits[0]=bump(url)
        out.append(' '.join(bits))
    return ', '.join(out)

def transform(relpath):
    src = os.path.join(ROOT, relpath)
    html = open(src, encoding='utf-8').read()
    out_html = transform_html(html, relpath)
    out_path = os.path.join(ROOT, 'zh', relpath)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'w', encoding='utf-8').write(out_html)
    return out_path

def transform_html(html, relpath):
    """Return the zh-Hant page for one EN page's HTML (relpath is its repo-relative path)."""
    doc = lxml.html.fromstring(html)
    # Pages rebuilt for the 2026-10 redesign load css/site.css: they ship a self-hosted
    # Chinese display subset and use system CJK fonts for body text.
    redesigned = bool(doc.xpath('//link[@rel="stylesheet"][contains(@href,"site.css")]'))

    # 1. html lang
    doc.set('lang', 'zh-Hant')

    # 1b. Chapter 1: the EN page carries the English edition; the Chinese original comes from
    # the fragment build_chapter.py writes (before step 2, so its CTA text is swapped too)
    if relpath == 'chapter-1.html':
        with open(os.path.join(ROOT, 'content', 'chapter-1.zh.html'), encoding='utf-8') as f:
            body = lxml.html.fragment_fromstring(f.read(), create_parent='article')
        article = doc.xpath('//article[contains(@class,"chapter-body")]')[0]
        body.attrib.update(article.attrib)
        body.set('lang', 'zh-Hant')
        article.getparent().replace(article, body)
        h1 = doc.xpath('//h1')[0]
        h1.set('class', 'cjk-display'); h1.set('lang', 'zh-Hant')
    for el in doc.xpath('//*[@data-href-zh]'):
        el.set('href', el.get('data-href-zh'))

    # 2. swap visible text for data-en/data-zh (elements inside data-zh-only stay as authored)
    for el in doc.xpath('//*[@data-zh][not(ancestor-or-self::*[@data-zh-only])]'):
        val = el.get('data-zh')
        if val is None: continue
        tag = el.tag.lower() if isinstance(el.tag, str) else ''
        if tag in ('input', 'textarea'):
            el.set('placeholder', val)
        elif tag == 'option':
            el.text = val
            for c in list(el): el.remove(c)
        else:
            for c in list(el): el.remove(c)
            if '<' in val:
                frag = lxml.html.fragment_fromstring(val, create_parent='span')
                el.text = frag.text
                for c in list(frag): el.append(c)
            else:
                el.text = val

    # 3. img alt
    for el in doc.xpath('//*[@data-alt-zh]'):
        el.set('alt', el.get('data-alt-zh') or '')

    # 4. title + description
    if relpath in OVERRIDES:
        zh_title, zh_desc = OVERRIDES[relpath]
    else:
        h1 = doc.xpath('//h1[@data-zh]')
        zh_title = (h1[0].get('data-zh') + " — Mikael Chew") if h1 else None
        # description: first <p data-zh>
        ps = doc.xpath('//p[@data-zh]')
        zh_desc = ps[0].get('data-zh') if ps else (h1[0].get('data-zh') if h1 else None)
        if zh_desc and len(zh_desc) > 160:
            zh_desc = zh_desc[:157].rstrip() + "…"
    # An explicit data-zh on the description meta always wins. Without this the
    # fallback grabs the first <p data-zh> on the page, which on book.html is the
    # launch badge — a 10-character meta description.
    explicit = doc.xpath('//meta[@name="description"][@data-zh]')
    if explicit and explicit[0].get('data-zh'):
        zh_desc = explicit[0].get('data-zh')
    title_el = doc.xpath('//title')
    if title_el and zh_title:
        title_el[0].text = zh_title

    def set_meta(sel, val):
        for m in doc.xpath(sel):
            m.set('content', val)
    if zh_desc:
        set_meta('//meta[@name="description"]', zh_desc)
        set_meta('//meta[@property="og:description"]', zh_desc)
        set_meta('//meta[@name="twitter:description"]', zh_desc)
    if zh_title:
        set_meta('//meta[@property="og:title"]', zh_title)
        set_meta('//meta[@name="twitter:title"]', zh_title)

    # 4b. share image: a page can name its zh card in data-zh (chapter-1 has an English card)
    for m in doc.xpath('//meta[@property="og:image" or @name="twitter:image"][@data-zh]'):
        m.set('content', m.get('data-zh'))

    # 5. og:locale swap
    set_meta('//meta[@property="og:locale"]', 'zh_TW')
    set_meta('//meta[@property="og:locale:alternate"]', 'en_US')
    set_meta('//meta[@property="og:url"]', zh_url(relpath))

    # 6. asset path rewrite (+1 ../) for relative non-html refs
    for el in doc.xpath('//*[@href]'):
        u = el.get('href')
        if asset_link(u): el.set('href', bump(u))
    for el in doc.xpath('//*[@src]'):
        u = el.get('src')
        if asset_link(u): el.set('src', bump(u))
    for el in doc.xpath('//*[@srcset]'):
        el.set('srcset', rewrite_srcset(el.get('srcset')))
    for el in doc.xpath('//*[@imagesrcset]'):
        el.set('imagesrcset', rewrite_srcset(el.get('imagesrcset')))

    # 6b. language link points back to the EN page (set after the asset rewrite above,
    # which would otherwise bump "zh/" on the homepage)
    back = '../' * (relpath.count('/') + 1) + ('' if relpath == 'index.html' else relpath)
    for a in doc.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," lang-link ")]'):
        a.set('href', back)
        a.set('lang', 'en'); a.set('hreflang', 'en')
        for c in list(a): a.remove(c)
        a.text = 'English'

    # 6c. the 404 page uses root-absolute links (it is served at any missed URL):
    # point its page links at the /zh/ mirror and its language link at /404.html
    if relpath == '404.html':
        for a in doc.xpath('//a[@href]'):
            u = a.get('href')
            if u.startswith('/') and not u.startswith('/zh/') and u.endswith('.html'):
                a.set('href', '/zh' + u)
        for a in doc.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," lang-link ")]'):
            a.set('href', '/404.html')

    # 7. canonical -> zh + hreflang alternates
    for c in doc.xpath('//link[@rel="canonical"]'):
        c.set('href', zh_url(relpath))
    head = doc.xpath('//head')[0]
    # remove any pre-existing hreflang we might add twice
    for a in doc.xpath('//link[@hreflang]'):
        a.getparent().remove(a)
    for hl, href in [('en', en_url(relpath)), ('zh-Hant', zh_url(relpath)), ('x-default', en_url(relpath))]:
        link = lxml.html.Element('link'); link.set('rel','alternate'); link.set('hreflang', hl); link.set('href', href)
        head.append(link)

    # 7b. inject Traditional-Chinese webfonts — only zh pages render Chinese, so
    # Noto TC is loaded here (async, from Google) rather than on the EN pages.
    GF_TC = ("https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700"
             "&family=Noto+Serif+TC:wght@400;700;900&display=swap")
    pre1 = lxml.html.Element('link'); pre1.set('rel','preconnect'); pre1.set('href','https://fonts.googleapis.com')
    pre2 = lxml.html.Element('link'); pre2.set('rel','preconnect'); pre2.set('href','https://fonts.gstatic.com'); pre2.set('crossorigin','')
    pl = lxml.html.Element('link'); pl.set('rel','preload'); pl.set('as','style'); pl.set('href', GF_TC); pl.set('onload',"this.onload=null;this.rel='stylesheet'")
    ns = lxml.html.fragment_fromstring('<noscript><link rel="stylesheet" href="%s"></noscript>' % GF_TC)
    if not redesigned:
        for el in (pre1, pre2, pl, ns):
            head.append(el)

    # 8. JSON-LD: point page's own url to zh + inLanguage
    e_url = en_url(relpath); z_url = zh_url(relpath)
    for s in doc.xpath('//script[@type="application/ld+json"]'):
        t = s.text or ''
        t = t.replace('"'+e_url+'"', '"'+z_url+'"')
        # only the page's own language: an English edition listed inside (workExample) stays "en"
        t = re.sub(r'^(\s*\{"@context":"https://schema\.org","@type":"[^"]+",[^{]*?)"inLanguage":"en"',
                   r'\1"inLanguage":"zh-Hant"', t)
        s.text = t

    return '<!DOCTYPE html>\n' + tostring(doc, encoding='unicode', method='html')

def main():
    # scorecard.html has no data-zh translations yet — skip it so we don't
    # publish an English page labeled zh-Hant. Remove from SKIP once translated.
    SKIP = {'scorecard.html'}
    pages = [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT,'*.html'))
             if os.path.basename(p) not in SKIP]
    pages += [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT,'blog','*.html'))]
    pages = sorted(pages)
    n=0
    for p in pages:
        transform(p); n+=1
    print(f"Generated {n} zh pages")

if __name__ == '__main__':
    main()
