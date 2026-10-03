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
 *   EPUB_FILE_ID       Drive file id of the EPUB (Chinese edition)
 *   PDF_FILE_ID        Drive file id of the PDF (Chinese edition)
 *   EPUB_FILE_ID_EN    Drive file id of the English EPUB
 *   PDF_FILE_ID_EN     Drive file id of the English PDF
 *   PRICE_CENTS_EN     English price in cents (defaults to PRICE_CENTS)
 *   REPLY_TO           e.g. hello@mikaelchew.com
 *   ADMIN_EMAIL        where failure alerts go
 *   RESEND_TOKEN       random string; lets you re-send a copy by hand
 *   BILLPLZ_COLLECTION_ID  the collection bills are created under (e.g. kd1zdpfg)
 *   PRICE_CENTS        price in cents — 2990 for RM 29.90
 *   REDIRECT_URL       https://www.mikaelchew.com/book-thank-you.html
 *
 * Two editions share one flow. The buy form sends edition ('zh' or 'en'); the bill
 * carries it in reference_1, and the callback reads it back from the re-fetched
 * bill, so the edition a buyer receives is decided by Billplz's record, not the form.
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

/**
 * Billplz signs callbacks: build "key"+"value" for every param except x_signature,
 * sort those STRINGS (not the keys — "paid_amount100" sorts before "paidtrue"),
 * join with "|", HMAC-SHA256 hex. Matches the source-string order in Billplz's API docs.
 */
function signatureValid_(params) {
  var key = prop_('BILLPLZ_XSIGN', '');
  if (!key) return null;                    // not configured — skip; API check still applies
  var given = params.x_signature;
  if (!given) return false;
  var source = Object.keys(params)
    .filter(function (k) { return k !== 'x_signature'; })
    .map(function (k) { return k + params[k]; })
    .sort()
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

/** Edition of a bill: 'en' only when the bill says so; everything else is the Chinese edition. */
function lang_(bill) {
  return String(bill.reference_1 || '').toLowerCase() === 'en' ? 'en' : 'zh';
}

function logOrder_(bill, status, note) {
  sheet_().appendRow([
    Utilities.formatDate(new Date(), 'Asia/Kuala_Lumpur', 'yyyy-MM-dd HH:mm:ss'), bill.id, bill.name || '', bill.email || '',
    (Number(bill.amount) / 100).toFixed(2), bill.state || '', status, note || '', lang_(bill)
  ]);
}

function sendBook_(toEmail, toName, lang) {
  if (lang === 'en') return sendBookEn_(toEmail, toName);
  var epub = DriveApp.getFileById(prop_('EPUB_FILE_ID', '')).getBlob();
  var pdf  = DriveApp.getFileById(prop_('PDF_FILE_ID', '')).getBlob();
  var name = toName || '';

  var html =
    '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.75;color:#1a1a1a;max-width:560px">' +
    '<p>' + (name ? name + '，' : '') + '謝謝你購買《直銷孫子兵法之不戰而勝》。</p>' +
    '<p>電子書就附在這封信裡，兩種格式都有：</p>' +
    '<ul><li><b>EPUB</b>：在手機和平板上閱讀，建議用這個。它會跟著螢幕自動排版，字可以放大縮小。</li>' +
    '<li><b>PDF</b>：固定版面，適合電腦閱讀或列印。在手機上要一直放大拖動，比較吃力。</li></ul>' +
    '<p><b>怎麼打開 EPUB：</b></p>' +
    '<ul><li><b>iPhone／iPad：</b>在「郵件」或 Gmail App 裡點一下 EPUB 附件，再點分享圖示（方框加向上箭頭），選「書籍」。如果第一排沒有「書籍」，往右滑到「更多」再找。書會放進「書籍」App 的書庫，以後打開「書籍」就能讀，字體大小、背景顏色都可以自己調。</li>' +
    '<li><b>Android：</b>點附件把 EPUB 下載到手機，打開「Google Play 圖書」，到「書庫」，從右上角的選單選擇上傳，再選這個檔案。手機沒有 Google Play 圖書（例如部分華為手機），在應用程式商店裝任何一個免費的 EPUB 閱讀 App 就可以打開。</li>' +
    '<li><b>Kindle（手機 App 或 Kindle 閱讀器）：</b>Kindle 不能直接打開附件。到 amazon.com/sendtokindle，登入你的 Amazon 帳號，上傳 EPUB，幾分鐘後會出現在你所有 Kindle 裝置的書庫。</li>' +
    '<li><b>Kobo 和其他電子書閱讀器（PocketBook、Boox 等）：</b>用 USB 線把閱讀器接上電腦，把 EPUB 複製進閱讀器，拔掉線就會在書庫裡出現。</li>' +
    '<li><b>Mac：</b>按兩下 EPUB，會用「書籍」App 打開。</li>' +
    '<li><b>Windows 電腦：</b>直接打開 PDF 最簡單。想用 EPUB，可以在 Microsoft Store 免費下載「Thorium Reader」。</li></ul>' +
    '<p>打不開或找不到附件，直接回覆這封信，我幫你處理。沒有 DRM 限制，你可以在自己的任何裝置上閱讀。</p>' +
    '<p>書裡每一章都從一個真實的一線故事開始。我建議你從第一章讀到最後一章；如果想先知道重點放在哪裡，翻到〈如何閱讀這本書〉，找到你現在的階段。</p>' +
    '<p>讀完之後有任何想法，直接回覆這封信，我會看到。</p>' +
    '<p>我們戰場上見。<br>周俊德（Mikael Chew）</p>' +
    '<hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0">' +
    '<p style="font-size:13px;color:#666">Thank you for your purchase. Your copy of <i>直銷孫子兵法之不戰而勝</i> is attached in both EPUB and PDF. On a phone, use the EPUB: it reflows to fit your screen. <b>iPhone/iPad:</b> tap the EPUB attachment, tap Share, choose Books (swipe to More if you don&#39;t see it). <b>Android:</b> download it, then in Google Play Books go to Library, open the menu and choose Upload; any free EPUB reader app also works. <b>Kindle app or e-reader:</b> upload it at amazon.com/sendtokindle. <b>Kobo and other e-readers:</b> connect by USB and copy the file across. <b>Mac:</b> double-click to open in Books. <b>Windows:</b> open the PDF, or install the free Thorium Reader for the EPUB. No DRM, so you can read it on any device you own. Reply to this email if anything is wrong and I will fix it.</p>' +
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

function sendBookEn_(toEmail, toName) {
  var epub = DriveApp.getFileById(prop_('EPUB_FILE_ID_EN', '')).getBlob();
  var pdf  = DriveApp.getFileById(prop_('PDF_FILE_ID_EN', '')).getBlob();
  var name = toName || '';

  var html =
    '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;color:#1a1a1a;max-width:560px">' +
    '<p>' + (name ? 'Hi ' + name + ',' : 'Hi,') + '</p>' +
    '<p>Thank you for buying <i>The Art of War for Direct Selling</i>. Your ebook is attached in two formats:</p>' +
    '<ul><li><b>EPUB</b>: best on a phone or tablet. It reflows to fit your screen and you can change the text size.</li>' +
    '<li><b>PDF</b>: a fixed layout, best on a computer or for printing.</li></ul>' +
    '<p><b>How to open the EPUB:</b></p>' +
    '<ul><li><b>iPhone/iPad:</b> tap the EPUB attachment, tap the Share icon and choose Books (swipe to More if you don&#39;t see it).</li>' +
    '<li><b>Android:</b> download the file, open Google Play Books, go to Library, open the menu and choose Upload. Any free EPUB reader app also works.</li>' +
    '<li><b>Kindle app or e-reader:</b> upload the EPUB at amazon.com/sendtokindle and it appears on all your Kindle devices within minutes.</li>' +
    '<li><b>Kobo and other e-readers:</b> connect by USB and copy the file across.</li>' +
    '<li><b>Mac:</b> double-click to open it in Books. <b>Windows:</b> open the PDF, or install the free Thorium Reader for the EPUB.</li></ul>' +
    '<p>There&#39;s no DRM, so you can read it on any device you own. If anything doesn&#39;t open, reply to this email and I&#39;ll sort it out.</p>' +
    '<p>Every chapter starts with a real story from the field. I recommend reading it from start to finish; if you want to know where to focus first, turn to <i>How to Read This Book</i> and find your stage.</p>' +
    '<p>When you&#39;ve read it, reply and tell me what stayed with you. I read every reply.</p>' +
    '<p>See you on the field,<br>Mikael Chew</p>' +
    '</div>';

  MailApp.sendEmail({
    to: toEmail,
    subject: 'Your ebook: The Art of War for Direct Selling',
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

    sendBook_(bill.email, bill.name, lang_(bill));
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
  var lang  = (p.edition || p.lang) === 'en' ? 'en' : 'zh';   // the site sends "edition"
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
      amount: lang === 'en' ? prop_('PRICE_CENTS_EN', prop_('PRICE_CENTS', '2990')) : prop_('PRICE_CENTS', '2990'),
      callback_url: exec,
      redirect_url: prop_('REDIRECT_URL', ''),
      reference_1_label: 'Edition',
      reference_1: lang,
      description: lang === 'en'
        ? 'The Art of War for Direct Selling (ebook, EPUB + PDF)'
        : '\u76f4\u92b7\u5b6b\u5b50\u5175\u6cd5\u4e4b\u4e0d\u6230\u800c\u52dd\uff08\u96fb\u5b50\u66f8 EPUB + PDF\uff09'
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
    sendBook_(bill.email, bill.name, lang_(bill));
    logOrder_(bill, 'delivered', 'manual resend');
    return ContentService.createTextOutput('resent to ' + bill.email);
  }
  return ContentService.createTextOutput('book-delivery');
}

/** Run once from the editor to create the Sheet header row. */
function setupSheet() {
  sheet_().appendRow(['timestamp', 'bill_id', 'name', 'email', 'amount_rm', 'state', 'status', 'note', 'lang']);
}

/** Run from the editor to send yourself a test copy (no payment involved). */
function testDelivery() {
  sendBook_(Session.getEffectiveUser().getEmail(), 'Test', 'zh');
}

/** Run from the editor to send yourself the English test copy. */
function testDeliveryEn() {
  sendBook_(Session.getEffectiveUser().getEmail(), 'Test', 'en');
}
