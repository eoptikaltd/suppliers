/* Atlas menu — one shared menu for every eOptika tool.   menu.js · v1 · 2026-11-10

   Add to any page (the tool serves /_atlas/ with atlas_menu.attach):
       <script src="/_atlas/menu.js?tool=<tool id>" defer></script>
   Options on the script address:
       tool=<id>      this tool: highlighted, and its group opened
       mount=<css>    put the Atlas button at the start of that element (e.g. .topbar);
                      without it the button floats at the top-left of the page
       size=s         a smaller button (34 px) for a slim top bar that would
                      otherwise wrap (e.g. BI)

   The Atlas button opens the menu over the page; the button inside the menu, a tap
   beside it, Esc, or picking a tool closes it. Menu content comes from menu.json on
   the page's own address (answered by the tool today, by Gateway once the tool sits
   behind it), so it is the same everywhere and only lists what this person may open.
*/
(function () {
  'use strict';
  if (window.__atlasMenu) return;
  window.__atlasMenu = true;

  var me = document.currentScript;
  var src = new URL(me && me.src ? me.src : '/_atlas/menu.js', location.href);
  var BASE = new URL('./', src).href;          // .../_atlas/
  var TOOL = src.searchParams.get('tool') || '';
  var MOUNT = src.searchParams.get('mount') || '';
  var SMALL = src.searchParams.get('size') === 's';
  var GROUPS_KEY = 'atlas-menu-groups';
  var root = document.documentElement;

  var hu = /^hu/i.test(root.lang || navigator.language || '');
  var T = hu ? { open: 'Atlas menü megnyitása', close: 'Atlas menü bezárása', none: 'Nincs elérhető eszköz.' }
             : { open: 'Open the Atlas menu', close: 'Close the Atlas menu', none: 'No tools to show.' };

  // the look: load menu.css unless the page already has it
  if (!document.querySelector('link[href*="_atlas/menu.css"]')) {
    var css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = BASE + 'menu.css';
    document.head.appendChild(css);
  }

  function el(tag, cls, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function icon(name) {
    var ns = 'http://www.w3.org/2000/svg';
    var s = document.createElementNS(ns, 'svg');
    s.setAttribute('aria-hidden', 'true');
    var u = document.createElementNS(ns, 'use');
    u.setAttribute('href', '#i-' + name);
    s.appendChild(u);
    return s;
  }
  function chev() {
    var ns = 'http://www.w3.org/2000/svg';
    var s = document.createElementNS(ns, 'svg');
    s.setAttribute('class', 'atm-chev');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('fill', 'none');
    s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '2');
    s.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', 'M6 9l6 6 6-6');
    s.appendChild(p);
    return s;
  }
  function stored() {
    try { return JSON.parse(localStorage.getItem(GROUPS_KEY)) || {}; } catch (e) { return {}; }
  }
  function store(v) {
    try { localStorage.setItem(GROUPS_KEY, JSON.stringify(v)); } catch (e) {}
  }

  function start() {
    // ---- the Atlas button on the page -------------------------------------
    var opener = el('button', 'atm-mark', { type: 'button', 'aria-controls': 'atlas-menu',
      'aria-expanded': 'false', 'aria-label': T.open, title: T.open });
    opener.appendChild(icon('atlas'));
    if (SMALL) opener.classList.add('atm-mark--s');
    function mountIn(place) {
      opener.classList.remove('atm-mark--float');
      opener.classList.add('atm-mark--mounted');
      place.insertBefore(opener, place.firstChild);
    }
    function floatIt() {
      opener.classList.remove('atm-mark--mounted');
      opener.classList.add('atm-mark--float');
      document.body.appendChild(opener);
    }
    // Keep the button where it belongs. Pages drawn by script (Dash) build their
    // top bar a moment after this runs, and may redraw it when the person moves
    // between the tool's own pages, which throws the button away: put it back.
    function keepPlaced() {
      var p = MOUNT ? document.querySelector(MOUNT) : null;
      if (p) { if (opener.parentNode !== p) mountIn(p); }
      else if (!opener.isConnected) floatIt();
    }
    floatIt();
    keepPlaced();
    if (MOUNT && window.MutationObserver) {
      var queued = false;
      new MutationObserver(function () {
        if (queued) return;
        queued = true;
        (window.requestAnimationFrame || setTimeout)(function () { queued = false; keepPlaced(); });
      }).observe(document.body, { childList: true, subtree: true });
    }

    // ---- the menu itself (filled when menu.json arrives) -------------------
    var backdrop = el('button', 'atm-backdrop', { type: 'button', tabindex: '-1', 'aria-label': T.close });
    var panel = el('aside', 'atm-panel', { id: 'atlas-menu', 'aria-label': 'Atlas' });
    var head = el('div', 'atm-head');
    var closer = el('button', 'atm-mark', { type: 'button', 'aria-controls': 'atlas-menu',
      'aria-label': T.close, title: T.close });
    closer.appendChild(icon('atlas'));
    var brand = el('a', 'atm-brand', { href: 'https://atlas.eoptika.com/' });
    brand.textContent = 'Atlas';
    head.appendChild(closer);
    head.appendChild(brand);
    var list = el('nav', 'atm-groups', { 'aria-label': 'Atlas' });
    panel.appendChild(head);
    panel.appendChild(list);
    document.body.appendChild(backdrop);
    document.body.appendChild(panel);

    var isOpen = false;
    function setOpen(open, focusBack) {
      isOpen = open;
      root.classList.toggle('atm-open', open);
      opener.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) { closer.focus({ preventScroll: true }); }
      else if (focusBack) { opener.focus({ preventScroll: true }); }
    }
    opener.addEventListener('click', function () { setOpen(!isOpen, true); });
    closer.addEventListener('click', function () { setOpen(false, true); });
    backdrop.addEventListener('click', function () { setOpen(false, true); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) setOpen(false, true);
    });
    list.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a.atm-item')) setOpen(false, false);
    });

    // ---- icons + content ---------------------------------------------------
    fetch(BASE + 'menu-icons.svg', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.text() : ''; })
      .then(function (svg) {
        if (!svg) return;
        var box = el('div', '', { 'aria-hidden': 'true', style: 'position:absolute;width:0;height:0;overflow:hidden' });
        box.innerHTML = svg;
        document.body.insertBefore(box, document.body.firstChild);
      })
      .catch(function () {});

    fetch(BASE + 'menu.json', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(fill)
      .catch(function () { opener.hidden = true; });   // no menu to show: no button either

    function fill(menu) {
      var home = (menu.home && menu.home.url) || 'https://atlas.eoptika.com';
      brand.href = home;
      var labels = menu.statuses || {};
      var openState = stored();
      var groups = menu.groups || [];
      if (!groups.length) {
        var none = el('p', 'atm-empty');
        none.textContent = T.none;
        list.appendChild(none);
        return;
      }
      groups.forEach(function (g) {
        var items = g.items || [];
        var mine = items.some(function (it) { return it.id === TOOL; });
        var open = mine || openState[g.name] === true;
        var box = el('section', 'atm-group', { 'data-open': open ? 'true' : 'false' });
        var btn = el('button', 'atm-section', { type: 'button', 'aria-expanded': open ? 'true' : 'false' });
        var name = el('span');
        name.textContent = g.name;
        btn.appendChild(name);
        btn.appendChild(chev());
        btn.addEventListener('click', function () {
          var now = box.getAttribute('data-open') !== 'true';
          box.setAttribute('data-open', now ? 'true' : 'false');
          btn.setAttribute('aria-expanded', now ? 'true' : 'false');
          var s = stored(); s[g.name] = now; store(s);
        });
        var wrap = el('div', 'atm-items');
        items.forEach(function (it) {
          // a tool without its own page links to its tile on the Atlas home page
          var href = it.url || (home.replace(/\/$/, '') + '/#t-' + encodeURIComponent(it.id));
          var a = el('a', 'atm-item', { href: href });
          if (it.id === TOOL) { a.classList.add('atm-item--active'); a.setAttribute('aria-current', 'page'); }
          a.appendChild(icon(it.icon || it.id));
          var label = el('span', 'atm-label');
          label.textContent = it.label;
          a.appendChild(label);
          var dot = el('span', 'atm-dot atm-dot--' + (it.status || 'plan'));
          var word = labels[it.status] || it.status || '';
          if (word) { dot.setAttribute('title', word); dot.setAttribute('aria-label', word); dot.setAttribute('role', 'img'); }
          a.appendChild(dot);
          wrap.appendChild(a);
        });
        box.appendChild(btn);
        box.appendChild(wrap);
        list.appendChild(box);
      });
      var active = list.querySelector('.atm-item--active');
      if (active) {   // show this tool's entry when the menu opens
        opener.addEventListener('click', function () {
          if (isOpen) active.scrollIntoView({ block: 'center' });
        });
      }
    }
  }

  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
})();
