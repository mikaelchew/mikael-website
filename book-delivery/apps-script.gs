/**
 * Book delivery — Billplz callback → email the ebook.
 *
 * Deployed as a Google Apps Script Web App. Billplz POSTs here when a bill is
 * paid; this script confirms the payment with Billplz directly, logs the order
 * to a Sheet, and emails the buyer the EPUB + PDF as attachments.
 *
 * SECURITY NOTE — why the callback body is not trusted:
 * anyone can POST to a public web-app URL. The X-Signature check below is a
 * first filter, but the AUTHORITATIVE check is re-fetching the bill from the
 * Billplz API with our secret key and reading `paid` from that response. A
 * forged callback fails there, because we never take the caller's word for it.
 *
 * All config lives in Script Properties (Project Settings → Script Properties),
 * never in this file — the site repo must stay free of secrets.
 *
 *   BILLPLZ_API_KEY    Billplz secret API key (Billplz → Settings → Account)
 *   BILLPLZ_XSIGN      Billplz X Signature Key (optional but recommended)
 *   BILLPLZ_SANDBOX    "true" while testing, "false" or unset for live
 *   ORDERS_SHEET_ID    Google Sheet that records orders
 *   EPUB_FILE_ID       Drive file id of the EPUB
 *   PDF_FILE_ID        Drive file id of the PDF
 *   REPLY_TO           e.g. hello@mikaelchew.com
 *   ADMIN_EMAIL        where failure alerts go
 *   RESEND_TOKEN       random string; lets you re-send a copy by hand
 *   BILLPLZ_COLLECTION_ID  the collection bills are created under (e.g. kd1zdpfg)
 *   PRICE_CENTS        price in cents — 2990 for RM 29.90
 *   REDIRECT_URL       https://www.mikaelchew.com/book-thank-you.html
 */

function prop_(k, dflt) {
  var v = PropertiesService.getScriptProperties().getProperty(k);
  return (v === null || v === '') ? dflt : v;
}

function apiBase_() {
  return prop_('BILLPLZ_SANDBOX', 'false') === 'true'
    ? 'https://www.billplz-sandbox.com/api/v3'
    : 'https://www.billplz.com/api/v3';
}

/** Billplz signs callbacks: sort keys, join "key"+"value" with "|", HMAC-SHA256. */
function signatureValid_(params) {
  var key = prop_('BILLPLZ_XSIGN', '');
  if (!key) return null;                    // not configured — skip; API check still applies
  var given = params.x_signature;
  if (!given) return false;
  var source = Object.keys(params)
    .filter(function (k) { return k !== 'x_signature'; })
    .sort()
    .map(function (k) { return k + params[k]; })
    .join('|');
  var mac = Utilities.computeHmacSha256Signature(source, key);
  var hex = mac.map(function (b) {
    return ('0' + (b & 0xff).toString(16)).slice(-2);
  }).join('');
  return hex === given;
}

/** Authoritative: ask Billplz what it thinks of this bill. */
function fetchBill_(billId) {
  var res = UrlFetchApp.fetch(apiBase_() + '/bills/' + encodeURIComponent(billId), {
    method: 'get',
    headers: {
      Authorization: 'Basic ' + Utilities.base64Encode(prop_('BILLPLZ_API_KEY', '') + ':')
    },
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) {
    throw new Error('Billplz API ' + res.getResponseCode() + ': ' + res.getContentText());
  }
  return JSON.parse(res.getContentText());
}

function sheet_() {
  return SpreadsheetApp.openById(prop_('ORDERS_SHEET_ID', '')).getSheets()[0];
}

/** Idempotency: Billplz retries callbacks, so never deliver the same bill twice. */
function alreadyDelivered_(billId) {
  var values = sheet_().getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][1]) === String(billId) && String(values[i][6]) === 'delivered') return true;
  }
  return false;
}

function logOrder_(bill, status, note) {
  sheet_().appendRow([
    Utilities.formatDate(new Date(), 'Asia/Kuala_Lumpur', 'yyyy-MM-dd HH:mm:ss'), bill.id, bill.name || '', bill.email || '',
    (Number(bill.amount) / 100).toFixed(2), bill.state || '', status, note || ''
  ]);
}

function sendBook_(toEmail, toName) {
  var epub = DriveApp.getFileById(prop_('EPUB_FILE_ID', '')).getBlob();
  var pdf  = DriveApp.getFileById(prop_('PDF_FILE_ID', '')).getBlob();
  var name = toName || '';

  var html =
    '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.75;color:#1a1a1a;max-width:560px">' +
    '<p>' + (name ? name + '，' : '') + '謝謝你購買《直銷孫子兵法之不戰而勝》。</p>' +
    '<p>電子書就附在這封信裡，兩種格式都有：</p>' +
    '<ul><li><b>EPUB</b> — 手機、平板、Kindle App、大部分電子書閱讀器</li>' +
    '<li><b>PDF</b> — 電腦閱讀或列印</li></ul>' +
    '<p>沒有 DRM 限制，你可以在自己的任何裝置上閱讀。</p>' +
    '<p>書裡每一章都從一次真實的失敗開始。如果你不知道從哪裡讀起，翻到〈如何閱讀這本書〉——照你現在的位置選一條路線。</p>' +
    '<p>讀完之後有任何想法，直接回覆這封信，我會看到。</p>' +
    '<p>我們戰場上見。<br>周俊德（Mikael Chew）</p>' +
    '<hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0">' +
    '<p style="font-size:13px;color:#666">Thank you for your purchase. Your copy of <i>直銷孫子兵法之不戰而勝</i> is attached in both EPUB and PDF. No DRM — read it on any device you own. Reply to this email if anything is wrong and I will fix it.</p>' +
    '</div>';

  MailApp.sendEmail({
    to: toEmail,
    subject: '你的電子書：《直銷孫子兵法之不戰而勝》',
    htmlBody: html,
    name: 'Mikael Chew',
    replyTo: prop_('REPLY_TO', ''),
    attachments: [epub, pdf]
  });
}

function alertAdmin_(subject, body) {
  var to = prop_('ADMIN_EMAIL', '');
  if (to) MailApp.sendEmail(to, '[book-delivery] ' + subject, body);
}

/**
 * POST endpoint. Two callers:
 *  - the book.html buy form: fetch() with a text/plain JSON body {action:'buy', name, email}
 *    (text/plain avoids a CORS preflight, and keeps the email out of any URL);
 *  - the Billplz callback: form-encoded, carries the bill id.
 */
function doPost(e) {
  if (e && e.postData && e.postData.type === 'text/plain') {
    var body = {};
    try { body = JSON.parse(e.postData.contents); } catch (err) {}
    if (body.action === 'buy') return handleBuy_(body);
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var p = (e && e.parameter) ? e.parameter : {};
    var billId = p.id;
    if (!billId) return ContentService.createTextOutput('no bill id');

    var sigOk = signatureValid_(p);
    if (sigOk === false) {
      // Log loudly but keep going — the API check below is what actually decides.
      console.warn('X-Signature mismatch for bill ' + billId + '; keys=' + Object.keys(p).sort().join(','));
    }

    var bill = fetchBill_(billId);          // authoritative
    if (bill.paid !== true) {
      logOrder_(bill, 'not-paid', 'state=' + bill.state + '; sig=' + sigOk);
      return ContentService.createTextOutput('OK');
    }
    if (alreadyDelivered_(billId)) {
      return ContentService.createTextOutput('OK (duplicate)');
    }
    if (!bill.email) {
      logOrder_(bill, 'failed', 'no email on bill');
      alertAdmin_('Paid bill with no email: ' + billId, JSON.stringify(bill));
      return ContentService.createTextOutput('OK');
    }

    sendBook_(bill.email, bill.name);
    logOrder_(bill, 'delivered', 'sig=' + sigOk + '; quota_left=' + MailApp.getRemainingDailyQuota());
    return ContentService.createTextOutput('OK');

  } catch (err) {
    console.error(err);
    alertAdmin_('Delivery FAILED', String(err) + ' -- params: ' + JSON.stringify((e && e.parameter) || {}));
    // Non-200 makes Billplz retry, which is what we want for a transient failure.
    throw err;
  } finally {
    lock.releaseLock();
  }
}

/** JSON reply for the buy form. The page itself navigates to `url`. */
function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Create a Billplz bill for one purchase and return its payment URL.
 * callback_url is REQUIRED by the Billplz API and cannot be set on a collection,
 * which is why every purchase gets its own bill created here rather than using a
 * static payment link.
 */
function handleBuy_(p) {
  var email = String(p.email || '').trim();
  var name  = String(p.name  || '').trim() || 'Reader';
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json_({ error: 'bad-email' });
  }
  var exec = ScriptApp.getService().getUrl();
  var res = UrlFetchApp.fetch(apiBase_() + '/bills', {
    method: 'post',
    headers: {
      Authorization: 'Basic ' + Utilities.base64Encode(prop_('BILLPLZ_API_KEY', '') + ':')
    },
    payload: {
      collection_id: prop_('BILLPLZ_COLLECTION_ID', ''),
      email: email,
      name: name,
      amount: prop_('PRICE_CENTS', '2990'),
      callback_url: exec,
      redirect_url: prop_('REDIRECT_URL', ''),
      description: '\u76f4\u92b7\u5b6b\u5b50\u5175\u6cd5\u4e4b\u4e0d\u6230\u800c\u52dd\uff08\u96fb\u5b50\u66f8 EPUB + PDF\uff09'
    },
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) {
    console.error('Bill creation failed: ' + res.getContentText());
    alertAdmin_('Bill creation FAILED', res.getContentText());
    return json_({ error: 'bill-failed' });
  }
  return json_({ url: JSON.parse(res.getContentText()).url });
}

/**
 * GET endpoint.
 *   ?ping=1                                  health check
 *   ?resend=<billId>&token=<RESEND_TOKEN>    re-send a paid order by hand
 */
function doGet(e) {
  var p = (e && e.parameter) ? e.parameter : {};
  if (p.ping) {
    return ContentService.createTextOutput('ok; mail quota left: ' + MailApp.getRemainingDailyQuota());
  }
  if (p.resend) {
    var expected = prop_('RESEND_TOKEN', '');
    if (!expected || p.token !== expected) return ContentService.createTextOutput('denied');
    var bill = fetchBill_(p.resend);
    if (bill.paid !== true) return ContentService.createTextOutput('bill not paid');
    sendBook_(bill.email, bill.name);
    logOrder_(bill, 'delivered', 'manual resend');
    return ContentService.createTextOutput('resent to ' + bill.email);
  }
  return ContentService.createTextOutput('book-delivery');
}

/** Run once from the editor to create the Sheet header row. */
function setupSheet() {
  sheet_().appendRow(['timestamp', 'bill_id', 'name', 'email', 'amount_rm', 'state', 'status', 'note']);
}

/** Run from the editor to send yourself a test copy (no payment involved). */
function testDelivery() {
  sendBook_(Session.getEffectiveUser().getEmail(), 'Test');
}
