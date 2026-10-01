# DESIGN.md — The Strategist's Map

The design system behind mikaelchew.com since the October 2026 redesign. Read this before changing any
page. The full rationale is in `docs/superpowers/specs/2026-10-01-strategist-map-redesign-design.md`;
who the site serves is in `PRODUCT.md`.

## Idea

A strategist's map table. Dark slate "table" with faint contour lines, warm paper for reading, one red for
seals and action, and Chinese set vertically like a Ming-era legend. Sun Tzu is a working framework here,
never decoration: every red mark means something (a status, an action, a station on the route).

## Tokens (`css/site.css` `:root`)

| Token | Value | Use |
|---|---|---|
| `--table` / `--table-deep` | #22303A / #19242C | page background / cards, footer |
| `--acetate` | #F2F2EE | primary text on dark |
| `--mute` / `--contour` | #B9C4C0 / #B6C4BE | secondary text / labels, map lines |
| `--red` / `--red-lit` / `--red-text` | #C0392B / #F0705F / #A93226 | buttons, seals / accents on dark / links on paper |
| `--paper` / `--ink` / `--ink-2` | #F5F0E8 / #1A1A1A / #4A4740 | reading surfaces (posts, Chapter 1, bands) |
| `--line` | rgba(182,196,190,.24) | hairlines on dark |
| `--ease-out` | cubic-bezier(.23,1,.32,1) | everything that enters or settles |
| `--ease-move` | cubic-bezier(.77,0,.175,1) | things that draw across the screen |
| `--sans` | Overpass (self-hosted) + system CJK | all Latin text |
| `--display-zh` | Noto Serif TC Display subset | Chinese display text only (`.cjk-display`) |

Don't add a second red, a gradient, or a new font. Body Chinese uses the system CJK font on purpose (the
display subset only contains characters used in `.cjk-display` text; `build_fonts.py` rebuilds it).

## Components

- **Bar:** brand 周俊德 / MIKAEL CHEW and six bilingual nav items from `partials/header.html` (never hand-edit
  per page; `build_shell.py` injects it). Current page = red underline.
- **Buttons:** `.btn` red fill; `.btn--ghost` acetate outline (ink on paper). Press = `scale(.97)`.
- **Seals:** red chop SVG symbols in the footer sprite (`#seal-launch`, `#seal-live`, `#seal-free`,
  `#seal-sent`). Status only; they stamp once when 60% in view.
- **Recon prints:** halftone photos (`images/print/`, `tools/make_prints.py`) of Mikael's own photographs.
- **Briefing card** (`.brief`): number, English title, Chinese title, one line. Hairline border, no side stripes.
- **Band** (`.band`): paper section with contour lines for next steps and forms.
- **Legend** (`.legend`): vertical Chinese in red on page heads; hidden on phones.
- **Review card** (`.c` in `.c-grid.all`): all eight LinkedIn recommendations, equal size, masonry columns,
  word-for-word from `data/testimonials.json`. Never stars, never trimmed, never invented.
- **Writing card** (`.dispatch .card`): 16:9 picture, category, title, date · read time; newest spans two
  columns. Pictures: stock photos (older posts), map covers (`tools/make_covers.py`, posts tied to the book),
  Gemini images (essay posts). See `images/blog/README.md`.
- **Forms:** one field + button, inline confirmation (`form[data-ajax]` + `.form-ok`).

## Motion (end of `css/site.css`, `initMotion` in `js/site.js`)

Rules, from the Emil Kowalski animation skills this project uses:

- Hover motion only under `@media (hover: hover) and (pointer: fine)`; 150–250ms; transform/opacity/colour.
- Scroll reveals fire once, only for elements **below the first screen** (so nothing above the fold waits
  for JS and LCP is unaffected), and only when JS runs and the user hasn't asked for reduced motion
  (`html.reveals`). Stagger 70ms via `--i`.
- Delight is spent where it's rare: the About timeline draws its route and lands each station in turn;
  halftone prints develop top to bottom; vertical legends ink in on load; figures count up.
- Reading progress on posts and Chapter 1 is CSS scroll-driven (`animation-timeline: scroll()`), with no fallback
  needed.
- `prefers-reduced-motion`: transitions and animations collapse to instant; content is never hidden.

## Bilingual

Every visible string carries `data-en` and `data-zh`; `build_zh.py` writes `/zh/`. Chinese copy never uses
「——」. Pages and posts that exist only in English still get a zh page (same text) so the language link works.

## Pages

| Page | Composition |
|---|---|
| Home | The Map: chapters as stations on a contour route (`js/map.js`), static fallback on low-end devices |
| Book | The Dossier: cover with seal, order box, chapter cards, free Chapter 1, FAQ, buy (after launch) |
| Chapter 1 | Paper reading layout generated from the manuscript |
| About | Story, dated route (2003 · 2009 · 8+15 years · 2026), values, all reviews |
| Speaking / Work With Me / Concepts / Contact | Page head with legend, briefing cards, FAQ, band |
| Writing | Card grid with topic filter, show-more, and date-gated scheduling |
| Posts | Paper reading layout, CTA, prev/next (scheduled links hidden), newsletter |

## Checks before calling UI work done

`./build_all.sh`, the test suite, `npx impeccable detect` (padding false positives on `.sec`, `.band`,
`.dispatch`, `.epigraph` are known and ignored), and a mobile performance trace for any first-screen change
(October 2026 baselines, 4× CPU + Slow 4G: home 0.17s, book 0.91s, About 0.19s, Speaking 0.17s,
Writing 0.18s LCP; CLS 0.00 everywhere).
