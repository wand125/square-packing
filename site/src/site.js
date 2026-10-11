(function () {
  var H = document.documentElement;
  function L() { return H.lang === 'ja' ? 'ja' : 'en'; }
  function labels() {
    var b = document.getElementById('lang'), t = document.getElementById('theme');
    if (b) b.textContent = L() === 'ja' ? 'English' : '日本語';
    if (t) t.textContent = H.dataset.theme === 'light' ? (L() === 'ja' ? 'ダーク' : 'Dark') : (L() === 'ja' ? 'ライト' : 'Light');
    document.querySelectorAll('[data-ph-en]').forEach(function (el) { el.placeholder = el.getAttribute('data-ph-' + L()); });
    document.dispatchEvent(new Event('langchange'));
  }
  window.SP = { L: L, labels: labels };
  document.addEventListener('DOMContentLoaded', function () {
    var b = document.getElementById('lang'), t = document.getElementById('theme');
    if (b) b.onclick = function () { H.lang = L() === 'ja' ? 'en' : 'ja'; try { localStorage.setItem('sp-lang', H.lang); } catch (e) {} labels(); };
    t.onclick = function () { H.dataset.theme = H.dataset.theme === 'light' ? 'dark' : 'light';
      try { localStorage.setItem('sp-theme', H.dataset.theme); } catch (e) {} labels(); };
    // links to other sites open in a new tab, marked by an icon on their left
    function ext(a) {
      if (!/^https?:/.test(a.getAttribute('href') || '') || a.host === location.host) return;
      a.target = '_blank'; a.rel = 'noopener';
      if (!a.classList.contains('gh')) a.classList.add('ext');
    }
    document.querySelectorAll('a[href]').forEach(ext);
    // links that the page scripts add or retarget later
    new MutationObserver(function (ms) {
      ms.forEach(function (m) {
        if (m.type === 'attributes') { if (m.target.tagName === 'A') ext(m.target); return; }
        m.addedNodes.forEach(function (n) { if (n.nodeType !== 1) return; if (n.tagName === 'A') ext(n); n.querySelectorAll && n.querySelectorAll('a[href]').forEach(ext); });
      });
    }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['href'] });
    // preview only: build-stamp.txt exists there; when it changes, the page offers a reload (the release has no stamp)
    (function () {
      var first = null;
      function check() {
        fetch('build-stamp.txt', { cache: 'no-store' }).then(function (r) { if (!r.ok) throw 0; return r.text(); }).then(function (v) {
          if (first === null) first = v;
          else if (v !== first && !document.getElementById('rebuilt')) {
            var b = document.createElement('button'); b.id = 'rebuilt'; b.type = 'button';
            b.textContent = L() === 'ja' ? 'サイトが更新された — 読み込み直す' : 'The site was rebuilt — reload';
            b.onclick = function () { location.reload(); }; document.body.appendChild(b);
          }
          setTimeout(check, 15000);
        }).catch(function () {});
      }
      check();
    })();
    document.querySelectorAll('[data-filterbar]').forEach(function (bar) {
      var tb = document.getElementById(bar.getAttribute('data-filterbar'));
      var cnt = bar.querySelector('.count'), ctl = Array.from(bar.querySelectorAll('[data-key]'));
      var heads = Array.from(tb.closest('table').querySelectorAll('th.sort'));
      var original = Array.from(tb.querySelectorAll('tr.r'));
      var sortKey = '', direction = 'a';
      function apply() {
        var n = 0;
        original.forEach(function (tr) {
          var ok = ctl.every(function (c) {
            var k = c.dataset.key, v = c.type === 'checkbox' ? (c.checked ? '1' : '') : c.value.trim();
            if (!v) return true;
            if (k === 'q') return tr.textContent.toLowerCase().indexOf(v.toLowerCase()) >= 0;
            if (k === 'nmin') return +tr.dataset.n >= +v;
            if (k === 'nmax') return +tr.dataset.n <= +v;
            return (tr.dataset[k] || '') === v;
          });
          if (ok) n++;
          tr.hidden = !ok;
          var x = tr.nextElementSibling;
          if (x && x.classList.contains('x')) x.hidden = !ok || !tr.classList.contains('open');
        });
        if (cnt) cnt.textContent = n + ' / ' + original.length;
      }
      function sort() {
        var pairs = original.map(function (tr) { var x = tr.nextElementSibling; return [tr, x && x.classList.contains('x') ? x : null]; });
        if (sortKey) pairs.sort(function (a, b) {
          var p = a[0].dataset[sortKey], q = b[0].dataset[sortKey];
          var c = (sortKey === 'n' || sortKey === 'v') ? Number(p) - Number(q) : String(p).localeCompare(String(q));
          return direction === 'a' ? c : -c;
        });
        pairs.forEach(function (pr) { tb.appendChild(pr[0]); if (pr[1]) tb.appendChild(pr[1]); });
        heads.forEach(function (th) { th.setAttribute('aria-sort', th.dataset.sort === sortKey ? (direction === 'a' ? 'ascending' : 'descending') : 'none'); });
      }
      function save() {
        var u = new URL(location.href);
        ctl.forEach(function (c) {
          var v = c.type === 'checkbox' ? (c.checked ? '1' : '0') : c.value.trim();
          var def = c.type === 'checkbox' ? (c.defaultChecked ? '1' : '0') : '';
          if (v === def) u.searchParams.delete(c.dataset.key); else u.searchParams.set(c.dataset.key, v);
        });
        if (sortKey) { u.searchParams.set('sort', sortKey); u.searchParams.set('dir', direction); }
        else { u.searchParams.delete('sort'); u.searchParams.delete('dir'); }
        if (u.href !== location.href) history.pushState(null, '', u);
      }
      function restore() {
        var p = new URL(location.href).searchParams;
        ctl.forEach(function (c) {
          if (c.type === 'checkbox') c.checked = p.has(c.dataset.key) ? p.get(c.dataset.key) !== '0' : c.defaultChecked;
          else { c.value = p.get(c.dataset.key) || ''; if (c.tagName === 'SELECT' && c.selectedIndex < 0) c.value = ''; }
        });
        sortKey = heads.some(function (th) { return th.dataset.sort === p.get('sort'); }) ? p.get('sort') : '';
        direction = p.get('dir') === 'd' ? 'd' : 'a'; sort(); apply();
      }
      function changed() { apply(); save(); }
      bar.addEventListener('input', changed); bar.addEventListener('change', changed);
      heads.forEach(function (th) {
        th.tabIndex = 0;
        function run() { direction = sortKey === th.dataset.sort && direction === 'a' ? 'd' : 'a'; sortKey = th.dataset.sort; sort(); save(); }
        th.addEventListener('click', run);
        th.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); run(); } });
      });
      window.addEventListener('popstate', restore); restore();
    });
    document.querySelectorAll('tr.r').forEach(function (tr) {
      var x = tr.nextElementSibling;
      if (!x || !x.classList.contains('x')) return;
      tr.tabIndex = 0; tr.setAttribute('aria-expanded', 'false');
      function tog(e) {
        if (e.target.closest('a')) return;
        tr.classList.toggle('open'); x.hidden = !tr.classList.contains('open');
        tr.setAttribute('aria-expanded', String(!x.hidden));
      }
      tr.addEventListener('click', tog);
      tr.addEventListener('keydown', function (e) { if (e.target === tr && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); tog(e); } });
    });
    labels();
  });
})();
