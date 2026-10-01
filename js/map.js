// ============================================
// Homepage map: the route halts at each chapter, advances on scroll, ends at the launch date.
// Waypoints and copy come from the chapter list in the page (.chapters li), which
// build_chapters.py renders from data/chapters.json, so EN and /zh/ share one source.
// The <html class="motion"> decision is made in <head> (reduced motion, low device memory);
// a slow first 30 frames (median > 34ms) also drops to the static map.
// ============================================
(function () {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var html = document.documentElement;
  var zh = (html.lang || '').indexOf('zh') === 0;
  var $ = function (id) { return document.getElementById(id); };
  var ops = $('ops'), map = $('map');
  if (!ops || !map) return;

  // ---------- read the chapters from the page ----------
  var items = [].slice.call(document.querySelectorAll('.chapters li'));
  var parts = [].slice.call(document.querySelectorAll('.part h3 > span:first-child')).map(function (s) { return s.textContent; });
  var CH = items.map(function (li) {
    return {
      x: +li.dataset.x, y: +li.dataset.y, part: +li.dataset.part, free: li.hasAttribute('data-free'),
      title: li.querySelector('b').textContent, alt: li.querySelector('.alt').textContent, line: li.querySelector('p').textContent
    };
  });
  var N = CH.length;
  var pad = function (i) { return (i + 1 < 10 ? '0' : '') + (i + 1); };

  // ---------- draw the sheet: grid, route, waypoints ----------
  var grid = $('grid'), x, y;
  for (x = 300; x < 2400; x += 300) grid.insertAdjacentHTML('beforeend', '<line x1="' + x + '" x2="' + x + '" y1="0" y2="1500"/>');
  for (y = 300; y < 1500; y += 300) grid.insertAdjacentHTML('beforeend', '<line y1="' + y + '" y2="' + y + '" x1="0" x2="2400"/>');
  // lead-in from the map edge, then every position; a little hand-drawn wobble baked into the path
  var jitter = function (i, s) { return ((Math.sin(i * 12.9898 + s) * 43758.5453) % 1) * 2 - 1; };
  var pts = [[40, 1470]];
  CH.forEach(function (c, i) {
    if (i > 0) { var p = CH[i - 1]; pts.push([(p.x + c.x) / 2 + jitter(i, 1) * 14, (p.y + c.y) / 2 + jitter(i, 2) * 14]); }
    pts.push([c.x, c.y]);
  });
  var seg = function (a, b, c, d) {
    return ' C' + (b[0] + (c[0] - a[0]) / 6) + ',' + (b[1] + (c[1] - a[1]) / 6) + ' ' + (c[0] - (d[0] - b[0]) / 6) + ',' + (c[1] - (d[1] - b[1]) / 6) + ' ' + c[0] + ',' + c[1];
  };
  var pathTo = function (k) {
    var d = 'M' + pts[0][0] + ',' + pts[0][1];
    for (var i = 0; i < k; i++) d += seg(pts[i - 1] || pts[i], pts[i], pts[i + 1], pts[i + 2] || pts[i + 1]);
    return d;
  };
  var route = $('route'), full = pathTo(pts.length - 1);
  route.setAttribute('d', full); $('ghost').setAttribute('d', full);
  var L = route.getTotalLength();
  var probe = document.createElementNS(NS, 'path'); map.appendChild(probe);
  var at = CH.map(function (_, i) { probe.setAttribute('d', pathTo(i === 0 ? 1 : 1 + i * 2)); return probe.getTotalLength(); });
  probe.remove();
  var wps = CH.map(function (c, i) {
    var g = document.createElementNS(NS, 'g'); g.setAttribute('class', 'wp'); g.dataset.i = i;
    g.innerHTML = '<circle class="halo" cx="' + c.x + '" cy="' + c.y + '" r="52"/><circle class="ring" cx="' + c.x + '" cy="' + c.y + '" r="32"/><text x="' + c.x + '" y="' + (c.y + 1) + '">' + pad(i) + '</text>';
    $('wps').appendChild(g); return g;
  });
  var rail = $('rail');
  CH.forEach(function (c, i) {
    if (i && c.part !== CH[i - 1].part) rail.insertAdjacentHTML('beforeend', '<span class="sep" aria-hidden="true"></span>');
    var label = zh ? '第' + (i + 1) + '章：' + c.title : 'Chapter ' + (i + 1) + ': ' + c.title;
    rail.insertAdjacentHTML('beforeend', '<button type="button" class="num" data-i="' + i + '" aria-label="' + label.replace(/"/g, '&quot;') + '">' + pad(i) + '</button>');
  });
  var railBtns = [].slice.call(rail.querySelectorAll('button'));
  var nib = $('nib'), cam = $('cam');
  var intro = $('intro'), briefing = $('briefing'), finale = $('finale');

  var stopped = false;
  function toStatic() {
    stopped = true;
    html.classList.remove('motion');
    ops.style.height = '';
    [].slice.call(ops.querySelectorAll('.snap')).forEach(function (s) { s.remove(); });
    cam.style.transform = '';
    route.style.strokeDasharray = 'none'; route.style.strokeDashoffset = '0';
    wps.forEach(function (w) { w.classList.add('done'); });
    nib.setAttribute('transform', 'translate(' + CH[N - 1].x + ',' + CH[N - 1].y + ')');
    [intro, briefing, finale].forEach(function (p) { p.classList.remove('off'); p.removeAttribute('inert'); });
  }

  if (!html.classList.contains('motion')) { toStatic(); return; }

  // ---------- motion mode ----------
  var HALT = 45, FIN = 70; // svh: a halt per chapter, a slightly longer finale
  ops.style.height = 'calc(100svh + ' + (N * HALT + FIN) + 'svh)';
  for (var i = 0; i <= N; i++) {
    var s = document.createElement('div'); s.className = 'snap';
    s.style.top = (i < N ? i * HALT + (i ? HALT * 0.25 : 0) : N * HALT + FIN) + 'svh';
    ops.appendChild(s);
  }
  route.style.strokeDasharray = L;

  var vh = innerHeight, vw = innerWidth, opsTop = 0, span = 1, narrow = false, cardTop = 0;
  function measure() {
    vh = innerHeight; vw = innerWidth; narrow = vw <= 900;
    opsTop = ops.getBoundingClientRect().top + scrollY; span = ops.offsetHeight - vh;
    cardTop = briefing.getBoundingClientRect().top || vh * 0.62;
  }
  function jump(i) {
    scrollTo({ top: opsTop + (i * HALT + (i ? HALT * 0.25 : 0)) * vh / 100 + 1, behavior: 'smooth' });
  }
  railBtns.concat([].slice.call(document.querySelectorAll('.ch'))).forEach(function (b) { b.addEventListener('click', function () { jump(+b.dataset.i); }); });
  wps.forEach(function (w) { w.addEventListener('click', function () { jump(+w.dataset.i); }); });

  function show(el, on) { el.classList.toggle('off', !on); if (on) el.removeAttribute('inert'); else el.setAttribute('inert', ''); }
  var k = -1, reached = 0;
  function fill(i) {
    var c = CH[i];
    $('b-part').textContent = parts[c.part] || '';
    $('b-n').textContent = pad(i);
    $('b-en').textContent = c.title; $('b-zh').textContent = c.alt; $('b-line').textContent = c.line;
    $('b-link').hidden = !c.free;
  }
  function setK(i, forward) {
    if (i === k) return;
    var body = $('b-body');
    if (forward && k >= 0 && !briefing.classList.contains('off') && body.animate) {
      body.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 100, easing: 'cubic-bezier(.23,1,.32,1)', fill: 'forwards' }).onfinish = function () {
        fill(i);
        body.animate([{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 220, easing: 'cubic-bezier(.23,1,.32,1)', fill: 'forwards' });
      };
    } else fill(i);
    wps.forEach(function (w, j) { w.classList.toggle('done', j < i); w.classList.toggle('now', j === i); });
    railBtns.forEach(function (b, j) { b.classList.toggle('done', j < i); if (j === i) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
    if (forward && i > reached) { var w = wps[i]; w.classList.remove('arrive'); void w.getBBox(); w.classList.add('arrive'); reached = i; }
    k = i;
  }

  // camera: scale + translate, eased with a time constant (frame-rate independent)
  var cs = 1, cx = 0, cy = 0, last = 0, raf = 0, onScreen = true, lastLen = -1;
  function target(len, g) {
    var q = route.getPointAtLength(Math.max(0, len));
    if (!narrow) { var s0 = Math.max(vw / 2400, vh / 1500); return [s0, (vw - 2400 * s0) / 2, (vh - 1500 * s0) / 2]; }
    var a = vw / 760, b = vw / 2400, sc = a + (b - a) * g;
    var tx = Math.min(0, Math.max(vw - 2400 * a, vw / 2 - q.x * a));
    var ty = Math.min(0, Math.max(cardTop - 1500 * a - vh * 0.1, cardTop * 0.45 - q.y * a));
    return [sc, tx + ((vw - 2400 * b) / 2 - tx) * g, ty + (vh * 0.5 - 1500 * b / 2 - ty) * g];
  }
  var smooth = function (v) { return v * v * (3 - 2 * v); };
  function tick(now) {
    raf = 0;
    if (stopped) return;
    var dt = Math.min(64, now - (last || now)); last = now;
    var u = Math.max(0, Math.min(span, scrollY - opsTop)) / vh * 100;
    var len, i, forward = true, g = 0;
    if (u < N * HALT) {
      var xx = u / HALT, s = Math.min(N - 1, Math.floor(xx)), f = xx - s;
      if (s >= N - 1 || f < 0.5) { len = at[s]; i = s; }
      else { var v = smooth((f - 0.5) / 0.5); len = at[s] + (at[s + 1] - at[s]) * v; i = v >= 1 ? s + 1 : s; }
    } else { len = L; i = N - 1; g = smooth(Math.min(1, (u - N * HALT) / (FIN * 0.8))); }
    if (len !== lastLen) {
      route.style.strokeDashoffset = L - len;
      var q = route.getPointAtLength(len); nib.setAttribute('transform', 'translate(' + q.x.toFixed(1) + ',' + q.y.toFixed(1) + ')');
      forward = len >= lastLen; lastLen = len;
    }
    show(intro, u < HALT * 0.3);
    show(briefing, u >= HALT * 0.3 && g === 0);
    show(finale, g > 0.35);
    ops.classList.toggle('end', g > 0.35);
    setK(i, forward);
    var t = target(len, g), kf = 1 - Math.exp(-dt / 180);
    cs += (t[0] - cs) * kf; cx += (t[1] - cx) * kf; cy += (t[2] - cy) * kf;
    cam.style.transform = 'translate3d(' + cx.toFixed(1) + 'px,' + cy.toFixed(1) + 'px,0) scale(' + cs.toFixed(4) + ')';
    if (onScreen && (Math.abs(t[0] - cs) > 0.0005 || Math.abs(t[1] - cx) > 0.3 || Math.abs(t[2] - cy) > 0.3)) kick(); else last = 0;
  }
  function kick() { if (!raf) raf = requestAnimationFrame(tick); }
  new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; if (onScreen) kick(); }).observe(ops);
  addEventListener('scroll', kick, { passive: true });
  addEventListener('resize', function () { measure(); last = 0; kick(); });
  measure();
  var t0 = target(at[0], 0); cs = t0[0]; cx = t0[1]; cy = t0[2];
  cam.style.transform = 'translate3d(' + cx + 'px,' + cy + 'px,0) scale(' + cs + ')';
  kick();

  // ---------- low-end check: if the first 30 frames are slow, show the static map ----------
  var frames = [], prev = 0;
  requestAnimationFrame(function sample(now) {
    if (prev) frames.push(now - prev);
    prev = now;
    if (frames.length < 30) { requestAnimationFrame(sample); return; }
    frames.sort(function (a, b) { return a - b; });
    if (frames[15] > 34) toStatic();
  });
})();
