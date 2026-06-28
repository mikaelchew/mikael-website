# Strategic Leader Scorecard — setup (15 minutes, free)

The page (`scorecard.html`) works in **demo mode** right out of the box — it just
doesn't save anywhere yet. To capture leads into a Google Sheet and get a Telegram
ping, do these three steps. Same pattern as your Zinzino-Day registration site.

---

## 1. The Google Sheet

1. Go to [sheets.new](https://sheets.new) and create a sheet. Name it e.g. **"Scorecard leads"**.
2. Rename the first tab (bottom-left) to exactly: **`Scorecard`**
3. That's it — the script writes the header row automatically on the first submission.

The Sheet *is* your list: name, email, all 7 answers, their profile, the score, and the time.

---

## 2. The Apps Script (the bridge) + your Web App URL

1. In that Sheet: **Extensions → Apps Script**.
2. Delete the placeholder code, paste in the entire contents of **`apps-script.gs`** (next to this file).
3. Click **Deploy → New deployment**.
   - Gear icon → **Web app**
   - **Execute as:** Me
   - **Who has access:** **Anyone**
   - **Deploy**, approve the permissions prompt.
4. Copy the **Web app URL** — it ends in `/exec`.
5. Open **`scorecard.html`**, find this line near the bottom, and paste your URL between the quotes:
   ```js
   var ENDPOINT = "";   // ← paste your /exec URL here
   ```

That alone gets every submission into your Sheet. Telegram is optional (step 3).

> Tip: visiting the `/exec` URL in a browser should return `{"ok":true,"rows":0}` — that confirms it's live.

---

## 3. The Telegram ping (optional)

Same bot mechanism as your omegahealth automation.

1. In Telegram, message **@BotFather** → `/newbot` → follow the prompts. Save the **token** it gives you (looks like `8123456789:AAH...`).
   - Or reuse your existing omegahealth bot's token — your call.
2. Send any message to your new bot (so it can "see" you).
3. Open this in a browser (paste your token in):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id": 123456789` — that number is your **chat ID**.
4. In the Apps Script, fill the two values at the top of `apps-script.gs`:
   ```js
   var TELEGRAM_BOT_TOKEN = 'your-token-here';
   var TELEGRAM_CHAT_ID   = 'your-chat-id-here';
   ```
5. **Deploy → Manage deployments → edit (pencil) → Version: New version → Deploy** to push the update.

Now each submission pings you:
`🎯 NEW SCORECARD — Ahmad, The Busy Operator (12/28). Focus on: Duplication, Retention.`

---

## Notes
- The bot token / chat ID live **only** inside Apps Script (server-side, private) — never in the website. Safe.
- To re-deploy after editing the script, always bump to a **New version** (step 3.5), or the change won't go live.
- No Mailchimp needed. If you ever want automated email sequences too, we can add a Mailchimp call inside `doPost` later.
