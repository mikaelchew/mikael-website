// ============================================
// mikaelchew.com — shared site behaviour (Strategist's Map redesign)
// Loaded with `defer` on every rebuilt page. The homepage map lives in js/map.js.
// ============================================
(function () {
  'use strict';

  var html = document.documentElement;
  var zh = (html.lang || '').indexOf('zh') === 0;

  // ---------- GA4 ----------
  // Production hosts report normally; previews (Vercel, localhost) report in DebugView only.
  var PROD = /^(www\.)?mikaelchew\.com$/.test(location.hostname); // www.mikaelchew.com
  if (typeof gtag === 'function') {
    gtag('config', 'G-ENGNTZ3PPC', PROD ? {} : { debug_mode: true });
  }
  function trackEvent(eventName, params) {
    if (typeof gtag === 'function') gtag('event', eventName, params || {});
  }
  window.trackEvent = trackEvent;

  // ---------- Navigation (phone menu) ----------
  function initNav() {
    var btn = document.querySelector('.menu-btn');
    if (!btn) return;
    var setOpen = function (open) {
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      html.classList.toggle('nav-open', open);
    };
    btn.addEventListener('click', function () { setOpen(btn.getAttribute('aria-expanded') !== 'true'); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  }

  // ---------- Click tracking (ported unchanged from js/main.js) ----------
  function initTracking() {
    document.querySelectorAll('a[href^="https://wa.me/"]').forEach(function (link) {
      link.addEventListener('click', function () {
        trackEvent('whatsapp_click', {
          source_page: window.location.pathname,
          link_class: link.className.replace(/\s+/g, ' ').trim().slice(0, 80)
        });
      });
    });
    document.querySelectorAll('a[href*="linkedin.com"], a[href*="facebook.com"], a[href*="instagram.com"]').forEach(function (link) {
      link.addEventListener('click', function () {
        var href = link.href, platform = 'unknown';
        if (href.indexOf('linkedin.com') > -1) platform = 'linkedin';
        else if (href.indexOf('facebook.com') > -1) platform = 'facebook';
        else if (href.indexOf('instagram.com') > -1) platform = 'instagram';
        var isShare = href.indexOf('/sharing/') > -1 || href.indexOf('/sharer/') > -1;
        trackEvent(isShare ? 'social_share' : 'social_click', { platform: platform, source_page: window.location.pathname });
      });
    });
    document.querySelectorAll('a[href$=".pdf"]').forEach(function (link) {
      link.addEventListener('click', function () {
        trackEvent('file_download', { file_name: link.href.split('/').pop(), source_page: window.location.pathname });
      });
    });
    // Language switch is now a plain link between the baked EN and /zh/ pages.
    document.querySelectorAll('a.lang-link').forEach(function (link) {
      link.addEventListener('click', function () {
        trackEvent('language_toggle', { new_language: zh ? 'en' : 'zh', page_path: window.location.pathname });
      });
    });
    // Writing index
    document.querySelectorAll('.blog-filter').forEach(function (btn) {
      btn.addEventListener('click', function () { trackEvent('blog_filter_click', { filter: btn.dataset.filter || 'unknown' }); });
    });
    var more = document.querySelector('#blog-show-more button');
    if (more) more.addEventListener('click', function () { trackEvent('blog_show_more_click', { page_path: window.location.pathname }); });
    // Post scroll depth
    if (document.querySelector('article.post')) {
      var seen = {};
      window.addEventListener('scroll', function () {
        var h = document.documentElement.scrollHeight - window.innerHeight;
        if (h <= 0) return;
        var pct = Math.round((window.scrollY / h) * 100);
        [25, 50, 75, 100].forEach(function (t) {
          if (pct >= t && !seen[t]) { seen[t] = true; trackEvent('scroll_depth', { depth: t, page_path: window.location.pathname }); }
        });
      }, { passive: true });
    }
  }

  // ---------- Kit / Formspree forms: inline confirmation, normal post as fallback ----------
  function listEvent(form) {
    var tagInput = form.querySelector('input[name="tags"]');
    var tag = tagInput ? tagInput.value : 'unknown';
    var eventName = 'newsletter_subscribe';
    if (tag === 'long-game-launch') eventName = 'long_game_waitlist';
    else if (tag === 'book-chapter') eventName = 'book_waitlist';
    else if (tag === 'book-launch') eventName = 'book_launch_waitlist';
    else if (tag === 'book-print') eventName = 'book_print_waitlist';
    trackEvent(eventName, { list_tag: tag, source_page: window.location.pathname });
  }
  function initForms() {
    document.querySelectorAll('form[data-ajax]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (form.querySelector('input[name="tags"]')) listEvent(form);
        var btn = form.querySelector('button[type="submit"]');
        if (btn) btn.disabled = true;
        // Kit doesn't send CORS headers, so its response is opaque: a resolved fetch means the
        // request reached it. Formspree answers CORS requests that ask for JSON (and only then
        // records them without a reCAPTCHA page), so its status is checked. Any failure falls
        // back to the ordinary form post, which always works.
        var formspree = form.action.indexOf('formspree.io') !== -1;
        var req = formspree
          ? fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
              .then(function (res) { if (!res.ok) throw new Error('formspree ' + res.status); })
          : fetch(form.action, { method: 'POST', body: new FormData(form), mode: 'no-cors' });
        req
          .then(function () {
            var ok = form.parentNode.querySelector('.form-ok');
            form.hidden = true;
            if (ok) { ok.hidden = false; ok.focus(); }
          })
          .catch(function () {
            form.removeAttribute('data-ajax');
            form.submit();
          });
      });
    });
  }

  // ---------- Book buy form (ported unchanged from js/main.js) ----------
  // Apps Script serves HTML in a sandboxed iframe that cannot redirect the page,
  // so the script returns JSON and this page does the navigation to Billplz.
  function initBuyForm() {
    document.querySelectorAll('.book-buy-form[data-endpoint]').forEach(function (form) {
      var btn = form.querySelector('button[type="submit"]');
      var status = form.querySelector('.book-buy-status');
      var label = btn.textContent;
      var msg = {
        busy: zh ? '正在前往安全付款頁面…' : 'Opening secure payment…',
        'bad-email': zh ? '電子郵件地址好像不對，請再檢查一次。' : "That email address doesn't look right. Please check it.",
        failed: zh ? '付款無法啟動。請再試一次，或寫信到 hello@mikaelchew.com。' : 'Payment could not be started. Please try again, or email hello@mikaelchew.com.'
      };
      // English pages preselect the English edition once it is on sale (data/site.json "english": "live")
      if (form.elements.edition && !zh && html.dataset.english === 'live') form.elements.edition.value = 'en';
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var edition = form.elements.edition ? form.elements.edition.value : 'zh';
        trackEvent('begin_checkout', {
          currency: 'MYR',
          value: 29.90,
          items: [{ item_name: 'Ebook ' + edition + ' edition', item_variant: (zh ? 'zh' : 'en') + ' page' }],
          source_page: window.location.pathname
        });
        btn.disabled = true;
        btn.textContent = msg.busy;
        status.textContent = '';
        fetch(form.dataset.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          // edition 'zh' or 'en' tells the delivery script which files to send
          body: JSON.stringify({ action: 'buy', name: form.elements.name.value, email: form.elements.email.value, edition: edition })
        })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.url) { window.location.href = res.url; return; }
            throw new Error(res.error || 'failed');
          })
          .catch(function (err) {
            status.textContent = msg[err.message] || msg.failed;
            btn.disabled = false;
            btn.textContent = label;
          });
      });
    });
  }

  // ---------- Seals: stamp once, when 60% in view and their image has loaded ----------
  function initSeals() {
    var seals = document.querySelectorAll('[data-stamp]');
    if (!seals.length) return;
    if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    html.classList.add('stamps');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        var img = en.target.closest('.has-seal') && en.target.closest('.has-seal').querySelector('img');
        var ready = img && img.decode ? img.decode().catch(function () {}) : Promise.resolve();
        ready.then(function () { en.target.classList.add('press'); });
      });
    }, { threshold: 0.6 });
    seals.forEach(function (s) { io.observe(s); });
  }

  // ---------- Writing: scheduled posts, topic filter, show more ----------
  // Anything with a future data-pubdate (index entries, next/previous links) stays hidden
  // until that local date, so a post can be published ahead and appear on its day.
  var SHOW = 8;
  function initWriting() {
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    document.querySelectorAll('[data-pubdate]').forEach(function (el) {
      var s = el.getAttribute('data-pubdate');
      if (s && new Date(s + 'T00:00:00').getTime() > today.getTime()) {
        el.classList.add('post-scheduled');
        el.hidden = true;
      }
    });
    // ...and anything with data-until (a time-limited offer) hides the day after that date
    document.querySelectorAll('[data-until]').forEach(function (el) {
      var s = el.getAttribute('data-until');
      if (s && new Date(s + 'T00:00:00').getTime() < today.getTime()) el.hidden = true;
    });

    var items = Array.prototype.slice.call(document.querySelectorAll('.dispatch:not(.post-scheduled)'));
    if (!items.length) return;
    var moreWrap = document.getElementById('blog-show-more');
    function show(filter, all) {
      var shown = 0;
      document.querySelectorAll('.blog-filter').forEach(function (b) {
        b.setAttribute('aria-pressed', (b.dataset.filter || 'all') === filter ? 'true' : 'false');
      });
      items.forEach(function (it) {
        var match = filter === 'all' || it.getAttribute('data-category') === filter;
        it.hidden = !match || (!all && filter === 'all' && shown >= SHOW);
        it.classList.toggle('top', match && shown === 0);
        if (match) shown++;
      });
      if (moreWrap) moreWrap.hidden = all || filter !== 'all' || shown <= SHOW;
    }
    show('all', false);
    document.querySelectorAll('.blog-filter').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.blog-filter').forEach(function (b) { b.classList.toggle('active', b === btn); });
        show(btn.dataset.filter || 'all', false);
      });
    });
    var more = moreWrap && moreWrap.querySelector('button');
    if (more) more.addEventListener('click', function () { show('all', true); });
  }

  // ---------- Motion: scroll reveals, the About timeline, count-up figures ----------
  // Only below-the-fold elements are hidden, so nothing on the first screen waits for JS
  // (no effect on LCP). Without IntersectionObserver or with reduced motion, nothing hides.
  var REVEAL = '.sec-h, .cards > *, .c-grid .c, .dispatch, .legend-group, .lines li, .faq details, ' +
    '.side, .print, .band-in > *, .glance > *, .quote, .free-card, .audience > div, .author, .buy-card, ' +
    '.chapter-cta, .post-nav, .related li, .story .copy > *';
  function countUp(el) {
    var m = el.textContent.match(/^(\d+)(.*)$/);
    if (!m) return;
    var end = parseInt(m[1], 10), rest = m[2], t0 = null;
    function step(t) {
      if (t0 === null) t0 = t;
      var p = Math.min((t - t0) / 900, 1), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(end * eased) + rest;
      if (p < 1) requestAnimationFrame(step);
    }
    el.textContent = '0' + rest;
    requestAnimationFrame(step);
  }
  function initMotion() {
    if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var fold = window.innerHeight;
    var below = function (el) { return el.getBoundingClientRect().top > fold * 0.92; };
    var items = Array.prototype.slice.call(document.querySelectorAll(REVEAL)).filter(below);
    var route = document.querySelector('.route');
    var counts = Array.prototype.slice.call(document.querySelectorAll('.glance b')).filter(below);
    if (!items.length && !(route && below(route)) && !counts.length) return;
    html.classList.add('reveals');
    items.forEach(function (el) {
      var sibs = Array.prototype.filter.call(el.parentNode.children, function (s) { return s.matches(REVEAL); });
      el.style.setProperty('--i', Math.min(sibs.indexOf(el), 6));
      el.setAttribute('data-reveal', '');
    });
    if (route) {
      Array.prototype.forEach.call(route.children, function (li, i) { li.style.setProperty('--i', i); });
      if (!below(route)) route.classList.add('in');
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        if (en.target.tagName === 'B') { countUp(en.target); return; }
        var el = en.target;
        el.classList.add('in');
        // Once revealed, hand the element back to its own transitions (card hovers etc.).
        if (el.hasAttribute('data-reveal')) {
          var wait = 1000 + (parseInt(el.style.getPropertyValue('--i'), 10) || 0) * 70;
          setTimeout(function () { el.removeAttribute('data-reveal'); el.classList.remove('in'); }, wait);
        }
      });
    }, { rootMargin: '0px 0px -12% 0px' });
    items.forEach(function (el) { io.observe(el); });
    counts.forEach(function (el) { io.observe(el); });
    if (route && below(route)) io.observe(route);
  }

  initNav();
  initTracking();
  initForms();
  initBuyForm();
  initSeals();
  initWriting();
  initMotion();
})();
