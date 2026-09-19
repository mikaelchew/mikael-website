#!/usr/bin/env python3
"""Generate chapter-1.html (the free-to-read sample) from the canonical manuscript.

The chapter is NOT hand-maintained: run this after any manuscript change so the
free sample can never drift from the book. (The old downloads/chapter1-sample.pdf
drifted for two months and shipped text that had been corrected for compliance.)

Usage:  /usr/bin/python3 build_chapter.py [path/to/Manuscript.docx]
Then:   /usr/bin/python3 build_zh.py      # regenerates /zh/chapter-1.html
"""
import sys, os, re, zipfile, html
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCX = os.path.normpath(os.path.join(
    ROOT, '..', '..', 'writing', 'Claude_Book_Editing', 'Manuscript_v1.9_TYPESET_READY.docx'))

# --- where the mid-chapter soft CTA goes (before this heading) ---
MID_CTA_BEFORE = '用Ikigai找到你獨特的切入點'
# --- WhatsApp: replace 60XXXXXXXXX with Mikael's number in international format ---
WHATSAPP = '60XXXXXXXXX'
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


def render(blocks):
    out, open_list, mid_done = [], None, False
    for b in blocks:
        if b['style'] == 'Heading2':
            continue  # page supplies its own <h1>
        if b['style'] == 'Heading3' and not mid_done and MID_CTA_BEFORE in b['text']:
            if open_list:
                out.append(f'</{open_list}>'); open_list = None
            out.append(MID_CTA_HTML); mid_done = True
        if b['list']:
            if open_list != b['list']:
                if open_list:
                    out.append(f'</{open_list}>')
                out.append(f'<{b["list"]}>'); open_list = b['list']
            out.append(f'  <li>{inline(b["runs"])}</li>')
            continue
        if open_list:
            out.append(f'</{open_list}>'); open_list = None
        if b['style'] == 'Heading3':
            out.append(f'<h2>{inline(b["runs"])}</h2>')
        else:
            out.append(f'<p>{inline(b["runs"])}</p>')
    if open_list:
        out.append(f'</{open_list}>')
    if not mid_done:
        print('  ! mid-chapter CTA anchor not found — CTA omitted', file=sys.stderr)
    return '\n'.join(out)


MID_CTA_HTML = '''<aside class="chapter-cta chapter-cta-soft">
  <p data-en="Still with me? The other twelve chapters go further — prospecting, invitation, the golden 72 hours, leading without being needed." data-zh="還在看？後面十二章走得更遠——拓客、邀約、黃金72小時，以及怎麼帶團隊帶到不需要你。">Still with me? The other twelve chapters go further — prospecting, invitation, the golden 72 hours, leading without being needed.</p>
  <a href="book.html#buy" class="btn btn-outline-light" data-en="See the full book" data-zh="看完整本書">See the full book</a>
</aside>'''


def build_page(chapter_html):
    src = open(os.path.join(ROOT, 'contact.html'), encoding='utf-8').read()
    nav_end = src.index('<!-- ========== ', src.index('<!-- ========== NAVBAR ========== -->') + 10)
    head_nav = src[:nav_end]
    footer = src[src.index('  <!-- ========== FOOTER ========== -->'):]

    desc_en = ("Read Chapter 1 of The Art of War for Direct Selling free: 38 rejections, "
               "RM 28 in the bank, and the idea that changed everything.")
    desc_zh = "免費閱讀《直銷孫子兵法之不戰而勝》第一章：38次拒絕、帳戶裡的 RM 28，以及那晚我找到的「道」。"
    head_nav = (head_nav
        .replace('<title>Contact — Mikael Chew</title>',
                 '<title>Read Chapter 1 Free — 直銷孫子兵法之不戰而勝</title>')
        .replace('content="Get in touch with Mikael Chew — for speaking engagements, mentorship inquiries, media requests, or general questions."',
                 f'data-zh="{desc_zh}" content="{desc_en}"')
        .replace('<meta name="keywords" content="Mikael Chew, contact, speaking engagement, mentorship, direct selling coach, Kuala Lumpur">',
                 '<meta name="keywords" content="直銷, 孫子兵法, 直銷書, 組織行銷, 領導力, Mikael Chew, 周俊德">')
        .replace('content="Contact — Mikael Chew"', 'content="Read Chapter 1 Free — 直銷孫子兵法之不戰而勝"')
        .replace('content="Have a question or want to connect? Get in touch with Mikael Chew."', f'content="{desc_en}"')
        .replace('content="https://www.mikaelchew.com/images/mikael-chew.jpg"',
                 'content="https://www.mikaelchew.com/images/book-social-card.jpg"')
        .replace('content="https://www.mikaelchew.com/contact.html"',
                 'content="https://www.mikaelchew.com/chapter-1.html"')
        # the skeleton comes from contact.html — move the nav highlight to Book
        .replace('<a href="contact.html" class="active" data-en="Contact" data-zh="聯繫">Contact</a>',
                 '<a href="contact.html" data-en="Contact" data-zh="聯繫">Contact</a>')
        .replace('<a href="book.html" data-en="Book" data-zh="著作">Book</a>',
                 '<a href="book.html" class="active" data-en="Book" data-zh="著作">Book</a>'))

    wa = f'https://wa.me/{WHATSAPP}?text={WA_TEXT.replace(" ", "%20")}'
    main = f'''  <!-- ========== CHAPTER 1 (generated by build_chapter.py — do not edit by hand) ========== -->
  <section class="section chapter-read">
    <div class="container">
      <div class="chapter-head">
        <span class="section-label" data-en="FREE SAMPLE — CHAPTER 1" data-zh="免費試讀 — 第一章">FREE SAMPLE — CHAPTER 1</span>
        <h1>第一章：發起召集 — 尋找你的「道」</h1>
        <p class="chapter-standfirst" data-en="The whole first chapter, free, no signup. It is the night I nearly quit — 38 rejections, RM 28 left in the bank — and what I worked out instead." data-zh="整個第一章，免費，不用留資料。那是我差點放棄的晚上——38次拒絕，帳戶裡只剩 RM 28——以及我後來想通的事。">The whole first chapter, free, no signup. It is the night I nearly quit — 38 rejections, RM 28 left in the bank — and what I worked out instead.</p>
        <p class="chapter-langnote" data-en="The book is written in Traditional Chinese. This chapter is presented exactly as written." data-zh="本書以繁體中文寫成，本章依原文呈現。">The book is written in Traditional Chinese. This chapter is presented exactly as written.</p>
      </div>

      <article class="chapter-body">
{chapter_html}
      </article>

      <aside class="chapter-cta chapter-cta-end">
        <h2 data-en="That was one chapter. There are twelve more." data-zh="這是第一章。後面還有十二章。">That was one chapter. There are twelve more.</h2>
        <p data-en="The rest of the book turns this into a system: who to approach and why, how to invite without a script, the 72 hours that decide whether a new partner stays, and how to build something that grows when you are not there." data-zh="後面的章節把這件事變成一套系統：該找誰、為什麼找他，怎麼邀約而不靠話術，決定新人去留的72小時，以及怎麼建立一個你不在也會長的事業。">The rest of the book turns this into a system: who to approach and why, how to invite without a script, the 72 hours that decide whether a new partner stays, and how to build something that grows when you are not there.</p>
        <div class="chapter-cta-actions">
          <a href="book.html#buy" class="btn btn-primary" data-en="Get the book — RM 29.90" data-zh="購買電子書 — RM 29.90">Get the book — RM 29.90</a>
          <a href="{wa}" class="btn btn-outline-light" target="_blank" rel="noopener" data-en="Rather talk? Message me" data-zh="想聊聊？傳訊息給我">Rather talk? Message me</a>
        </div>
        <form class="newsletter-form chapter-notify" action="https://mikaelchew.us13.list-manage.com/subscribe/post?u=2f80eb2c2614b95d65a07406e&amp;id=043e3f13be&amp;f_id=00608de2f0" method="post" target="_blank">
          <input type="email" name="EMAIL" aria-label="Email address" placeholder="your@email.com" required>
          <input type="hidden" name="tags" value="book-chapter">
          <div aria-hidden="true" style="position:absolute;left:-5000px;"><input type="text" name="b_2f80eb2c2614b95d65a07406e_043e3f13be" tabindex="-1" value=""></div>
          <button type="submit" data-en="Not ready yet — keep me posted" data-zh="還沒決定——有消息通知我">Not ready yet — keep me posted</button>
        </form>
      </aside>
    </div>
  </section>

'''
    return head_nav + main + footer


if __name__ == '__main__':
    docx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DOCX
    if not os.path.exists(docx):
        sys.exit(f'manuscript not found: {docx}')
    blocks = load_chapter(docx)
    page = build_page(render(blocks))
    open(os.path.join(ROOT, 'chapter-1.html'), 'w', encoding='utf-8').write(page)
    chars = sum(len(b['text']) for b in blocks)
    print(f'chapter-1.html written from {os.path.basename(docx)} — {len(blocks)} blocks, {chars} chars')
    if WHATSAPP.startswith('60XXX'):
        print('  ! WhatsApp number is still a placeholder (WHATSAPP in this script)', file=sys.stderr)
