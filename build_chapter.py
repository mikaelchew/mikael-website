#!/usr/bin/env python3
"""Generate chapter-1.html (the free-to-read sample) from the canonical manuscript.

The chapter is NOT hand-maintained: run this after any manuscript change so the
free sample can never drift from the book. (The old downloads/chapter1-sample.pdf
drifted for two months and shipped text that had been corrected for compliance.)

Usage:  /usr/bin/python3 build_chapter.py [path/to/Manuscript.docx]
Then:   /usr/bin/python3 build_zh.py      # regenerates /zh/chapter-1.html
"""
import sys
import urllib.parse, os, re, zipfile, html
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCX = os.path.normpath(os.path.join(
    ROOT, '..', '..', 'writing', 'Claude_Book_Editing', 'Manuscript_v2.0_FINAL.docx'))

# --- where the mid-chapter soft CTA goes (before this heading) ---
MID_CTA_BEFORE = '用Ikigai找到你獨特的切入點'
# --- WhatsApp: Mikael's number, international format, no + and no spaces ---
WHATSAPP = '60195513038'
WA_TEXT = '我剛讀完《直銷孫子兵法之不戰而勝》第一章'


def load_chapter(docx):
    z = zipfile.ZipFile(docx)
    root = ET.fromstring(z.read('word/document.xml'))
    numbering = z.read('word/numbering.xml').decode()
    absn = {m.group(1): (re.search(r'w:numFmt w:val="([^"]+)"', m.group(0)).group(1)
                         if re.search(r'w:numFmt w:val="([^"]+)"', m.group(0)) else 'bullet')
            for m in re.finditer(r'<w:abstractNum w:abstractNumId="(\d+)".*?</w:abstractNum>', numbering, re.S)}
    nums = {m.group(1): m.group(2) for m in
            re.finditer(r'<w:num w:numId="(\d+)">.*?<w:abstractNumId w:val="(\d+)"/>', numbering, re.S)}

    ps = list(root.iter(W + 'p'))
    def txt(p): return ''.join(t.text or '' for t in p.iter(W + 't'))
    def style(p):
        e = p.find(f'{W}pPr/{W}pStyle')
        return e.get(f'{W}val') if e is not None else 'Normal'
    def numid(p):
        e = p.find(f'{W}pPr/{W}numPr/{W}numId')
        return e.get(f'{W}val') if e is not None else None

    starts = [i for i, p in enumerate(ps) if txt(p).startswith('第一章：') and style(p) == 'Heading2']
    end = next(i for i, p in enumerate(ps) if txt(p).startswith('第二章：') and style(p) == 'Heading2')
    out = []
    for p in ps[starts[0]:end]:
        t = txt(p)
        if not t.strip():
            continue
        runs = []
        for r in p.iter(W + 'r'):
            rt = ''.join(x.text or '' for x in r.iter(W + 't'))
            if not rt:
                continue
            bold = r.find(f'{W}rPr/{W}b') is not None
            runs.append((rt, bold))
        nid = numid(p)
        kind = 'ol' if (nid and absn.get(nums.get(nid)) == 'decimal') else ('ul' if nid else None)
        out.append({'style': style(p), 'text': t, 'runs': runs, 'list': kind})
    return out


def inline(runs):
    parts = []
    for t, bold in runs:
        e = html.escape(t)
        parts.append(f'<b>{e}</b>' if bold else e)
    return ''.join(parts)


# Chapter 1's figures, in caption order (FigureCaption paragraphs); sources live in the
# book project's figures/ folder beside the manuscript and are converted to WebP here.
FIGURES = ['ch1_ikigai.png', 'ch1_dao_triangle.png']


def render(blocks, figures=FIGURES):
    """Manuscript blocks -> chapter HTML. Box styles from the final manuscript become
    semantic elements: BoxQuote(+Source) epigraph, BoxBrief, FigureCaption figure,
    BoxTipTitle/BoxTip aside.tip, BoxSummaryTitle/BoxSummary aside.summary."""
    out, open_list, box, mid_done, fig_i = [], None, None, False, 0

    def close_list():
        nonlocal open_list
        if open_list:
            out.append(f'</{open_list}>'); open_list = None

    def close_box():
        nonlocal box
        close_list()
        if box == 'quote':
            out.append('</blockquote>')
        elif box:
            out.append('</aside>')
        box = None

    for b in blocks:
        st = b['style']
        if st == 'Heading2':
            continue  # page supplies its own <h1>
        if st == 'Heading3' and not mid_done and MID_CTA_BEFORE in b['text']:
            close_box()
            out.append(MID_CTA_HTML); mid_done = True
        if st == 'BoxQuote':
            close_box(); out.append(f'<blockquote class="epigraph"><p>{inline(b["runs"])}</p>'); box = 'quote'; continue
        if st == 'BoxQuoteSource':
            out.append(f'<cite>{inline(b["runs"])}</cite>')
            if box == 'quote':
                out.append('</blockquote>'); box = None
            continue
        if st == 'BoxTipTitle':
            close_box(); out.append(f'<aside class="tip"><h3>{inline(b["runs"])}</h3><ul>'); box = 'tip'; open_list = 'ul'; continue
        if st == 'BoxTip':
            text = inline(b['runs']).lstrip('・').strip()
            out.append(f'  <li>{text}</li>'); continue
        if st == 'BoxSummaryTitle':
            close_box(); out.append(f'<aside class="summary"><h2>{inline(b["runs"])}</h2>'); box = 'summary'; continue
        if st == 'BoxSummary' and box != 'summary':
            close_box(); out.append('<aside class="summary">'); box = 'summary'
        if box in ('tip', 'quote') and st not in ('BoxTip', 'BoxQuoteSource'):
            close_box()
        if st == 'FigureCaption':
            close_list()
            name = figures[fig_i] if fig_i < len(figures) else None
            fig_i += 1
            cap = inline(b['runs'])
            if name:
                src = 'images/chapter-1/' + os.path.splitext(name)[0].replace('_', '-') + '.webp'
                out.append(f'<figure><img src="{src}" alt="{html.escape(b["text"])}" loading="lazy" width="1200"><figcaption>{cap}</figcaption></figure>')
            else:
                print(f'  ! no figure file for caption: {b["text"]}', file=sys.stderr)
            continue
        if st == 'BoxBrief':
            close_list(); out.append(f'<p class="brief-box">{inline(b["runs"])}</p>'); continue
        if b['list']:
            if open_list != b['list']:
                close_list()
                out.append(f'<{b["list"]}>'); open_list = b['list']
            out.append(f'  <li>{inline(b["runs"])}</li>')
            continue
        close_list()
        if st == 'Heading3':
            close_box()
            out.append(f'<h2>{inline(b["runs"])}</h2>')
        else:
            out.append(f'<p>{inline(b["runs"])}</p>')
    close_box()
    if not mid_done:
        print('  ! mid-chapter CTA anchor not found — CTA omitted', file=sys.stderr)
    if fig_i != len(figures):
        print(f'  ! {fig_i} figure captions for {len(figures)} figure files', file=sys.stderr)
    return '\n'.join(out)


def convert_figures(docx, figures=FIGURES):
    """Write images/chapter-1/<name>.webp (1200px wide) from the book project's figures/."""
    from PIL import Image
    src_dir = os.path.join(os.path.dirname(os.path.abspath(docx)), 'figures')
    out_dir = os.path.join(ROOT, 'images', 'chapter-1')
    os.makedirs(out_dir, exist_ok=True)
    for name in figures:
        im = Image.open(os.path.join(src_dir, name)).convert('RGB')
        im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        im.save(os.path.join(out_dir, os.path.splitext(name)[0].replace('_', '-') + '.webp'), 'WEBP', quality=82, method=6)


MID_CTA_HTML = '''<aside class="chapter-cta chapter-cta-soft" lang="en">
  <p data-en="Still with me? The other twelve chapters go further: prospecting, invitation, the golden 72 hours, leading without being needed." data-zh="還在看？後面十二章走得更遠：拓客、邀約、黃金72小時，以及怎麼帶團隊帶到不需要你。">Still with me? The other twelve chapters go further: prospecting, invitation, the golden 72 hours, leading without being needed.</p>
  <a href="book.html" class="btn btn--ghost when-prelaunch" data-en="See the full book (on sale 20 October)" data-zh="看完整本書（10月20日上市）">See the full book (on sale 20 October)</a>
  <a href="book.html#buy" class="btn when-launched" data-en="Get the book: RM 29.90" data-zh="購買電子書：RM 29.90">Get the book: RM 29.90</a>
</aside>'''


TITLE = '第一章：發起召集 - 尋找你的「道」'
DESC_EN = ("Read Chapter 1 of The Art of War for Direct Selling free: 38 rejections, "
           "a first commission cheque of RM 128, and the idea that changed everything.")
DESC_ZH = "免費閱讀《直銷孫子兵法之不戰而勝》第一章：38次拒絕、只有 RM 128 的第一張佣金支票，以及那晚我找到的「道」。"


def build_page(chapter_html):
    wa = 'https://wa.me/%s?text=%s' % (WHATSAPP, urllib.parse.quote(WA_TEXT))
    return f'''<!DOCTYPE html>
<html data-phase="prelaunch" lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="google-site-verification" content="embeCp3FnhQSbE8YajaqByuuUis1O6FDwtC7frU03mU" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" data-zh="{DESC_ZH}" content="{DESC_EN}">
  <meta name="keywords" content="直銷, 孫子兵法, 直銷書, 組織行銷, 領導力, Mikael Chew, 周俊德">
  <meta name="author" content="Mikael Chew">
  <meta property="og:title" content="Read Chapter 1 Free — 直銷孫子兵法之不戰而勝">
  <meta property="og:description" content="{DESC_EN}">
  <meta property="og:image" content="https://www.mikaelchew.com/images/book-social-card.jpg">
  <meta property="og:url" content="https://www.mikaelchew.com/chapter-1.html">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Mikael Chew">
  <meta property="og:locale" content="en_US">
  <meta property="og:locale:alternate" content="zh_TW">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Read Chapter 1 Free — 直銷孫子兵法之不戰而勝">
  <meta name="twitter:description" content="{DESC_EN}">
  <meta name="twitter:image" content="https://www.mikaelchew.com/images/book-social-card.jpg">
  <title>Read Chapter 1 Free — 直銷孫子兵法之不戰而勝</title>
  <link rel="preload" as="font" type="font/woff2" href="vendor/fonts/overpass-900-latin.woff2" crossorigin>
  <link rel="stylesheet" href="vendor/fonts/site-fonts.css">
  <link rel="stylesheet" href="css/site.css">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="icon" type="image/png" href="favicon.png">
  <meta name="theme-color" content="#22303A">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="manifest" href="site.webmanifest">
  <link rel="canonical" href="https://www.mikaelchew.com/chapter-1.html">
  <link rel="alternate" hreflang="en" href="https://www.mikaelchew.com/chapter-1.html">
  <link rel="alternate" hreflang="zh-Hant" href="https://www.mikaelchew.com/zh/chapter-1.html">
  <link rel="alternate" hreflang="x-default" href="https://www.mikaelchew.com/chapter-1.html">
  <!-- Google Analytics (config call lives in js/site.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ENGNTZ3PPC"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
  </script>
  <script src="js/site.js" defer></script>
</head>
<body data-nav="book">
<!-- generated by build_chapter.py from the manuscript — do not edit by hand -->
<!-- shell:header -->
<!-- /shell:header -->

<main id="main" class="prose on-paper">
  <div class="measure">
    <h1 class="cjk-display" lang="zh-Hant">{TITLE}</h1>
    <p class="standfirst" data-en="The whole first chapter, free, no sign-up. It is the night I nearly quit, after 38 rejections and a first commission cheque of RM 128, and what I worked out instead." data-zh="整個第一章，免費，不用留資料。那是我差點放棄的晚上。38次拒絕，第一張佣金支票只有 RM 128，還有我後來想通的事。">The whole first chapter, free, no sign-up. It is the night I nearly quit, after 38 rejections and a first commission cheque of RM 128, and what I worked out instead.</p>
    <p class="meta" data-en="The book is written in Traditional Chinese. This chapter is presented exactly as written." data-zh="本書以繁體中文寫成，本章依原文呈現。">The book is written in Traditional Chinese. This chapter is presented exactly as written.</p>

    <article class="chapter-body" lang="zh-Hant">
{chapter_html}
    </article>

    <aside class="chapter-cta chapter-cta-end" lang="en">
      <h2 data-en="That was one chapter. There are twelve more." data-zh="這是第一章。後面還有十二章。">That was one chapter. There are twelve more.</h2>
      <p data-en="The rest of the book turns this into a system: who to approach and why, how to invite without a script, the 72 hours that decide whether a new partner stays, and how to build something that grows when you are not there." data-zh="後面的章節把這件事變成一套系統：該找誰、為什麼找他，怎麼邀約而不靠話術，決定新人去留的72小時，以及怎麼建立一個你不在也會長的事業。">The rest of the book turns this into a system: who to approach and why, how to invite without a script, the 72 hours that decide whether a new partner stays, and how to build something that grows when you are not there.</p>
      <div class="cta-actions">
        <a href="book.html" class="btn when-prelaunch" data-en="See the book (on sale 20 October)" data-zh="看本書（10月20日上市）">See the book (on sale 20 October)</a>
        <a href="book.html#buy" class="btn when-launched" data-en="Get the book: RM 29.90" data-zh="購買電子書：RM 29.90">Get the book: RM 29.90</a>
        <a href="{wa}" class="btn btn--ghost" target="_blank" rel="noopener" data-en="Rather talk? Message me" data-zh="想聊聊？傳訊息給我">Rather talk? Message me</a>
      </div>
      <form class="field" action="https://app.kit.com/forms/9983525/subscriptions" method="post" data-ajax>
        <label class="sr" for="c1-em" data-en="Email address" data-zh="電子郵件">Email address</label>
        <input id="c1-em" type="email" name="email_address" placeholder="Your email" data-en="Your email" data-zh="你的電子郵件" autocomplete="email" required>
        <input type="hidden" name="tags" value="book-chapter">
        <button type="submit" data-en="Not ready yet? Keep me posted" data-zh="還沒決定，有消息通知我">Not ready yet? Keep me posted</button>
      </form>
      <p class="form-ok" tabindex="-1" hidden data-en="Check your inbox to confirm. No spam, unsubscribe any time." data-zh="請到信箱確認訂閱。不發垃圾信，隨時可退訂。">Check your inbox to confirm. No spam, unsubscribe any time.</p>
    </aside>
  </div>
</main>

<!-- shell:footer -->
<!-- /shell:footer -->
</body>
</html>
'''


if __name__ == '__main__':
    docx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DOCX
    if not os.path.exists(docx):
        sys.exit(f'manuscript not found: {docx}')
    blocks = load_chapter(docx)
    convert_figures(docx)
    page = build_page(render(blocks))
    open(os.path.join(ROOT, 'chapter-1.html'), 'w', encoding='utf-8').write(page)
    chars = sum(len(b['text']) for b in blocks)
    print(f'chapter-1.html written from {os.path.basename(docx)} — {len(blocks)} blocks, {chars} chars')
    if 'X' in WHATSAPP or not WHATSAPP.isdigit():
        print('  ! WhatsApp number looks wrong (WHATSAPP in this script)', file=sys.stderr)
