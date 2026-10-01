# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: book readers.** Direct-selling and network-marketing leaders, two or more years in the business, many Malaysian Chinese and often 40–60. They feel stuck at their level, are tired of "hustle harder" advice, and distrust hype. Their job on the site: decide whether *The Art of War for Direct Selling* 《直銷孫子兵法之不戰而勝》 is worth their time and money, usually by reading Chapter 1 first, then buy it (ebook launches 20 October 2026; print follows 4–8 weeks later).

**Secondary:** event organisers booking Mikael to speak, and leaders who want mentorship. Both matter, but neither may outrank the book during the launch campaign.

## Product Purpose

mikaelchew.com is Mikael Chew's personal-brand hub and the book's home and sales page. Success during the campaign: visitors read Chapter 1, join the launch list, and buy the ebook direct (highest margin). After launch, the site keeps converting readers and supports speaking and mentorship enquiries.

## Positioning

A dual perspective few in the industry hold: 8 years building teams in the field, 15 in senior corporate management across three multinational direct-selling companies, nearly 450 professionals mentored. The book applies Sun Tzu's *Art of War* as a working strategic framework, not decoration, and every chapter pairs a principle with a real, verified story and a weekly exercise. The stance is anti-hype: strategy over hustle, ethics as a competitive advantage. The book is company-agnostic.

## Operating Context

- Readers arrive from Facebook, LinkedIn, WhatsApp and email (the Kit launch list), largely on phones, and also read on desktop.
- The book is written in Traditional Chinese; the site is English-first with a generated Traditional Chinese mirror under `/zh/` (`build_zh.py`).
- Chapter 1 is published ungated as `chapter-1.html`, generated from the manuscript by `build_chapter.py`; never hand-edit it.
- Direct sale: ebook RM 29.90 via the site's Billplz (FPX) checkout; Kindle USD 9.99. Print price not yet confirmed.

## Capabilities and Constraints

- Hand-written static HTML/CSS/vanilla JS on GitHub Pages. No framework, no npm dependency chain. **Pushing to `main` publishes immediately.**
- Fonts and Font Awesome are self-hosted under `vendor/` for performance; Core Web Vitals on mobile matter.
- Every EN page with a Chinese equivalent must be regenerated through `build_zh.py`; copy carries `data-en` / `data-zh` pairs.
- Undecided: print-edition price and timing; English edition (a post-launch consideration only, never promised).

## Brand Commitments

- Voice: a strategic advisor speaking to peers, warm but firm, story-first, no hype. No "passive income", "financial freedom", income claims, guarantees, scarcity tactics, countdown urgency or engagement bait (`MARBLISM_INSTRUCTIONS.md`, Vault voice profile and anti-AI writing rules).
- Chinese copy uses no 「——」 dashes (Mikael: "I don't write like that").
- Language is part of the identity: the Chinese title and characters (e.g. 不戰而勝) are design material on both the English and Chinese versions, while English copy stays primary on the main site.
- Brand palette per `MARBLISM_INSTRUCTIONS.md`: black #1a1a1a, beige #f5f0e8, red #c0392b. The current site's visual implementation is being replaced (redesign approved 2026-10-01); the palette is a stated commitment, open to extension in the new world.
- Name is set as MIKAEL CHEW. Sun Tzu / generals / terrain / campaign metaphors are the brand's native language.

## Evidence on Hand

- Real, named LinkedIn recommendations (quoted word-for-word on the homepage). They carry no star ratings; never show stars.
- Real stage and teaching photography in `images/` (APAC stage, big stage, large audience, speaking, classroom, team).
- The book: 13 chapters in four parts (Foundations, The Battlefield, Building Your Army, The General's Path), chapter blurbs on `book.html`, and the full Chapter 1.
- Verified story facts per `BOOK_FACTS_ALIGNMENT.md` (first commission cheque RM 128, 38 rejections, nearly 450 mentored, "400+" on stat counters).
- **Absent, never fabricate:** book endorsements, press coverage, video, reader reviews, sales figures, star ratings.

## Product Principles

1. The book leads until launch is over; every page should make reading Chapter 1 or buying the book the obvious next step.
2. Prove, don't claim: real stories, real numbers from the verified manuscript, real photographs.
3. Strategy, not hype: confidence comes from specificity and restraint, never urgency tricks.
4. Bilingual by nature: the Chinese title is the product, not a translation footnote.
5. One source of truth for book facts: the manuscript and `BOOK_FACTS_ALIGNMENT.md`.

## Accessibility & Inclusion

Much of the core audience is 40–60: generous text sizes and contrast, no tiny grey labels, full `prefers-reduced-motion` support, real heading structure, and correct `lang` attributes on Chinese content.
