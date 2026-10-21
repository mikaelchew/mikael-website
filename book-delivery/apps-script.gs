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
 *   REPLY_TO           e.g. mikael@mikaelchew.com
 *   FROM_EMAIL         send buyer emails as this address, e.g. mikael@mikaelchew.com. It must be a verified
 *                      "Send mail as" alias of the Gmail account that runs this script. Unset = send as the
 *                      account itself (MailApp).
 *   ADMIN_EMAIL        where failure alerts go
 *   RESEND_TOKEN       random string; lets you re-send a copy by hand
 *   BILLPLZ_COLLECTION_ID  the collection bills are created under (e.g. kd1zdpfg)
 *   PRICE_CENTS        price in cents — 2990 for RM 29.90
 *   REDIRECT_URL       https://www.mikaelchew.com/book-thank-you.html
 *   KIT_URL_ZH         link to the Chinese Leader's Training Kit folder (buyer gift; kept out of this public repo)
 *   KIT_URL_EN         link to the English Leader's Training Kit folder
 *
 * The 13-week buyer email course lives in two more files of the same Apps Script project, course.gs and
 * course_content.gs. They are kept in the book repo (publishing/email_course/apps_script/), not here,
 * because this repo is published by GitHub Pages. Without them, the hooks below do nothing.
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

/**
 * The buyer's files as download links (20 Oct 2026: ~12 MB of attachments plus Gmail "send as"
 * sent delivery emails to Hotmail's Junk folder). Links only work once each file is shared
 * "anyone with the link can view" (run shareBuyerFiles() once). If a file isn't shared, the
 * email falls back to attachments and you get an alert, so a buyer is never sent a dead link.
 */
function bookFiles_(epubId, pdfId, billId, lang) {
  var epub = DriveApp.getFileById(epubId), pdf = DriveApp.getFileById(pdfId);
  var shared = [epub, pdf].every(function (f) {
    return f.getSharingAccess() === DriveApp.Access.ANYONE_WITH_LINK;
  });
  if (!shared) {
    alertAdmin_('Buyer files not shared by link: sent as attachments',
      'Run shareBuyerFiles() once in the Apps Script editor so delivery emails carry download links instead of ~12 MB of attachments.');
    return { links: false, attachments: [epub.getBlob(), pdf.getBlob()] };
  }
  var url = function (id) { return 'https://drive.google.com/uc?export=download&id=' + id; };
  // a paid order gets its personal, tracked links; manual sends and tests get the plain Drive links
  if (billId) return { links: true, epub: dlPage_(billId, lang, 'epub'), pdf: dlPage_(billId, lang, 'pdf') };
  return { links: true, epub: url(epubId), pdf: url(pdfId) };
}

/** Run once from the editor: share the four buyer files "anyone with the link can view" and log the links. */
function shareBuyerFiles() {
  ['EPUB_FILE_ID', 'PDF_FILE_ID', 'EPUB_FILE_ID_EN', 'PDF_FILE_ID_EN'].forEach(function (k) {
    var id = prop_(k, '');
    if (!id) return console.log(k + ': not set');
    var f = DriveApp.getFileById(id);
    f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    console.log(k + ': ' + f.getName() + ' -> https://drive.google.com/uc?export=download&id=' + id);
  });
}

/** A download button for the delivery emails. */
function fileButton_(href, label) {
  return '<a href="' + href + '" style="display:inline-block;margin:4px 8px 4px 0;padding:10px 16px;background:#c0392b;color:#fff;' +
    'text-decoration:none;font-weight:700;border-radius:3px">' + label + '</a>';
}

/** billId (optional) makes the download links personal and tracked; manual.gs calls it without one. */
function sendBook_(toEmail, toName, lang, billId) {
  if (lang === 'en') return sendBookEn_(toEmail, toName, billId);
  var files = bookFiles_(prop_('EPUB_FILE_ID', ''), prop_('PDF_FILE_ID', ''), billId, 'zh');
  var name = toName || '';
  var get = files.links
    ? '<p>電子書請用下面兩個按鈕下載，兩種格式都有：</p>' +
      '<p>' + fileButton_(files.epub, '下載 EPUB（手機、平板）') + '<br>' + fileButton_(files.pdf, '下載 PDF（電腦、列印）') + '</p>' +
      '<p style="font-size:13px;color:#666">這兩個連結只供你自己使用，請不要轉傳。</p>'
    : '<p>電子書就附在這封信裡，兩種格式都有：</p>';
  var item = files.links ? '下載連結' : '附件';

  var html =
    '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.75;color:#1a1a1a;max-width:560px">' +
    '<p>' + (name ? name + '，' : '') + '謝謝你購買《直銷孫子兵法之不戰而勝》。</p>' +
    get +
    '<ul><li><b>EPUB</b>：在手機和平板上閱讀，建議用這個。它會跟著螢幕自動排版，字可以放大縮小。</li>' +
    '<li><b>PDF</b>：固定版面，適合電腦閱讀或列印。在手機上要一直放大拖動，比較吃力。</li></ul>' +
    '<p><b>怎麼打開 EPUB：</b></p>' +
    '<ul><li><b>iPhone／iPad：</b>' + (files.links ? '點「下載 EPUB」，下載完成後點檔案，再點分享圖示（方框加向上箭頭），選「書籍」。' : '在「郵件」或 Gmail App 裡點一下 EPUB 附件，再點分享圖示（方框加向上箭頭），選「書籍」。') + '如果第一排沒有「書籍」，往右滑到「更多」再找。書會放進「書籍」App 的書庫，以後打開「書籍」就能讀，字體大小、背景顏色都可以自己調。</li>' +
    '<li><b>Android：</b>' + (files.links ? '點「下載 EPUB」把檔案下載到手機，' : '點附件把 EPUB 下載到手機，') + '打開「Google Play 圖書」，到「書庫」，從右上角的選單選擇上傳，再選這個檔案。手機沒有 Google Play 圖書（例如部分華為手機），在應用程式商店裝任何一個免費的 EPUB 閱讀 App 就可以打開。</li>' +
    '<li><b>Kindle（手機 App 或 Kindle 閱讀器）：</b>Kindle 不能直接打開' + item + '。先把 EPUB 下載到手機或電腦，再到 amazon.com/sendtokindle，登入你的 Amazon 帳號，上傳 EPUB，幾分鐘後會出現在你所有 Kindle 裝置的書庫。</li>' +
    '<li><b>Kobo 和其他電子書閱讀器（PocketBook、Boox 等）：</b>用 USB 線把閱讀器接上電腦，把 EPUB 複製進閱讀器，拔掉線就會在書庫裡出現。</li>' +
    '<li><b>Mac：</b>按兩下 EPUB，會用「書籍」App 打開。</li>' +
    '<li><b>Windows 電腦：</b>直接打開 PDF 最簡單。想用 EPUB，可以在 Microsoft Store 免費下載「Thorium Reader」。</li></ul>' +
    '<p>下載不了、打不開或找不到' + item + '，直接回覆這封信，我幫你處理。沒有 DRM 限制，你可以在自己的任何裝置上閱讀。</p>' +
    '<p>書裡每一章都從一個真實的一線故事開始。我建議你從第一章讀到最後一章；如果想先知道重點放在哪裡，翻到〈如何閱讀這本書〉，找到你現在的階段。</p>' +
    giftsZh_() +
    '<p>讀完之後有任何想法，直接回覆這封信，我會看到。</p>' +
    '<p>我們戰場上見。<br>周俊德（Mikael Chew）</p>' +
    '<hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0">' +
    '<p style="font-size:13px;color:#666">Thank you for your purchase. Your copy of <i>直銷孫子兵法之不戰而勝</i> ' + (files.links ? 'can be downloaded with the two buttons above, in EPUB and PDF (the links are for your own use)' : 'is attached in both EPUB and PDF') + '. On a phone, use the EPUB: it reflows to fit your screen. <b>iPhone/iPad:</b> ' + (files.links ? 'tap the EPUB button, tap the downloaded file, tap Share' : 'tap the EPUB attachment, tap Share') + ', choose Books (swipe to More if you don&#39;t see it). <b>Android:</b> download it, then in Google Play Books go to Library, open the menu and choose Upload; any free EPUB reader app also works. <b>Kindle app or e-reader:</b> upload it at amazon.com/sendtokindle. <b>Kobo and other e-readers:</b> connect by USB and copy the file across. <b>Mac:</b> double-click to open in Books. <b>Windows:</b> open the PDF, or install the free Thorium Reader for the EPUB. No DRM, so you can read it on any device you own. Reply to this email if anything is wrong and I will fix it.</p>' +
    '</div>';

  send_({
    to: toEmail,
    subject: '你的電子書：《直銷孫子兵法之不戰而勝》',
    htmlBody: html,
    name: 'Mikael Chew',
    replyTo: prop_('REPLY_TO', ''),
    attachments: files.attachments
  });
}

function sendBookEn_(toEmail, toName, billId) {
  var files = bookFiles_(prop_('EPUB_FILE_ID_EN', ''), prop_('PDF_FILE_ID_EN', ''), billId, 'en');
  var name = toName || '';
  var get = files.links
    ? '<p>Thank you for buying <i>The Art of War for Direct Selling</i>. Download your ebook in either format:</p>' +
      '<p>' + fileButton_(files.epub, 'Download EPUB (phone, tablet)') + '<br>' + fileButton_(files.pdf, 'Download PDF (computer, print)') + '</p>' +
      '<p style="font-size:13px;color:#666">These links are for your own use; please don&#39;t share them.</p>'
    : '<p>Thank you for buying <i>The Art of War for Direct Selling</i>. Your ebook is attached in two formats:</p>';

  var html =
    '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;color:#1a1a1a;max-width:560px">' +
    '<p>' + (name ? 'Hi ' + name + ',' : 'Hi,') + '</p>' +
    get +
    '<ul><li><b>EPUB</b>: best on a phone or tablet. It reflows to fit your screen and you can change the text size.</li>' +
    '<li><b>PDF</b>: a fixed layout, best on a computer or for printing.</li></ul>' +
    '<p><b>How to open the EPUB:</b></p>' +
    '<ul><li><b>iPhone/iPad:</b> ' + (files.links ? 'tap Download EPUB, tap the downloaded file, then tap the Share icon' : 'tap the EPUB attachment, tap the Share icon') + ' and choose Books (swipe to More if you don&#39;t see it).</li>' +
    '<li><b>Android:</b> download the file, open Google Play Books, go to Library, open the menu and choose Upload. Any free EPUB reader app also works.</li>' +
    '<li><b>Kindle app or e-reader:</b> download the EPUB, then upload it at amazon.com/sendtokindle and it appears on all your Kindle devices within minutes.</li>' +
    '<li><b>Kobo and other e-readers:</b> connect by USB and copy the file across.</li>' +
    '<li><b>Mac:</b> double-click to open it in Books. <b>Windows:</b> open the PDF, or install the free Thorium Reader for the EPUB.</li></ul>' +
    '<p>There&#39;s no DRM, so you can read it on any device you own. If anything doesn&#39;t download or open, reply to this email and I&#39;ll sort it out.</p>' +
    '<p>Every chapter starts with a real story from the field. I recommend reading it from start to finish; if you want to know where to focus first, turn to <i>How to Read This Book</i> and find your stage.</p>' +
    giftsEn_() +
    '<p>When you&#39;ve read it, reply and tell me what stayed with you. I read every reply.</p>' +
    '<p>See you on the field,<br>Mikael Chew</p>' +
    '</div>';

  send_({
    to: toEmail,
    subject: 'Your ebook: The Art of War for Direct Selling',
    htmlBody: html,
    name: 'Mikael Chew',
    replyTo: prop_('REPLY_TO', ''),
    attachments: files.attachments
  });
}

/** Buyer-gift paragraph for the delivery emails. Empty until the course and kit links are set up. */
function giftsZh_() {
  var kit = prop_('KIT_URL_ZH', '');
  var course = typeof enrollCourse_ === 'function';
  if (!kit && !course) return '';
  return '<p><b>讀者禮物：</b>' +
    (course ? '從明天開始，接下來十三個星期，我每週寄一封實戰信給你，一章一個行動。' : '') +
    (kit ? '如果你在帶團隊，四份帶領者教材（投影片、講者備註、現場練習）在這裡：<a href="' + kit + '">帶領者教材</a>。' : '') +
    '</p>';
}

function giftsEn_() {
  var kit = prop_('KIT_URL_EN', '');
  var course = typeof enrollCourse_ === 'function';
  if (!kit && !course) return '';
  return '<p><b>Your reader gifts:</b> ' +
    (course ? 'starting tomorrow, I&#39;ll send you one email a week for thirteen weeks, one chapter and one action at a time. ' : '') +
    (kit ? 'If you lead a team, the four Leader&#39;s Training Kit decks (slides, speaker notes, exercises) are here: <a href="' + kit + '">Leader&#39;s Training Kit</a>.' : '') +
    '</p>';
}

/**
 * Send a buyer email. With FROM_EMAIL set, GmailApp sends it from that alias (MailApp cannot send from an
 * alias). If that fails, fall back to MailApp so the buyer still gets it, and alert. Both count against the
 * same daily Gmail recipient quota, which MailApp.getRemainingDailyQuota() reports.
 */
function send_(o) {
  var from = prop_('FROM_EMAIL', '');
  if (from) {
    var plain = String(o.htmlBody || '')
      .replace(/<li>/gi, '- ').replace(/<br\s*\/?>|<\/li>/gi, '\n').replace(/<\/p>|<\/ul>|<\/ol>/gi, '\n\n')
      .replace(/<a [^>]*href="([^"]+)"[^>]*>([^<]*)<\/a>/gi, '$2 ($1)').replace(/<[^>]+>/g, '')
      .replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
    var opts = { from: from, name: o.name, htmlBody: o.htmlBody };
    if (o.replyTo) opts.replyTo = o.replyTo;
    if (o.attachments) opts.attachments = o.attachments;
    try {
      GmailApp.sendEmail(o.to, o.subject, plain, opts);
      return;
    } catch (err) {
      alertAdmin_('Sending as ' + from + ' failed; sent from the account address instead', String(err));
    }
  }
  MailApp.sendEmail(o);
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
    if (body.action === 'resend') return handleResend_(body);
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

    sendBook_(bill.email, bill.name, lang_(bill), bill.id);
    logOrder_(bill, 'delivered', 'sig=' + sigOk + '; quota_left=' + MailApp.getRemainingDailyQuota());
    // The book is out; a course problem must not make Billplz retry (that would resend the book).
    if (typeof enrollCourse_ === 'function') {
      try { enrollCourse_(bill.email, bill.name, lang_(bill), 'direct'); }
      catch (err) { alertAdmin_('Course enrolment failed for bill ' + billId, String(err)); }
    }
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
 * Bot checks for the buy form (20 Oct 2026: card payments are on, so scripted submissions could
 * use the form to test stolen cards). The site sends hp (a honeypot people never see) and t
 * (ms since the page started loading). Returns a reason to refuse, or '' to allow.
 * Requests without t (posted straight to this endpoint, or from a page cached before the site
 * change) are refused, so deploy this at least 15 minutes after the site change goes live.
 */
var MIN_FORM_MS = 3000;          // a person scrolls, picks an edition and types; a bot posts at once
var PER_EMAIL_PER_HOUR = 3;      // bills per email address per hour
var ALL_PER_10_MIN = 30;         // bills across the whole site per 10 minutes

function botCheck_(p, email) {
  if (String(p.hp || '') !== '') return 'honeypot';
  var t = Number(p.t);
  if (!(t >= MIN_FORM_MS)) return 'too-fast';
  var cache = CacheService.getScriptCache();
  if (!countUnder_(cache, 'buy-em:' + email.toLowerCase(), PER_EMAIL_PER_HOUR, 3600)) return 'email-limit';
  if (!countUnder_(cache, 'buy-all', ALL_PER_10_MIN, 600)) {
    if (!cache.get('buy-all-alerted')) {
      cache.put('buy-all-alerted', '1', 600);
      alertAdmin_('Buy form rate limit hit',
        'More than ' + ALL_PER_10_MIN + ' purchase attempts in 10 minutes. New bills are refused until the window passes. ' +
        'If this is a real rush of buyers, raise ALL_PER_10_MIN in the script; if not, check the Billplz collection for junk bills.');
    }
    return 'site-limit';
  }
  return '';
}

/** Increment a cache counter; false once it has reached `max` within `seconds`. */
function countUnder_(cache, key, max, seconds) {
  var lock = LockService.getScriptLock();
  lock.waitLock(5000);
  try {
    var n = Number(cache.get(key) || 0);
    if (n >= max) return false;
    cache.put(key, String(n + 1), seconds);   // the window restarts on each counted bill
    return true;
  } finally {
    lock.releaseLock();
  }
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
  var refused = botCheck_(p, email);
  if (refused) {
    console.warn('Buy refused (' + refused + '): ' + email);
    return json_({ error: 'failed' });   // same reply as any failure: nothing for a bot to learn
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
 *   ?unsub=<id>                              leave the 13-week course (course.gs)
 */
function doGet(e) {
  var p = (e && e.parameter) ? e.parameter : {};
  if (p.unsub && typeof courseUnsubscribe_ === 'function') return courseUnsubscribe_(p.unsub);
  if (p.verify) return handleVerify_(String(p.verify));
  if (p.dl) return handleDownload_(String(p.dl), String(p.f || ''));
  if (p.ping) {
    return ContentService.createTextOutput('ok; mail quota left: ' + MailApp.getRemainingDailyQuota());
  }
  if (p.resend) {
    var expected = prop_('RESEND_TOKEN', '');
    if (!expected || p.token !== expected) return ContentService.createTextOutput('denied');
    var bill = fetchBill_(p.resend);
    if (bill.paid !== true) return ContentService.createTextOutput('bill not paid');
    sendBook_(bill.email, bill.name, lang_(bill), bill.id);
    logOrder_(bill, 'delivered', 'manual resend');
    return ContentService.createTextOutput('resent to ' + bill.email);
  }
  return ContentService.createTextOutput('book-delivery');
}

/* ==========================================================================================
 * Delivery guarantee (21 Oct 2026). Some delivery emails never reached buyers (Junk, or nothing
 * at all), so the ebook no longer depends on email:
 *  - the thank-you page asks ?verify=<bill id>; once Billplz says the bill is paid it shows
 *    the download buttons on the page;
 *  - every download link is personal: <site>/download.html?t=<token>&f=epub|pdf, where the
 *    token is the bill id plus an HMAC (DL_SECRET, created on first use). The page calls
 *    ?dl=<token>&f=..., which logs the download in the "events" tab and returns the Drive URL;
 *  - dailyDownloadCheck() (daily trigger, installDailyTrigger()) emails anyone paid more than
 *    24 h ago with no download one reminder, and sends the admin one summary;
 *  - resend.html POSTs {action:'resend'}: resend to the paid address, or to a new address only
 *    with the matching bill id. Logged and rate-limited.
 * The four book files must be shared "anyone with the link can view" (shareBuyerFiles()).
 * ========================================================================================== */
var SITE = 'https://www.mikaelchew.com';
var GUARANTEE_FROM = '2026-10-19';   // the daily check ignores orders before launch day

function dlSecret_() {
  var props = PropertiesService.getScriptProperties();
  var s = props.getProperty('DL_SECRET');
  if (!s) { s = Utilities.getUuid() + Utilities.getUuid(); props.setProperty('DL_SECRET', s); }
  return s;
}

function hex_(bytes) {
  return bytes.map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
}

/** "<bill id>.<24 hex chars>": proves the link was made by this script for that bill. */
function dlToken_(billId) {
  return billId + '.' + hex_(Utilities.computeHmacSha256Signature(String(billId), dlSecret_())).slice(0, 24);
}

/** The bill id a token belongs to, or null if the token is forged. */
function dlBill_(token) {
  token = String(token || '');
  var i = token.lastIndexOf('.');
  if (i < 1) return null;
  var id = token.slice(0, i);
  return dlToken_(id) === token ? id : null;
}

/** The buyer-facing download page for one file of one order. */
function dlPage_(billId, lang, f) {
  return SITE + (lang === 'en' ? '' : '/zh') + '/download.html?t=' + encodeURIComponent(dlToken_(billId)) + '&f=' + f;
}

function fileId_(lang, f) {
  return prop_((f === 'pdf' ? 'PDF_FILE_ID' : 'EPUB_FILE_ID') + (lang === 'en' ? '_EN' : ''), '');
}

/** Sheet timestamp (Date, or "yyyy-MM-dd HH:mm:ss" in Kuala Lumpur time) -> ms. */
function rowTime_(v) {
  if (v instanceof Date) return v.getTime();
  return new Date(String(v).replace(' ', 'T') + '+08:00').getTime();
}

/** Delivered orders, one per bill id (the latest row wins). */
function deliveredOrders_() {
  var values = sheet_().getDataRange().getValues(), byId = {};
  for (var i = 1; i < values.length; i++) {
    var r = values[i];
    if (String(r[6]) !== 'delivered' || !r[1]) continue;
    byId[String(r[1])] = { id: String(r[1]), time: rowTime_(r[0]), name: String(r[2] || ''),
      email: String(r[3] || '').trim(), lang: String(r[8] || '') === 'en' ? 'en' : 'zh' };
  }
  return Object.keys(byId).map(function (k) { return byId[k]; });
}

function events_() {
  var ss = SpreadsheetApp.openById(prop_('ORDERS_SHEET_ID', ''));
  var sh = ss.getSheetByName('events');
  if (!sh) { sh = ss.insertSheet('events'); sh.appendRow(['timestamp', 'bill_id', 'event', 'detail']); }
  return sh;
}

function logEvent_(billId, event, detail) {
  events_().appendRow([Utilities.formatDate(new Date(), 'Asia/Kuala_Lumpur', 'yyyy-MM-dd HH:mm:ss'),
    String(billId), event, detail || '']);
}

/** GET ?verify=<bill id>: the thank-you page's check. Download links only for a paid bill. */
function handleVerify_(billId) {
  var bill;
  try { bill = fetchBill_(billId); } catch (err) { return json_({ paid: false }); }
  if (bill.paid !== true) return json_({ paid: false });
  var lang = lang_(bill);
  return json_({ paid: true, lang: lang, epub: dlPage_(bill.id, lang, 'epub'), pdf: dlPage_(bill.id, lang, 'pdf') });
}

/** GET ?dl=<token>&f=epub|pdf from download.html: log it, return the Drive download URL. */
function handleDownload_(token, f) {
  var id = dlBill_(token);
  if (!id) return json_({ error: 'bad-link' });
  f = f === 'pdf' ? 'pdf' : 'epub';
  var order = deliveredOrders_().filter(function (o) { return o.id === id; })[0];
  var lang = order ? order.lang : null;
  if (!lang) {   // paid but not logged yet (the thank-you page can be faster than the callback)
    try {
      var bill = fetchBill_(id);
      if (bill.paid !== true) return json_({ error: 'not-paid' });
      lang = lang_(bill);
    } catch (err) { return json_({ error: 'bad-link' }); }
  }
  var fileId = fileId_(lang, f);
  if (DriveApp.getFileById(fileId).getSharingAccess() !== DriveApp.Access.ANYONE_WITH_LINK) {
    alertAdmin_('Download failed: file not shared by link', 'Run shareBuyerFiles(). Bill ' + id + ', ' + lang + ' ' + f);
    return json_({ error: 'unavailable' });
  }
  logEvent_(id, 'download-' + f, lang);
  return json_({ url: 'https://drive.google.com/uc?export=download&id=' + fileId });
}

/** POST {action:'resend', email, newEmail?, billId?, hp, t} from resend.html. */
function handleResend_(p) {
  var email = String(p.email || '').trim().toLowerCase();
  var to = String(p.newEmail || '').trim().toLowerCase() || email;
  var billId = String(p.billId || '').trim();
  var valid = function (e) { return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e); };
  if (!valid(email) || !valid(to)) return json_({ error: 'bad-email' });
  if (String(p.hp || '') !== '' || !(Number(p.t) >= MIN_FORM_MS)) return json_({ error: 'failed' });
  var cache = CacheService.getScriptCache();
  if (!countUnder_(cache, 'resend-em:' + email, 3, 86400) || !countUnder_(cache, 'resend-all', 30, 3600)) {
    return json_({ error: 'limit' });
  }
  var orders = deliveredOrders_().filter(function (o) { return o.email.toLowerCase() === email; });
  if (!orders.length) { logEvent_('-', 'resend-not-found', email); return json_({ error: 'not-found' }); }
  orders.sort(function (a, b) { return b.time - a.time; });
  var order = orders[0];
  if (to !== email) {   // a new address only with the bill id of that purchase
    order = orders.filter(function (o) { return o.id === billId; })[0];
    if (!order) { logEvent_(billId || '-', 'resend-bill-mismatch', email + ' -> ' + to); return json_({ error: 'bill-mismatch' }); }
  }
  sendBook_(to, order.name, order.lang, order.id);
  logEvent_(order.id, 'resend', to === email ? 'same address' : 'new address ' + to);
  if (to !== email) alertAdmin_('Ebook resent to a new address', order.name + ' (' + email + ', bill ' + order.id + ') -> ' + to);
  return json_({ ok: true, to: to });
}

/** The short "your download links" reminder. */
function sendReminder_(o) {
  var zh = o.lang !== 'en';
  var html = '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;color:#1a1a1a;max-width:560px">' +
    (zh
      ? '<p>' + (o.name ? o.name + '，' : '') + '你好。</p><p>你買了《直銷孫子兵法之不戰而勝》，但我看到電子書還沒有下載。如果之前的信跑到垃圾郵件匣，這裡是你的下載按鈕：</p>'
      : '<p>' + (o.name ? 'Hi ' + o.name + ',' : 'Hi,') + '</p><p>You bought <i>The Art of War for Direct Selling</i>, but the ebook hasn&#39;t been downloaded yet. In case the first email went to Junk, here are your download buttons:</p>') +
    '<p>' + fileButton_(dlPage_(o.id, o.lang, 'epub'), zh ? '下載 EPUB（手機、平板）' : 'Download EPUB (phone, tablet)') + '<br>' +
    fileButton_(dlPage_(o.id, o.lang, 'pdf'), zh ? '下載 PDF（電腦、列印）' : 'Download PDF (computer, print)') + '</p>' +
    (zh ? '<p>有任何問題，直接回覆這封信，我會親自處理。<br>周俊德（Mikael Chew）</p>'
        : '<p>If anything doesn&#39;t work, reply to this email and I&#39;ll sort it out myself.<br>Mikael Chew</p>') +
    '</div>';
  send_({ to: o.email, name: 'Mikael Chew', replyTo: prop_('REPLY_TO', ''), htmlBody: html,
    subject: zh ? '你的電子書下載連結：《直銷孫子兵法之不戰而勝》' : 'Your download links: The Art of War for Direct Selling' });
}

/** Daily: remind anyone paid more than 24 h ago with no download (once), then one summary to the admin. */
function dailyDownloadCheck() {
  var now = Date.now(), from = new Date(GUARANTEE_FROM + 'T00:00:00+08:00').getTime();
  var ev = events_().getDataRange().getValues(), downloaded = {}, reminded = {};
  for (var i = 1; i < ev.length; i++) {
    var e = String(ev[i][2]);
    if (e.indexOf('download-') === 0) downloaded[String(ev[i][1])] = true;
    if (e === 'reminder') reminded[String(ev[i][1])] = true;
  }
  var late = deliveredOrders_().filter(function (o) {
    return o.time >= from && o.time < now - 24 * 3600 * 1000 && !downloaded[o.id] && o.email;
  });
  var lines = late.map(function (o) {
    var note = 'reminded earlier';
    if (!reminded[o.id]) {
      try { sendReminder_(o); logEvent_(o.id, 'reminder', o.email); note = 'reminder sent today'; }
      catch (err) { note = 'reminder FAILED: ' + err; }
    }
    return '- ' + (o.name || '(no name)') + ', ' + o.email + ', ' + o.lang + ', paid ' +
      Utilities.formatDate(new Date(o.time), 'Asia/Kuala_Lumpur', 'd MMM HH:mm') + ': ' + note;
  });
  if (lines.length) {
    alertAdmin_('Daily: ' + lines.length + ' buyer(s) have not downloaded the ebook',
      'Paid more than 24 hours ago, no download yet. A WhatsApp may help:\n\n' + lines.join('\n'));
  }
}

/** Run once from the editor: run dailyDownloadCheck every day at about 10:00 Kuala Lumpur time. */
function installDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'dailyDownloadCheck') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('dailyDownloadCheck').timeBased().everyDays(1).atHour(10).inTimezone('Asia/Kuala_Lumpur').create();
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
