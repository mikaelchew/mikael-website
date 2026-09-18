# Book delivery — Billplz → Apps Script → buyer's inbox

How a direct sale of 《直銷孫子兵法之不戰而勝》 actually works, and how to switch it on.

## The flow

```
book.html "Buy Now"
   → Billplz collection page   (buyer enters name + email, pays by FPX / e-wallet / card)
       → Billplz CALLBACK  ──► Apps Script doPost
       │                        1. sanity-check X-Signature
       │                        2. re-fetch the bill from the Billplz API  ← the real check
       │                        3. skip if this bill was already delivered
       │                        4. email EPUB + PDF as attachments
       │                        5. append a row to the orders Sheet
       └─ Billplz REDIRECT ──► book-thank-you.html  ("check your inbox")
```

Two separate things arrive from Billplz. The **callback** is server-to-server and is what
delivers the book. The **redirect** just sends the buyer to a page — it is cosmetic and is
never trusted, because anyone can type that URL.

Why the site itself has no payment code: mikaelchew.com is static on GitHub Pages and cannot
run server-side logic or keep a secret. Apps Script is already this project's backend (same
pattern as `scorecard-setup/`), so the API key lives in Script Properties and never in the repo.

## One-time setup

**1. Put the two files in Drive.** Upload from the book project's `publishing/` folder:
`直銷孫子兵法之不戰而勝_ebook.epub` and `Manuscript_v1.9_EBOOK_EDITION.pdf`. Open each,
copy the file id out of the URL (`/d/<FILE_ID>/`).

**2. Create the orders Sheet.** A blank Google Sheet. Copy its id from the URL.

**3. Create the Apps Script project.** script.google.com → New project → paste
`apps-script.gs` → name it `book-delivery`.

**4. Add Script Properties** (Project Settings → Script Properties):

| Property | Value |
|---|---|
| `BILLPLZ_API_KEY` | Billplz → Settings → Account → secret key |
| `BILLPLZ_XSIGN` | Billplz → Settings → X Signature Key |
| `BILLPLZ_SANDBOX` | `true` while testing, `false` when live |
| `ORDERS_SHEET_ID` | from step 2 |
| `EPUB_FILE_ID` / `PDF_FILE_ID` | from step 1 |
| `REPLY_TO` | hello@mikaelchew.com |
| `ADMIN_EMAIL` | where failure alerts go |
| `RESEND_TOKEN` | any long random string |

**5. Run `setupSheet` once** from the editor (writes the header row, and triggers the
permission prompts — accept them).

**6. Run `testDelivery` once.** It emails you the book with no payment involved. If the
attachments arrive and look right, delivery works.

**7. Deploy → New deployment → Web app**, Execute as **Me**, Who has access
**Anyone**. Copy the `/exec` URL. ("Anyone" is required — Billplz's servers are
anonymous. The endpoint gives nothing away: it only accepts a bill id and checks it
against Billplz.)

**8. Create the Billplz collection.** Billplz → Billing → Open Collection:

- Title: 直銷孫子兵法之不戰而勝（電子書）
- Amount: **RM 29.90**, fixed
- Ask for name and email (the email is where the book goes — make it required)
- **Callback URL**: the `/exec` URL from step 7
- **Redirect URL**: `https://www.mikaelchew.com/book-thank-you.html`

Copy the public collection URL.

**9. Put the URL on the site.** In `book.html`, replace `#BILLPLZ_COLLECTION_URL_PENDING`
with the collection URL, delete the `hidden` attribute on `<section class="section book-buy">`,
then run `/usr/bin/python3 build_zh.py` and commit.

## Before you take real money

- Run one **sandbox** purchase end to end (`BILLPLZ_SANDBOX=true`, sandbox keys).
- Then one **real RM 29.90 purchase to yourself** on the live keys. Check: the book arrives,
  the Sheet row says `delivered`, and the statement shows *Ignite Ventures*.
- Refund yourself from the Billplz dashboard afterwards if you want the money back.

## Things that will bite

- **Gmail send quota.** Apps Script sends ~100 emails/day on a consumer Gmail account,
  ~1,500/day on Workspace. A launch-day spike past the cap silently fails delivery. Check
  `?ping=1` on the web-app URL to see the remaining quota; if you expect a big day, use a
  Workspace account.
- **Editing the script does not redeploy it.** Apps Script serves the *deployed* version —
  after changing code, Deploy → Manage deployments → edit → New version.
- **Attachment size.** EPUB + PDF is ~1.2 MB, well under Gmail's 25 MB limit. If the PDF is
  ever replaced with a typeset print-quality file, re-check this.
- **Bill id is the idempotency key.** The script refuses to deliver the same bill twice, so
  Billplz's callback retries are safe.
- **If a buyer says nothing arrived:** check the Sheet first. If the row says `delivered`,
  it is a spam-folder problem. If there is no row, re-send by hand:
  `<exec-url>?resend=<bill_id>&token=<RESEND_TOKEN>`

## Files

| File | What it is |
|---|---|
| `book-delivery/apps-script.gs` | the web app — paste into script.google.com |
| `book-thank-you.html` | Billplz redirect lands here (noindex) |
| `book.html` → `<section class="book-buy">` | the buy cards, currently `hidden` |
