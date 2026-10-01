# Book facts alignment — for any agent editing mikaelchew.com

> **2026-10-01:** Mikael checked: the first commission cheque was **RM 128**, not RM 28. Every mention below and across the site now says RM 128.

**Written 2026-09-30 by the book-editing session.** Mikael has just finished a line-by-line truth check of every story in the manuscript. Several facts the website repeats have **changed**. This file lists what the site must say from now on, and where the old versions live. The manuscript itself has **not been updated yet** — the book session will apply everything in one pass and then regenerate `chapter-1.html` (see §4).

Source of truth for every decision: the book project's `editorial/Story_Verification_2026-09-29.md` (private; not in this repo).

## 1. The facts that changed

| Topic | OLD (wrong) | NEW (use this) |
|---|---|---|
| **RM 128** | "RM 128 in the bank" / 「銀行帳戶裡只剩RM 128」 / 「帳戶餘額：RM 128」 | **RM 128 was his first commission cheque.** 「第一張佣金支票只有RM 128」 / "his first commission cheque was RM 128". Bank balance at the low point ≈ **RM 240**. |
| **Income in the first three months** | "Income: zero" / 「收入：零」 / 「三個月零收入」 | Income was **not** zero: cheque 1 RM 128, cheque 2 higher (family and relatives bought — **never print the month-2 figure**), cheque 3 RM 0. |
| **Costs, first three months** | (unchanged) | Product RM 3,300+, training RM 800+, petrol RM 900+ ≈ **RM 5,000** spent; net loss ≈ RM 3,300. |
| **38 rejections** | "38 people, every one said no" | Roughly **38 people outside his family and relatives**, from a name list of 200, said no. Keep "38" as an approximate count. |
| **The 39th / first customer** | "my first customer, on the 39th attempt"; Aunty Lim "a neighbour" | Aunty Lim was **the first customer who bought because she believed, not out of obligation** (family had bought earlier). She was a teacher who phoned after getting his leaflet and lived ~30 min away (**not** a neighbour). |
| **People coached** | "more than 450" / 「超過450位」 / "450+" | **"nearly 450" / 「將近450位」**. Headline line: 「23年。**近**450名學員。38次拒絕。」. Stat counters: **"400+"**. |
| **Alex** (Ch 1 cautionary tale) | "Alex" | **"Scott"** everywhere. Do not describe it as the author's own team. |
| **Kindle price** | USD 7.99 | **USD 9.99** (already live on book.html). |
| **Chinese punctuation** | 「——」 em dashes | Mikael: *"I don't write like that."* **No 「——」 in any Chinese copy.** Use a comma, colon, full stop or brackets. Chapter-title separators use a plain hyphen: 「第一章：發起召集 - 尋找你的「道」」. |
| **Compliance** | — | Still no income figures, no "passive income", no "financial freedom" promises, no guarantees, no health claims. |

## 2. Where the old versions are (as of commit on 2026-09-30)

- `index.html:262` — home stat **"450+"** → "400+".
- `build_chapter.py:115–117` (meta descriptions EN/ZH) and `:144` (standfirst) — "38 rejections, RM 128 in the bank" / 「帳戶裡的 RM 128」 / "RM 128 left in…" → first-cheque wording; standfirst also has a dash.
- `chapter-1.html` — **generated; do not hand-edit** (see §4).
- `KIT_EMAIL_SETUP.md:37–91` — "Income: zero. Bank balance: RM 128" and 「收入：零。帳戶餘額：RM 128。」 → rewrite with the first-cheque facts; the preview line "38 people said no" can stay.
- `BOOK_LAUNCH_COPY.md` (lines ~31–76) — "450" → "nearly 450"; check every RM 128 / 38 mention; remove 「——」 from Chinese copy.
- `BOOK_LAUNCH_PLAN.md:153` — "450+" → "400+".
- `book.html` — check the hook / FAQ / schema for RM 128, 450, and 「——」 (23 occurrences of 「——」 at time of writing).
- Also the KDP store description (not in this repo) — the book session owns it.

**Status 2026-09-30 (website session, second pass):** done. The book session applied the full story verification to `Manuscript_v1.9_TYPESET_READY.docx` (book repo commit `0bec953`), and the site now matches it:
- `chapter-1.html` + `/zh/` regenerated from the corrected manuscript.
- `book.html` chapter descriptions rewritten to the manuscript: Ch 1 (first cheque), Ch 3 (no partner income claim), Ch 4 (approximate rates), Ch 5 (friendship not lost), Ch 6 (Irene), Ch 7 (Aunty Lim per the verified events), Ch 9 ("the few", not "5% rule"), Ch 10 (Leon), Ch 11 (caught up with KL), Ch 12 (Vivian, no percentages), Ch 13 (no financial-freedom promise). Ch 4 pull quote uses the manuscript's approximate figures.
- `blog/saying-no-prospect.html` retold the Ch 4 sprint with the old exact numbers and "first two years" framing; now matches the manuscript.
- `BOOK_LAUNCH_COPY.md`, `KIT_EMAIL_SETUP.md`, `MARBLISM_INSTRUCTIONS.md`, `llms.txt`, `index.html` schema and stats updated.
- 「——」 removed site-wide (644 on 31 pages, rule-based: paired dashes to brackets, single to comma or colon; attributions to brackets). `/zh/` regenerated.
- **Not done here:** `downloads/chapter1-sample.pdf` is still the 2026-09-19 build (no link to it from the site; see `build_chapter.py` header). The KDP description is the book session's.

## 3. Suggested wording (Chinese)

- Hook: 「23年前，我連續被38個人拒絕，第一張佣金支票只有RM 128。」
- Stat line: 「23年。近450名學員。38次拒絕。」
- EN: "Twenty-three years ago, 38 people turned him down and his first commission cheque was RM 128."

## 4. Order of operations

1. The book session applies all story changes to the manuscript (not done yet).
2. Then run `/usr/bin/python3 build_chapter.py` and `/usr/bin/python3 build_zh.py` to regenerate `chapter-1.html` and `/zh/chapter-1.html` — do **not** patch the chapter body by hand, or it will be overwritten.
3. Everything in §2 that is *not* generated can be fixed now.
