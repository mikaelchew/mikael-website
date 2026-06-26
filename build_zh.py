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
                "Mikael Chew——作家、導師、播客《The Long Game》主持人。23 年直銷資歷，從前線走到企業管理，幫助領袖以正道致勝。"),
 "404.html": ("找不到頁面 — Mikael Chew",
              "抱歉，這個頁面不存在。回到首頁繼續瀏覽 Mikael Chew 的內容。"),
 "privacy.html": ("隱私政策 — Mikael Chew",
                  "mikaelchew.com 的隱私政策——我們如何收集、使用和保護你的個人資料。"),
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
    doc = lxml.html.fromstring(html)

    # 1. html lang
    doc.set('lang', 'zh-Hant')

    # 2. swap visible text for data-en/data-zh
    for el in doc.xpath('//*[@data-zh]'):
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
    for el in (pre1, pre2, pl, ns):
        head.append(el)

    # 8. JSON-LD: point page's own url to zh + inLanguage
    e_url = en_url(relpath); z_url = zh_url(relpath)
    for s in doc.xpath('//script[@type="application/ld+json"]'):
        t = s.text or ''
        t = t.replace('"'+e_url+'"', '"'+z_url+'"')
        t = t.replace('"inLanguage":"en"', '"inLanguage":"zh-Hant"')
        s.text = t

    out_html = '<!DOCTYPE html>\n' + tostring(doc, encoding='unicode', method='html')
    out_path = os.path.join(ROOT, 'zh', relpath)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'w', encoding='utf-8').write(out_html)
    return out_path

def main():
    pages = [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT,'*.html'))]
    pages += [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT,'blog','*.html'))]
    pages = sorted(pages)
    n=0
    for p in pages:
        transform(p); n+=1
    print(f"Generated {n} zh pages")

if __name__ == '__main__':
    main()
