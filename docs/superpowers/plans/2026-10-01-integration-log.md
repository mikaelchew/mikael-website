# Integration log: Strategist's Map preview

Preview: https://mikaelchew-redesign-preview-inoi7d2wz-mikaelchews-projects.vercel.app
(Vercel project `mikaelchew-redesign-preview`, deployed 2026-10-01 from commit after c5508d0.
Sign in to Vercel as mikaelchew to view it.)

## Deployment

| Check | Result |
|---|---|
| Hashed preview URL needs a Vercel login | Yes: 302 to the Vercel login |
| Short alias `mikaelchew-redesign-preview.vercel.app` | Removed by Mikael 2026-10-01; now 404 |
| mikaelchew.com untouched | Yes. Still GitHub Pages from `main`; no domain on the Vercel project |
| Upload contents | Site files only (`.vercelignore` excludes Markdown, Python, Apps Script sources, docs, tests, tools, the manuscript and `.env*`) |

## Integration checks (pending: need Mikael)

| Check | Expected | Result |
|---|---|---|
| Real RM 29.90 FPX purchase | Bill created, payment completes, thank-you page shows "Payment received", delivery email arrives with EPUB + PDF | **Pass.** Mikael ran two purchases, both successful (reported 2026-10-01); no further purchase needed |
| One test submission per Kit form/tag (book-launch, book-print, book-chapter, long-game-launch, newsletter) | Subscriber appears in Kit with the right tag | pending |
| Formspree test message | Arrives | pending |
| GA4 DebugView | All events fire with parameters (`debug_mode` is on for non-production hosts) | pending |
| WhatsApp links | Open with the right prefilled text | pending |
| Mikael on his own phone | Notes collected as a fix list for Task 13 | pending |

## Checked locally before deploy (Task 8)

- Reduced motion: static map, all 13 chapters visible.
- JavaScript off: homepage shows the static campaign and chapter list; seals visible.
- Kit fetch failure: falls back to a native POST to app.kit.com, with no false success message.
