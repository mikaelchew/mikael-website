# Strategist's Map Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild every page of mikaelchew.com (English and generated `/zh/`) in the approved Strategist's Map world, preview it on Vercel, and merge to `main` on 17 October 2026, three days before the 20 October ebook launch.

**Architecture:**
- **Static HTML/CSS/JS on GitHub Pages.** Small local Python generators keep the 37 pages consistent:
  - a shared header and footer injected from partials;
  - one chapter-data file that feeds both the homepage map and the book page;
  - the existing Chinese and Chapter 1 generators;
  - a font subsetter.
- **Shared front-end code:** `css/site.css` and `js/site.js`. The homepage alone loads `css/map.css` and `js/map.js`.
- **Tests:** stdlib `unittest` plus `lxml`, run against the HTML files that are built and committed.

**Tech Stack:**
- Hand-written HTML, CSS and vanilla JS.
- Python 3.9 at `/usr/bin/python3`, with lxml, fontTools and brotli.
- The Vercel CLI 58 for previews.
- Chrome DevTools MCP for performance traces; the built-in browser for screenshots.

**Spec:** `docs/superpowers/specs/2026-10-01-strategist-map-redesign-design.md`. Read it with this plan. The approved prototype is `redesign/strategist-map/index.html`; it is git-ignored and local only.

## Global Constraints

- **No framework, no npm, no CI build.** Pages are served straight from `main` by GitHub Pages, and pushing `main` publishes the site.
- **Every existing URL keeps working**, along with these in-page anchors: `#buy`, `#print`, `#chapters`, `#free-chapter`, `#notify`.
- **`zh/` and `chapter-1.html` are generated. Never hand-edit them.** Always run Python as `/usr/bin/python3`.
- **Tokens, exactly:**
  - `--table:#22303A`, `--table-deep:#19242C`, `--acetate:#F2F2EE`, `--mute:#B9C4C0`, `--contour:#B6C4BE`
  - `--red:#C0392B` (fills only), `--red-lit:#F0705F` (red text on the table), `--red-text:#A93226` (red text on paper)
  - `--paper:#F5F0E8`, `--ink:#1A1A1A`
- **Easing:** `--ease-out:cubic-bezier(.23,1,.32,1)`, `--ease-move:cubic-bezier(.77,0,.175,1)`, `--ease-impact:cubic-bezier(.55,0,1,.45)` (used for seals only).
- **Fonts:**
  - Overpass 400/600/800/900 for Latin.
  - Noto Serif TC 600/900, subset to the characters inside `.cjk-display` elements, for Chinese display text.
  - Chinese body text uses the system stack: `"PingFang TC","Noto Sans CJK TC","Microsoft JhengHei",sans-serif`.
  - Minimum 15px for any text a reader is meant to read.
- **Integration IDs, unchanged:**
  - Kit forms `9983525` (tags `book-launch`, `book-print`, `book-chapter`), `9983575` and `9983582`.
  - Formspree `xreojdqa`.
  - GA4 `G-ENGNTZ3PPC`.
  - Billplz buy form: `form.book-buy-form[data-endpoint]`, with the existing Apps Script URL copied verbatim from `book.html:399`.
  - WhatsApp `wa.me/60195513038`.
- **GA4 events kept:** `begin_checkout`, `whatsapp_click`, `file_download`, `scroll_depth`, `blog_filter_click`, `blog_show_more_click`, `language_toggle`, `book_waitlist`. `theme_toggle` is retired.
- **Prices and dates:** ebook RM 29.90 direct, Kindle USD 9.99, launch 20 October 2026, FPX-only wording.
- **Speed targets:** LCP under 2.5s on a throttled mid-range phone (homepage and book page); CLS under 0.1 on every page.
- **Copy:**
  - No new factual claims, no stars, no "reader reviews", no "financial freedom" or "passive income", no 「——」 in Chinese.
  - Book facts must match `BOOK_FACTS_ALIGNMENT.md`.
- **Merge** to `main` on **17 October 2026** after Mikael signs off on the Vercel preview. Pushing needs Mikael's explicit OK at that moment.

## Review Focus

1. **A Chinese reader on `/zh/` sees Chinese everywhere**, including text that JavaScript renders: map briefings, rail labels, form confirmations and seals. Task 5 pins this with `test_zh_home_briefing_strings_are_chinese`.
2. **A form submit that can't reach Kit** (offline, blocked or CORS) must still subscribe through a normal form post, not fail silently. Task 3 pins this with `test_forms_keep_action_and_method`, plus a manual offline check.
3. **A half-applied launch switch**, where English says "launched" and Chinese says "prelaunch", must be impossible. Task 2 pins this with `test_phase_identical_on_every_page`.
4. **Old shared links with anchors** must still land on the right section. Task 6 pins this with `test_legacy_anchors_exist`.
5. **No-JS and low-end phones** must still get the full chapter list and every call to action. Task 5 pins this with `test_home_content_present_without_js`, plus the low-memory static fallback.

---

## File structure

| Path | Responsibility |
|---|---|
| `data/site.json` | `{"phase":"prelaunch"}`: the one launch flag |
| `data/chapters.json` | Parts and 13 chapters: titles, one-liners (EN + ZH), map coordinates, the `free` flag |
| `partials/header.html`, `partials/footer.html` | Shared top bar, footer and SVG symbols (seals, ink filter) |
| `build_shell.py` | Injects the partials between `<!-- shell:header -->…<!-- /shell:header -->` and the footer markers, sets `<html data-phase>`, and marks the current nav item from `<body data-nav>` |
| `build_chapters.py` | Renders the chapter markup between `<!-- chapters:map -->` (homepage) and `<!-- chapters:book -->` (book page) markers |
| `build_fonts.py` | Writes the Noto Serif TC subset woff2 files from the `.cjk-display` characters |
| `build_all.sh` | Runs, in order: `build_shell`, `build_chapters`, `build_chapter.py`, `build_zh.py`, `build_fonts` |
| `css/site.css` | Tokens, base styles and every shared component |
| `css/map.css`, `js/map.js` | The homepage map only |
| `js/site.js` | Nav menu, form submit, buy form, GA4 `trackEvent`, seal stamp, phase |
| `vendor/fonts/site-fonts.css` + woff2 | Self-hosted fonts |
| `images/map/terrain.svg`, `images/print/*.webp` + `images/print/README.md` | Terrain and recon prints, with their provenance |
| `tools/halftone.py`, `tools/contours.py`, `tools/retemplate_posts.py` | Asset and migration tools, moved in from `redesign/` |
| `tests/test_*.py` | unittest suites (run all: `/usr/bin/python3 -m unittest discover -s tests -v`) |

**Two additions to the spec's generator list need noting** (raise both with Mikael at plan review):
- `build_shell.py`, so 37 headers can't drift apart;
- `build_chapters.py`, which delivers the spec's "chapter data in one file" (§5, §12).

The phase flag lives in `data/site.json`, written into `<html data-phase>` by `build_shell.py`, rather than in `js/site.js` as the spec said. It still meets the spec's goal: one change flips every page, English and Chinese.

**Calendar:**

| Date | Tasks |
|---|---|
| 1–2 Oct | 1–3 |
| 3–5 Oct | 4–5 |
| 6–8 Oct | 6–8 |
| 9 Oct | 9: preview and integration tests |
| 10–12 Oct | 10 |
| 13–14 Oct | 11 |
| 15 Oct | 12 |
| 16 Oct | 13: review, sign-off |
| 17 Oct | 14: merge |

**Cut line (spec §11.3):** Tasks 1–9 are launch-critical. Tasks 10–12 can slip to launch week 1.

---

### Task 1: Worktree, tooling, test harness

**Files:**
- Create: `tests/__init__.py`, `tests/helpers.py`, `tests/test_harness.py`
- Modify: `PROJECT_HANDOFF.md` (§8 migration checklist: add the fonttools/brotli install)

**Interfaces:**
- Produces:
  - `tests.helpers.ROOT: str`
  - `tests.helpers.en_pages() -> list[str]`: root `*.html` plus `blog/*.html`, excluding `chapter-1.html`, `zh/` and `redesign/`
  - `tests.helpers.zh_pages() -> list[str]`
  - `tests.helpers.doc(path) -> lxml.html.HtmlElement`

- [ ] **Step 1:** Create the worktree on branch `redesign/strategist-map` using superpowers:using-git-worktrees, at `.claude/worktrees/strategist-map`. `.claude/` is git-ignored.
- [ ] **Step 2:** Install the font tools. This needs Mikael's OK: it downloads from PyPI. Run `/usr/bin/python3 -m pip install --user fonttools brotli`, then check that `/usr/bin/python3 -c "import fontTools, brotli"` exits 0.
- [ ] **Step 3: Write the failing test** `test_harness.py::test_every_en_page_parses`. It asserts that `en_pages()` is non-empty and that every page parses with an `<html>` root.
- [ ] **Step 4:** Run `/usr/bin/python3 -m unittest tests.test_harness -v`. Expected: an ImportError, because `tests.helpers` doesn't exist yet.
- [ ] **Step 5:** Implement `tests/helpers.py` (glob plus `lxml.html.parse`).
- [ ] **Step 6:** Run it again. Expected: PASS.
- [ ] **Step 7:** Add the install line to PROJECT_HANDOFF.md §8, next to the lxml step.
- [ ] **Step 8: Commit:** `git commit -m "Redesign: test harness and tooling"`.

### Task 2: Launch flag, shared header and footer

**Files:**
- Create: `data/site.json`, `partials/header.html`, `partials/footer.html`, `build_shell.py`, `tests/test_shell.py`
- Modify: every EN page. Add the shell markers once, and add `data-nav` on `<body>` with values `home`, `book`, `about`, `writing`, `speaking`, `work`, `contact` or `none`.

**Interfaces:**
- Produces:
  - `build_shell.apply(html: str, nav: str, phase: str) -> str`
  - `build_shell.main() -> int` (number of pages written)
  - Header markup: `.bar` holding `.brand` and `nav` with `a[data-nav]`. The current item gets `aria-current="page"`.
  - The language link is `a.lang-link`. Its href is the matching `/zh/` page, and `build_zh.py` flips it (Task 4).
  - The footer carries the `<svg><defs>` with `#inked`, `#seal-launch` (十月上市), `#seal-live` (已上市), `#seal-free` (免費試讀) and `#seal-sent` (已發送).

- [ ] **Step 1: Write the failing tests:**
  - `test_phase_identical_on_every_page`: every page in `en_pages()` plus `zh_pages()` has `html/@data-phase` equal to `json.load(data/site.json)["phase"]`.
  - `test_header_identical_except_current`: the header subtree, with `aria-current` stripped, is byte-identical across all EN pages.
  - `test_current_nav_marked`: on book.html, `a[data-nav="book"]` has `aria-current="page"`.
- [ ] **Step 2:** Run `/usr/bin/python3 -m unittest tests.test_shell -v`. Expected: FAIL.
- [ ] **Step 3: Write the partials** from the prototype's `.bar` and footer:
  - six bilingual nav items: The Book 著作, About 關於, Writing 專欄, Speaking 演講, Work With Me 合作, plus the language link;
  - a phone menu button (`button.menu-btn[aria-expanded]`);
  - a skip link to `#main`.

  Then implement `build_shell.py`. It replaces the text between the markers and sets `data-phase` on `<html>`. Use string slicing between the markers; don't reserialise with lxml, so the rest of the page stays exactly as written.
- [ ] **Step 4:** Run `build_shell.py`, then `build_zh.py`, then the tests. Expected: PASS.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: shared shell and launch flag"`.

### Task 3: Design system CSS, site JS, forms

**Files:**
- Create: `css/site.css`, `js/site.js`, `tests/test_integrations.py`
- Modify: the shell partials, to load `css/site.css` and `js/site.js` with `defer`

**Interfaces:**
- Consumes: the Task 2 header and footer markup.
- Produces, in `js/site.js` (global functions):
  - `trackEvent(name: string, params?: object): void` wraps `gtag`.
  - On any host other than `www.mikaelchew.com` or `mikaelchew.com`, `gtag('config','G-ENGNTZ3PPC',{debug_mode:true})` is called instead of the normal config, so preview traffic shows in DebugView only.
  - `initForms()`: every `form[data-ajax]` submits by `fetch(action,{method:'POST',body:FormData,mode:'no-cors'})`. On resolve it swaps in `.form-ok` (aria-live polite). On reject it calls `form.submit()`, the normal post. It fires `book_waitlist` when the hidden tag is `book-chapter`, as `js/main.js:424` does today.
  - `initBuyForm()` is ported **unchanged** from `js/main.js:500-540`, including `begin_checkout`.
  - `initNav()`, `initSeals()`: a seal `[data-stamp]` gets `.press` once it's 60% visible and its `img` ancestor has decoded.
  - `whatsapp_click`, `file_download`, `scroll_depth` and `language_toggle` are ported from `js/main.js` with the same names and parameters.
- Produces, in `css/site.css`: the tokens and the components from spec §4.3, as `.btn`, `.btn--ghost`, `.seal`, `.print`, `.brief`, `.band`, `.legend`, `.field` (form), `.prose` (reading layout on paper).
  - Phase rules: `[data-phase="prelaunch"] .when-launched{display:none}` and `[data-phase="launched"] .when-prelaunch{display:none}`.

- [ ] **Step 1: Write the failing tests:**
  - `test_forms_keep_action_and_method`: every `form[data-ajax]` has an `action` starting `https://app.kit.com/forms/` or `https://formspree.io/f/xreojdqa`, and `method="post"`.
  - `test_kit_tags_valid`: every hidden `tags` input value is one of `book-launch`, `book-print`, `book-chapter`, and the form ID is one of `9983525`, `9983575`, `9983582`.
  - `test_buy_form_endpoint_unchanged`: `book.html` `form.book-buy-form/@data-endpoint` equals the URL copied from `git show main:book.html`.
  - `test_ga4_events_present`: `js/site.js` contains each of the 8 event names in the Global Constraints.
- [ ] **Step 2:** Run `/usr/bin/python3 -m unittest tests.test_integrations -v`. Expected: FAIL.
- [ ] **Step 3:** Implement `site.css` and `site.js` to the interfaces above. Take the component CSS from the prototype; drop `backdrop-filter` and thick coloured bars.
- [ ] **Step 4:** Run the tests. Expected: PASS for everything except the book-page tests, which go green in Task 6.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: design system and site JS"`.

### Task 4: Fonts and the Chinese build

**Files:**
- Create: `build_fonts.py`, `vendor/fonts/site-fonts.css`, `vendor/fonts/overpass-{400,600,800,900}-latin.woff2`, `vendor/fonts/noto-serif-tc-{600,900}-subset.woff2`, `tests/test_fonts.py`, `tests/test_zh.py`, `build_all.sh`
- Modify: `build_zh.py`

**Interfaces:**
- `build_fonts.collect(pages: list[str]) -> str` returns the sorted unique CJK characters inside `.cjk-display` elements, across EN and ZH pages.
- `build_fonts.main()` writes the subset woff2 files.
- `build_zh.py`:
  - leaves elements carrying `data-zh-only` untouched;
  - rewrites `a.lang-link` to point at the EN equivalent and changes its text to `English`.

- [ ] **Step 1:** Fetch the source fonts. This needs Mikael's OK: it downloads OFL files from the `google/fonts` GitHub repo, about 0.3 MB of Overpass static TTFs and about 20 MB of the Noto Serif TC variable font.
  - Keep the sources in `tools/font-src/`, git-ignored.
  - Subset Overpass to Latin with `pyftsubset --unicodes=U+0000-00FF,U+2010-2027,U+20AC --flavor=woff2`.
- [ ] **Step 2: Write the failing tests:**
  - `test_subset_covers_display_chars`: every character from `collect()` is in the cmap of `noto-serif-tc-900-subset.woff2`, read with `fontTools.ttLib.TTFont`.
  - `test_zh_lang_link_points_back`: `zh/book.html` has `a.lang-link/@href` `../book.html` and text `English`.
  - `test_zh_only_untouched`: an element with `data-zh-only` keeps the same text in `book.html` and `zh/book.html`.
- [ ] **Step 3:** Run `/usr/bin/python3 -m unittest tests.test_fonts tests.test_zh -v`. Expected: FAIL.
- [ ] **Step 4:** Implement the `build_fonts.py` and `build_zh.py` changes. `build_all.sh` runs the five generators in order and stops on the first failure (`set -e`).
- [ ] **Step 5:** Run `./build_all.sh` and then the tests. Expected: PASS. The subset woff2 should be under 150 KB per weight; record the actual size in the commit message.
- [ ] **Step 6: Commit:** `git commit -m "Redesign: self-hosted fonts and zh build changes"`.

### Task 5: Homepage, the Map

**Files:**
- Create: `data/chapters.json`, `build_chapters.py`, `css/map.css`, `js/map.js`, `images/map/terrain.svg`, `images/print/{field,boardroom}.webp`, `images/print/README.md`, `tools/{halftone,contours}.py`, `tests/test_chapters.py`, `tests/test_home.py`
- Modify: `index.html`

**Interfaces:**
- `data/chapters.json` holds:

  ```
  {"parts":[{"en":"Foundations","zh":"基礎"},…4],
   "chapters":[{"n":1,"part":0,"zh":"發起召集","en":"Finding Your Dao",
                "line_en":"…","line_zh":"…","x":230,"y":1290,"free":true},…13]}
  ```

  Coordinates and English lines come from the prototype's `CH` array. The `line_zh` one-liners are adapted from book.html's existing `data-zh` chapter descriptions, rewritten to the verified facts with no 「——」, and sent to Mikael for approval with this task's review.
- `build_chapters.render_map(data) -> str` produces `<ol class="chapters">` with `li[data-x][data-y][data-part]` holding `.n`, `b[data-en][data-zh]`, `.zh.cjk-display`, `p[data-en][data-zh]`.
- `build_chapters.render_book(data) -> str` produces the book page's Part-grouped briefing cards.
- `js/map.js`, `initMap(root: HTMLElement): void`, reads every waypoint from `root.querySelectorAll('.chapters li')`; there is no JS data array. It ports the prototype's halt/advance/finale logic, its IntersectionObserver-gated `requestAnimationFrame` loop and its transform camera.
  - **Static fallback:** when reduced motion is on, OR `navigator.deviceMemory <= 2`, OR the median frame time over the first 30 frames exceeds 34ms, the page drops the `motion` class and shows the whole campaign.

- [ ] **Step 1: Write the failing tests:**
  - `test_thirteen_chapters_in_four_parts`: the JSON has 13 chapters, part indices are 0–3, and the counts per part are 3, 4, 2, 4.
  - `test_chapter_facts_current`: no chapter line contains "450+", "RM 28 in the bank", "Alex", "most successful partner", "50% stronger" or "——".
  - `test_home_content_present_without_js`: the static `index.html` holds 13 `.chapters li`, the "Read Chapter 1" link to `chapter-1.html`, and a Kit 9983525 form carrying the tag `book-launch`.
  - `test_zh_home_briefing_strings_are_chinese`: every `.chapters li p` in `zh/index.html` contains CJK characters and no ASCII words longer than 3 letters, apart from FORMHD, RM and numbers.
  - `test_prints_have_phone_variant`: every `img` under `.print` has a `srcset` containing a `-600.webp` candidate.
  - `test_print_provenance`: every file in `images/print/` and `images/map/` is listed in `images/print/README.md` with its source photo and generating script.
- [ ] **Step 2:** Run `/usr/bin/python3 -m unittest tests.test_chapters tests.test_home -v`. Expected: FAIL.
- [ ] **Step 3:** Move the assets. Copy `redesign/strategist-map/img/*` to `images/map/` and `images/print/`, the tools to `tools/`, and write the provenance README. Generate 600px-wide phone variants of each print (`*-600.webp`), and serve them with `srcset`/`sizes` (spec §5).
- [ ] **Step 4:** Implement `chapters.json`, `build_chapters.py`, and `index.html` from the prototype's markup. Mark CJK display text `.cjk-display`; mark the vertical legend `data-zh-only`. Then write `css/map.css` and `js/map.js` to the interfaces above, with the prelaunch and launched finale using `.when-*`.
- [ ] **Step 5:** Run `./build_all.sh` and then the tests. Expected: PASS.
- [ ] **Step 6: Verify** in one batched round:
  - built-in browser screenshots at 1440×900 and 375×812: top, halt 7 and the finale;
  - the same at 375×812 on `/zh/`;
  - `npx impeccable detect --json index.html`: no findings, other than any already recorded as exceptions;
  - a Chrome DevTools trace at 375×812, CPU ×4, Slow 4G: LCP under 2.5s and CLS under 0.1, numbers recorded in the commit message;
  - a scroll-smoothness pass as on 1 October: no frames over 50ms on the second pass.
- [ ] **Step 7: Commit:** `git commit -m "Redesign: homepage map (LCP …s, CLS …)"`.

### Task 6: Book page, the Dossier

**Files:**
- Modify: `book.html`
- Test: `tests/test_book.py`

**Interfaces:**
- Consumes:
  - from Task 5: `build_chapters.render_book`, the markers `<!-- chapters:book -->`;
  - from Task 3: the `.when-prelaunch` and `.when-launched` classes, `initBuyForm`, and `form[data-ajax]`.

- [ ] **Step 1: Write the failing tests:**
  - `test_legacy_anchors_exist`: `#buy`, `#print`, `#chapters`, `#free-chapter` and `#notify` exist on `book.html` and `zh/book.html`.
  - `test_buy_hidden_prelaunch`: `#buy` has the class `when-launched`, and there is no `hidden` attribute (the phase class handles visibility).
  - `test_faq_no_english_edition_claim`: the FAQ text and the FAQPage JSON-LD do not contain "being prepared in both English".
  - `test_book_structured_data`: the `Book` JSON-LD keeps the name, alternateName and author, and `datePublished` reads `2026-10-20`.
  - `test_buy_form_endpoint_unchanged` from Task 3 now passes.
- [ ] **Step 2:** Run `/usr/bin/python3 -m unittest tests.test_book -v`. Expected: FAIL.
- [ ] **Step 3:** Rebuild `book.html` to spec §6.1. Copy over unchanged:
  - the buy form, the Billplz note, the refund link, the Kindle card (`#AMAZON_URL_PENDING` stays until Mikael gives the URL);
  - the print waitlist with its WhatsApp line;
  - the team-licence line.

  Drop "BEST VALUE". The FAQ English-edition answer becomes "The book is in Traditional Chinese. An English edition is being considered for after launch; join the newsletter to hear first." with the matching `data-zh`, and the JSON-LD is updated to match.
- [ ] **Step 4:** Run `./build_all.sh` and then the tests. Expected: PASS.
- [ ] **Step 5: Verify:**
  - screenshots at 1440 and 375, with the phase set to both `prelaunch` and `launched` (temporarily switch `data/site.json`, rebuild, then revert);
  - the Impeccable detector;
  - a DevTools trace: LCP under 2.5s.
- [ ] **Step 6: Commit:** `git commit -m "Redesign: book page"`.

### Task 7: Chapter 1 and thank-you pages

**Files:**
- Modify: `build_chapter.py` (template only), `book-thank-you.html`
- Test: `tests/test_reading.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_chapter1_lang`: the chapter body container in `chapter-1.html` has `lang="zh-Hant"`.
  - `test_chapter1_ctas`: the page has 2 buy/launch calls to action using `.btn`, and both respect the phase classes.
  - `test_thanks_nav_book`: `book-thank-you.html` has `body[data-nav="book"]` and the `#seal-sent` seal.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Restyle the template in `build_chapter.py` as a `.prose` reading page on `--paper`, with the shell markers and the calls to action. Don't change how it extracts the manuscript. Rebuild the thank-you page to spec §6.3.
- [ ] **Step 4:** Run `./build_all.sh`, then the tests (expected: PASS), then screenshots at 375 of the chapter middle and of the thank-you page.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: Chapter 1 and thank-you"`.

### Task 8: Low-end and fallback hardening

**Files:**
- Modify: `js/map.js`, `js/site.js`
- Test: `tests/test_home.py` (extend)

- [ ] **Step 1: Write the failing test** `test_map_has_static_fallback_hooks`: `js/map.js` references `deviceMemory`, `prefers-reduced-motion` and a frame-time threshold of `34`.
- [ ] **Step 2: Manual checks**, each recorded with a screenshot:
  - Kit forms with DevTools offline: the fallback post fires, and you land on Kit's page on reconnect.
  - Reduced motion emulated with the initScript method from 1 October.
  - JS disabled: the homepage shows the static campaign plus the chapter list.
- [ ] **Step 3: Commit:** `git commit -m "Redesign: fallbacks verified"`.

### Task 9: Vercel preview and integration tests (target 9 Oct)

**Files:**
- Create: `vercel.json` (`{"cleanUrls":false,"trailingSlash":false}`, no build command), on the branch only

- [ ] **Step 1:** Deploy with `vercel deploy` from the worktree, as a **preview, never `--prod`**. Create a new Vercel project named `mikaelchew-redesign-preview`, not linked to any domain, with Deployment Protection on. Record the preview URL in PROJECT_HANDOFF.md.
- [ ] **Step 2: Run the integration checks** on the preview, with Mikael present for the first two:

  | Check | What should happen |
  |---|---|
  | A real RM 29.90 FPX purchase by Mikael | The Apps Script creates the bill, payment completes, the thank-you page loads, and the delivery email arrives with the EPUB and PDF. Refund it per the refund policy if Mikael wants. |
  | One test submission to each Kit form and tag | The subscriber appears in Kit with the right tag. |
  | A Formspree test message | It arrives. |
  | A GA4 DebugView session | All 8 events fire with their parameters. |
  | WhatsApp links | They open with the right prefilled text. |
- [ ] **Step 3:** Mikael checks the preview on his own phone. Collect his notes as a fix list. Fixes go into a batch inside Task 13.
- [ ] **Step 4: Commit:** `git commit -m "Redesign: Vercel preview and integration log"`. Record the results in `docs/superpowers/plans/2026-10-01-integration-log.md`.

### Task 10: Inner pages

**Files:**
- Modify: `about.html`, `speaking.html`, `work-with-me.html`, `concepts.html`, `contact.html`
- Test: `tests/test_inner.py`

- [ ] **Step 1: Write the failing tests:**
  - `test_inner_use_shell`: each page has the shell markers and none still links `css/style.css`.
  - `test_contact_formspree`: `contact.html` has a `form[data-ajax][action="https://formspree.io/f/xreojdqa"]`.
  - `test_about_timeline_facts`: about.html mentions 2003 and 2009, and does not mention 2016 or 2018 as a field period.
  - `test_no_invented_outcomes`: work-with-me.html has no `%`, "income" or "results guaranteed" outside the existing quoted testimonials.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Rebuild each page to spec §6.4 from the shared components, carrying the existing copy over with its `data-zh`. The case-study section on Work With Me appears only if Mikael has supplied cases (spec §13 item 4).
- [ ] **Step 4:** Run `./build_all.sh` and the tests (expected: PASS), then screenshots at 1440 and 375 per page, plus the detector.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: inner pages"`.

### Task 11: Writing (blog index and 25 posts)

**Files:**
- Create: `tools/retemplate_posts.py`
- Modify: `blog.html`, `blog/*.html` (25 files)
- Test: `tests/test_blog.py`

**Interfaces:**
- `tools/retemplate_posts.py`, `retemplate(path: str) -> str`, keeps:
  - the `<head>` meta, canonical, hreflang and JSON-LD;
  - the `article` content nodes and their `data-en`/`data-zh` pairs.

  It replaces the page chrome with the shell markers and the `.prose` layout.

- [ ] **Step 1: Write the failing tests:**
  - `test_post_text_unchanged`: for each post, the normalised text of the article body is identical to `git show main:blog/<post>`.
  - `test_post_meta_unchanged`: title, description, canonical and JSON-LD are unchanged.
  - `test_blog_filter_events`: `blog.html` keeps `.blog-filter[data-filter]` and the show-more button.
- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement the retemplate script, run it over the 25 posts, and rebuild `blog.html` as the dispatch index.
- [ ] **Step 4:** Run `./build_all.sh` and the tests (expected: PASS), then screenshots of 3 posts at 375, plus the detector on `blog/`.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: writing"`.

### Task 12: Legal pages, 404, scorecard; retire the old system

**Files:**
- Modify: `privacy.html`, `refund-policy.html`, `404.html`, `scorecard.html`
- Delete: `css/style.css`, `js/main.js`, `vendor/fontawesome/`, `vendor/fonts/{inter,playfair}-*.woff2`, `vendor/fonts/fonts.css`. Delete only once the test below proves nothing references them.
- Test: `tests/test_retired.py`

- [ ] **Step 1: Write the failing test** `test_nothing_references_old_assets`: no EN or ZH page references `style.css`, `main.js`, `fontawesome`, `fonts.css`, `fa-` classes, `.fade-in`, or `data-theme`.
- [ ] **Step 2:** Run it. Expected: FAIL.
- [ ] **Step 3:** Rebuild the four pages. Keep `scorecard.html` in `build_zh.py`'s `SKIP` set and keep it unlisted. Then delete the old assets.
- [ ] **Step 4:** Run `./build_all.sh` and the whole suite: `/usr/bin/python3 -m unittest discover -s tests -v`. Expected: all PASS.
- [ ] **Step 5: Commit:** `git commit -m "Redesign: legal pages; retire old CSS/JS/icons"`.

### Task 13: Finish review, DESIGN.md, sign-off (target 16 Oct)

- [ ] **Step 1:** Proofread all book facts against `BOOK_FACTS_ALIGNMENT.md` and the manuscript (`Manuscript_v1.9_TYPESET_READY.docx`, in the book project), and fix anything that's wrong.
- [ ] **Step 2:** Batch Mikael's Task 9 fix list into one round, and redeploy the preview.
- [ ] **Step 3:** Capture `.impeccable/review/desktop.png` and `mobile.png` for the homepage and book page. Run `npx impeccable detect --json` over every changed page.
- [ ] **Step 4:** Spawn the `impeccable-finish-reviewer` with:
  - the spec;
  - the direction contract (the HTML comment from the prototype);
  - the screenshots;
  - the detector output.

  Act on the disposition, within the two-round ceiling.
- [ ] **Step 5:** Spawn the `impeccable-documenter` to write `DESIGN.md` from the built site.
- [ ] **Step 6:** Update `AGENTS.md`, `CLAUDE.md` key paths and `PROJECT_HANDOFF.md` with:
  - the new generators, the `./build_all.sh` run order, the launch flag, and the Vercel preview project;
  - the fontTools install;
  - removing the old "toggle" and "theme" notes.
- [ ] **Step 7:** Mikael signs off on the preview, desktop and phone. Record the sign-off in the integration log.
- [ ] **Step 8: Commit:** `git commit -m "Redesign: finish review, DESIGN.md, docs"`.

### Task 14: Merge and go live (17 Oct), then the launch switch (20 Oct)

- [ ] **Step 1:** Run `sync_with_base_branch`, which brings in content edits made on `main` since 1 October. Re-run `./build_all.sh` and the full suite: all PASS.
- [ ] **Step 2: With Mikael's explicit OK**, merge to `main` and push (this publishes). Then check live, at 1440 and 375: the homepage, book page, Chapter 1, one post, and `/zh/`. Run one live DevTools trace.
- [ ] **Step 3: Rehearse the switch** on the preview, not live:
  - set `data/site.json` phase to `launched`, run `./build_all.sh`, and deploy the preview;
  - check that Buy shows and the launch lists hide, in EN and ZH;
  - revert.
- [ ] **Step 4: On 20 October, with Mikael's OK:**
  - fill in the Amazon URL;
  - set `"phase":"launched"`;
  - run `./build_all.sh` and the suite;
  - commit, push, and check live.
