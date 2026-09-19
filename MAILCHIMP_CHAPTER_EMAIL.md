# Mailchimp — `book-chapter` automation, replacement copy

**Written 2026-09-19. Replaces whatever that automation sends today.**

## Why this changes

The old automation promised "I'll send Chapter 1 directly to your inbox" and (presumably) attached
`downloads/chapter1-sample.pdf`. Two problems with that:

1. **It drifts.** The attached file was generated in July and still carried text the manuscript had
   since corrected — the same stale-derivative bug that put deleted income figures back on the
   website. Anything sent as a file is a copy that has to be kept in sync by hand.
2. **It sends people away from the site.** The free chapter is now a page — `/chapter-1.html` — with
   the buy CTA in the middle and at the end of it. A PDF in an inbox sells nothing.

**So: send the link, not the file.** One source of truth (the manuscript → `build_chapter.py` →
the page), and every reader lands somewhere that can sell.

## Setup in Mailchimp

1. Mailchimp → **Automations** → the journey triggered by the `book-chapter` tag.
2. Open its email. **Remove the attachment.**
3. Replace subject, preview text and body with the copy below.
4. Set the button URL to `https://www.mikaelchew.com/chapter-1.html`
   (Chinese version of the email: `https://www.mikaelchew.com/zh/chapter-1.html`).
5. Send yourself a test before switching it back on.

`downloads/chapter1-sample.pdf` stays live and current — it is now regenerated from the v1.9
manuscript — so any old link already in the wild still serves correct text. Do not link to it from
anything new.

---

## English version

**Subject:** Chapter 1 is ready for you
**Preview text:** 38 people said no. Here's what happened on the 39th.

Hi [FNAME],

Thanks for asking for Chapter 1.

It's not an attachment — it's a page, so you can read it on whatever you're holding right now, no
download, no app:

**[ Read Chapter 1 → ]** → https://www.mikaelchew.com/chapter-1.html

The chapter opens on the worst night of my direct selling career. Third month in. Product cost
RM 3,300. Training RM 800. Petrol RM 900. Income: zero. Bank balance: RM 28. And 38 people had
already told me no.

What I got wrong wasn't my technique. It was that I had never answered the one question Sun Tzu
puts before all the others — 「道」, the why. That's what Chapter 1 is about, and it's why the 39th
conversation went differently.

Take fifteen minutes with it. If it's useful, the other twelve chapters are on the same site.

Mikael

---

## 中文版本

**主旨：** 第一章已經準備好了
**預覽文字：** 38個人說「不」。第39個人，故事不一樣了。

[FNAME] 你好，

謝謝你索取第一章。

它不是附件，是一個網頁——你現在手上拿著什麼裝置都能直接讀，不必下載，不必裝任何 app：

**［ 閱讀第一章 → ］** → https://www.mikaelchew.com/zh/chapter-1.html

這一章從我直銷生涯最糟的那個晚上開始。入行第三個月。產品成本 RM 3,300，培訓 RM 800，交通油費
RM 900。收入：零。帳戶餘額：RM 28。而那之前，已經有38個人跟我說「不」。

我做錯的不是技巧。是我從來沒有回答孫子擺在所有問題最前面的那一個——「道」，你為何而戰。第一章講
的就是這件事，也是為什麼第39次談話結果不一樣。

給它十五分鐘。如果對你有用，另外十二章在同一個網站上。

周俊德（Mikael）

---

## Two notes on tone

- No launch date and no price in this email. It is the first thing a new subscriber receives; asking
  for money in it costs more than it earns. The chapter page itself carries both CTAs.
- The numbers here (38 rejections, RM 3,300 / RM 800 / RM 900 / RM 28) all come straight from the
  manuscript. Don't round them or add new ones — every number that goes out has to be traceable back
  to the book.
