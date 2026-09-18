# Book delivery — Billplz → Apps Script → buyer's inbox

How a direct sale of 《直銷孫子兵法之不戰而勝》 works, and how to switch it on.
Written 2026-09-18 after inspecting the live Billplz dashboard for IGNITE VENTURES.

## Why it is built this way

Billplz's `callback_url` — the thing that tells us a payment succeeded — is a parameter
on **`POST /v3/bills`** and is **required** there. It cannot be set on a Collection: the
Collection menu in the dashboard offers only Payment Method, Split Rule, Collaborator and
Stop collection, and `POST /v3/collections` takes no callback or redirect parameter.

So there is no "static payment link" that can tell us who paid. Every purchase gets its
own bill, created through the API at the moment the buyer clicks Buy. That is why the buy
card asks for name and email first — the API needs both, and the email is where the book
goes.

(Billplz has also moved its old Payment Form feature to a separate product, **Catalog**
(catalog.billplz.com). Catalog is a hosted storefront; it is not used here, because the
v3 API gives us delivery control that a hosted form does not.)

## The flow

```
book.html buy form  (name + email)
   → GET  Apps Script ?action=buy
       → POST /v3/bills  (amount, callback_url = this script, redirect_url = thank-you page)
       → browser redirected to the Billplz payment page  (FPX / e-wallet / card)
           → Billplz CALLBACK ──► Apps Script doPost
           │                       1. sanity-check X-Signature
           │                       2. re-fetch the bill from the API   ← the real check
           │                       3. skip if this bill already delivered
           │                       4. email EPUB + PDF
           │                       5. append row to the orders Sheet
           └─ Billplz REDIRECT ──► book-thank-you.html
```

The **callback** delivers the book. The **redirect** only moves the buyer to a page and is
never trusted — anyone can type that URL.

The site itself holds no secret: mikaelchew.com is static on GitHub Pages. Apps Script is
already this project's backend (same pattern as `scorecard-setup/`), so credentials live in
Script Properties.

## Account state (verified 2026-09-18)

| | |
|---|---|
| Merchant | IGNITE VENTURES (Organization) |
| Bank details | Verified |
| Payment gateway | Configured |
| Existing collection | `IGNITE VENTURES SHOP | CATALOG` — **Collection ID `kd1zdpfg`** |
| Account active until | 17/09/27 |
| **Credit balance** | **RM 3.30 — top this up before launch** |

**Credit balance matters.** Billplz deducts its per-transaction fee from a prepaid credit
balance. At RM 3.30 that covers only a handful of sales before the balance goes negative.
Either self-reload (minimum RM 2, from the Billplz console) or opt into auto-reload, which
offsets a negative balance from daily collections. Top up before you announce the book.

## One-time setup

**1. Put the two files in Drive.** From the book project's `publishing/` folder:
`直銷孫子兵法之不戰而勝_ebook.epub` and `Manuscript_v1.9_EBOOK_EDITION.pdf`. Open each and
copy the id out of the URL (`/d/<FILE_ID>/`). Put them in their own folder, e.g. *Book delivery*.

Why Drive and not the repo: GitHub Pages serves everything publicly, so a paid file in the
site repo would be a free download for anyone who found the URL. (That is exactly why the
free Chapter 1 sample *does* live there.)

**Updating the book later — read this before you regenerate anything.** `publishing/` is the
source of truth; Drive is a copy, and a stale copy means buyers get the wrong edition with no
error anywhere. When a new build exists (adding the eISBN, a v2.0 with errata):

> right-click the existing Drive file → **Manage versions → Upload new version**

That keeps the same file id, so no Script Property changes and nothing to redeploy. Never
upload the new build as a *new* file unless you also update `EPUB_FILE_ID` / `PDF_FILE_ID`.
Record the two file ids in the book project's `REVISIONS.md` so a future session knows where
they point.

**2. Create the orders Sheet.** A blank Google Sheet; copy its id from the URL.

**3. Create the Apps Script project.** script.google.com → New project → paste
`apps-script.gs` → name it `book-delivery`.

**4. Add Script Properties** (Project Settings → Script Properties). Get the two keys from
Billplz → **Settings → Keys & Integration**:

| Property | Value |
|---|---|
| `BILLPLZ_API_KEY` | the API Key from Keys & Integration |
| `BILLPLZ_XSIGN` | the XSignature Key from the same page |
| `BILLPLZ_SANDBOX` | `true` while testing, `false` when live |
| `BILLPLZ_COLLECTION_ID` | `kd1zdpfg` (or a new collection you create) |
| `PRICE_CENTS` | `2990` |
| `REDIRECT_URL` | `https://www.mikaelchew.com/book-thank-you.html` |
| `ORDERS_SHEET_ID` | from step 2 |
| `EPUB_FILE_ID` / `PDF_FILE_ID` | from step 1 |
| `REPLY_TO` | hello@mikaelchew.com |
| `ADMIN_EMAIL` | where failure alerts go |
| `RESEND_TOKEN` | any long random string |

**5. Run `setupSheet` once** from the editor — writes the header row and triggers the
permission prompts. Accept them.

**6. Run `testDelivery` once.** Emails you the book with no payment involved. If the
attachments arrive intact, delivery works.

**7. Deploy → New deployment → Web app.** Execute as **Me**; Who has access **Anyone**.
Copy the `/exec` URL. ("Anyone" is required — Billplz's servers are anonymous. The endpoint
gives nothing away: it only accepts a bill id and re-checks it against Billplz.)

**8. Wire the site.** In `book.html`, replace `#APPS_SCRIPT_EXEC_URL_PENDING` in the buy
form's `action` with that `/exec` URL. Replace `#AMAZON_URL_PENDING` with the Amazon
product URL when it exists. Then delete the `hidden` attribute on
`<section class="section book-buy">`, run `/usr/bin/python3 build_zh.py`, commit and push.

Note: no callback or redirect URL is configured in the Billplz dashboard. The script sends
both with every bill it creates.

## Before you take real money

1. **Sandbox.** billplz-sandbox.com is a separate site with its own login and keys. Set
   `BILLPLZ_SANDBOX=true`, use the sandbox keys and a sandbox collection id, and run a full
   purchase. Confirm: the book arrives, the Sheet row says `delivered`.
2. **One real RM 29.90 purchase to yourself** on live keys. Confirm the same, plus that your
   statement shows *Ignite Ventures*. Refund it from the dashboard afterwards.
3. Only then remove `hidden` from the buy section.

## Things that will bite

- **Gmail send quota.** Apps Script sends ~100 emails/day on consumer Gmail, ~1,500/day on
  Workspace. A launch-day spike past the cap fails silently. `<exec-url>?ping=1` reports the
  remaining quota.
- **Editing the script does not redeploy it.** Apps Script serves the *deployed* version —
  after changing code: Deploy → Manage deployments → edit → New version.
- **Credit balance** (above) — the quiet way sales stop working.
- **Attachment size.** EPUB + PDF is ~1.2 MB, well under the 25 MB limit. Re-check if the PDF
  is ever swapped for a print-quality file.
- **Bill id is the idempotency key**, so Billplz's callback retries cannot double-send.
- **If a buyer says nothing arrived:** check the Sheet. Row says `delivered` → spam folder.
  No row → resend by hand: `<exec-url>?resend=<bill_id>&token=<RESEND_TOKEN>`

## Files

| File | What it is |
|---|---|
| `book-delivery/apps-script.gs` | the web app — paste into script.google.com |
| `book-thank-you.html` | Billplz redirect target (noindex) |
| `book.html` → `<section class="book-buy">` | buy cards + form, currently `hidden` |
