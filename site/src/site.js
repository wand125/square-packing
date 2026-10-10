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
    b.onclick = function () { H.lang = L() === 'ja' ? 'en' : 'ja'; try { localStorage.setItem('sp-lang', H.lang); } catch (e) {} labels(); };
    t.onclick = function () { H.dataset.theme = H.dataset.theme === 'light' ? 'dark' : 'light';
      try { localStorage.setItem('sp-theme', H.dataset.theme); } catch (e) {} labels(); };
    // generic filterable tables: <table data-filter> rows carry data-* keys; controls carry data-key
    document.querySelectorAll('[data-filterbar]').forEach(function (bar) {
      var tb = document.getElementById(bar.getAttribute('data-filterbar'));
      var cnt = bar.querySelector('.count');
      function apply() {
        var ctl = bar.querySelectorAll('[data-key]'), n = 0, tot = 0;
        tb.querySelectorAll('tr.r').forEach(function (tr) {
          var ok = true;
          ctl.forEach(function (c) {
            var k = c.getAttribute('data-key'), v = c.type === 'checkbox' ? (c.checked ? '1' : '') : c.value.trim();
            if (!v) return;
            if (k === 'q') { if (tr.textContent.toLowerCase().indexOf(v.toLowerCase()) < 0) ok = false; }
            else if (k === 'nmin') { if (+tr.dataset.n < +v) ok = false; }
            else if (k === 'nmax') { if (+tr.dataset.n > +v) ok = false; }
            else if ((tr.dataset[k] || '') !== v) ok = false;
          });
          tot++; if (ok) n++;
          tr.hidden = !ok;
          var x = tr.nextElementSibling; if (x && x.classList.contains('x')) x.hidden = !ok || !tr.classList.contains('open');
        });
        if (cnt) cnt.textContent = n + ' / ' + tot;
      }
      bar.addEventListener('input', apply); bar.addEventListener('change', apply); apply();
    });
    // expandable rows
    document.querySelectorAll('tr.r').forEach(function (tr) {
      var x = tr.nextElementSibling;
      if (!x || !x.classList.contains('x')) return;
      tr.tabIndex = 0;
      function tog(e) { if (e.target.closest('a')) return; tr.classList.toggle('open'); x.hidden = !tr.classList.contains('open'); }
      tr.addEventListener('click', tog);
      tr.addEventListener('keydown', function (e) { if (e.key === 'Enter') tog(e); });
    });
    // sortable columns
    document.querySelectorAll('th.sort').forEach(function (th) {
      th.addEventListener('click', function () {
        var tb = th.closest('table').tBodies[0], key = th.getAttribute('data-sort'), dir = th.dataset.dir === 'a' ? 'd' : 'a';
        th.dataset.dir = dir;
        var pairs = [];
        tb.querySelectorAll('tr.r').forEach(function (tr) { var x = tr.nextElementSibling; pairs.push([tr, x && x.classList.contains('x') ? x : null]); });
        pairs.sort(function (a, b) {
          var p = a[0].dataset[key], q = b[0].dataset[key], np = parseFloat(p), nq = parseFloat(q);
          var c = (!isNaN(np) && !isNaN(nq)) ? np - nq : String(p).localeCompare(String(q));
          return dir === 'a' ? c : -c;
        });
        pairs.forEach(function (pr) { tb.appendChild(pr[0]); if (pr[1]) tb.appendChild(pr[1]); });
      });
    });
    labels();
  });
})();
