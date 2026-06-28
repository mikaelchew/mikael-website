/* =============================================================
   STRATEGIC LEADER SCORECARD — backend (Google Apps Script)
   Writes each submission to a Google Sheet AND pings your Telegram.
   Mirrors the Zinzino-Day registration script + the omegahealth
   telegramSend() you already use.

   SETUP (see SETUP.md for the full walk-through):
     1. Create a Google Sheet. Add a tab named exactly: Scorecard
     2. In that Sheet: Extensions > Apps Script. Paste this whole file.
     3. Fill the 3 CONFIG values below.
     4. Deploy > New deployment > Web app
          - Execute as: Me
          - Who has access: Anyone
        Copy the /exec URL and paste it into scorecard.html (ENDPOINT).
   ============================================================= */

// ---- CONFIG ---------------------------------------------------
var SHEET_NAME = 'Scorecard';

// Telegram (optional — leave as-is to skip the ping; the Sheet still fills).
// 1. Talk to @BotFather, /newbot, save the token.
var TELEGRAM_BOT_TOKEN = 'PASTE_YOUR_BOT_TOKEN_HERE';
// 2. Message your bot once, then open:
//    https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
//    Copy the "chat":{"id": ... } number.
var TELEGRAM_CHAT_ID = 'PASTE_YOUR_CHAT_ID_HERE';
// ---------------------------------------------------------------

var HEADERS = ['Time', 'Name', 'Email', 'Profile', 'Score',
  'Q1 Duplication', 'Q2 First 72h', 'Q3 Leverage', 'Q4 Time', 'Q5 Recruiting',
  'Q6 Retention', 'Q7 Real customers', 'Focus on', 'Page'];

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = getSheet_();

    var answers = data.answers || [];
    var byFront = {};
    answers.forEach(function (a) { byFront[a.front] = a.answer; });

    var row = [
      new Date(),
      data.name || '',
      data.email || '',
      data.profile || '',
      data.score != null ? data.score + ' / 28' : '',
      byFront['Duplication'] || '',
      byFront['The first 72 hours'] || '',
      byFront['Leverage'] || '',
      byFront['Where your time goes'] || '',
      byFront['How you recruit'] || '',
      byFront['Retention'] || '',
      byFront['Real customers'] || '',
      (data.gaps || []).join(', '),
      data.page || ''
    ];
    sheet.appendRow(row);

    telegramSend(
      '🎯 *NEW SCORECARD*\n' +
      '*Name:* ' + (data.name || '?') + '\n' +
      '*Email:* `' + (data.email || '?') + '`\n' +
      '*Profile:* ' + (data.profile || '?') + '  (' + (data.score || '?') + '/28)\n' +
      '*Focus on:* ' + ((data.gaps || []).join(', ') || 'no major gaps')
    );

    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

// Optional health check: visiting the /exec URL in a browser returns a count.
function doGet() {
  var sheet = getSheet_();
  return json_({ ok: true, rows: Math.max(0, sheet.getLastRow() - 1) });
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) { sheet = ss.insertSheet(SHEET_NAME); }
  if (sheet.getLastRow() === 0) { sheet.appendRow(HEADERS); }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function telegramSend(text) {
  if (TELEGRAM_BOT_TOKEN === 'PASTE_YOUR_BOT_TOKEN_HERE') { return; }
  var url = 'https://api.telegram.org/bot' + TELEGRAM_BOT_TOKEN + '/sendMessage';
  try {
    UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: text,
        parse_mode: 'Markdown',
        disable_web_page_preview: true
      }),
      muteHttpExceptions: true
    });
  } catch (err) { /* never block the Sheet write on a Telegram hiccup */ }
}
