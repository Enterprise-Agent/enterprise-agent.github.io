// Small behaviours for the page. Everything stays readable without this file.
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches || /[?&]static/.test(location.search);

  // The bar is clear over the title page and solid after it.
  var bar = document.getElementById('topbar');
  var ground = document.getElementById('hero-ground');
  function setBar() {
    var end = ground.getBoundingClientRect().bottom;
    bar.classList.toggle('solid', end < bar.offsetHeight + 8);
  }
  setBar();
  window.addEventListener('scroll', setBar, { passive: true });
  window.addEventListener('resize', setBar);

  // Sections ease in as they are reached. Without IntersectionObserver they are simply shown.
  var items = [].slice.call(document.querySelectorAll('[data-reveal]'));
  if (!reduce && 'IntersectionObserver' in window && !document.hidden) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    items.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.95) return;          // already on screen: leave it visible
      var sibs = el.parentElement ? [].slice.call(el.parentElement.children).filter(function (c) { return c.hasAttribute('data-reveal'); }) : [];
      el.style.setProperty('--d', Math.min(sibs.indexOf(el), 5) * 60 + 'ms');
      el.classList.add('reveal');
      io.observe(el);
    });
  }

  // The section in view is marked in the bar.
  var links = [].slice.call(document.querySelectorAll('.nav a'));
  var targets = links.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  if ('IntersectionObserver' in window) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a, i) { a.setAttribute('aria-current', targets[i] === e.target ? 'true' : 'false'); });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    targets.forEach(function (t) { if (t) seen.observe(t); });
  }

  // Pointing at an author marks the institutions, and the other way round.
  var people = document.getElementById('people');
  var authors = [].slice.call(people.querySelectorAll('.authors span'));
  var affils = [].slice.call(people.querySelectorAll('.affils li'));
  function mark(nums, source) {
    people.classList.add('linking');
    authors.forEach(function (a) {
      var mine = a.getAttribute('data-a').split(',');
      a.classList.toggle('on', a === source || (source.tagName === 'LI' && mine.indexOf(nums[0]) > -1));
    });
    affils.forEach(function (l) { l.classList.toggle('on', nums.indexOf(l.getAttribute('data-n')) > -1); });
  }
  function clear() {
    people.classList.remove('linking');
    authors.concat(affils).forEach(function (el) { el.classList.remove('on'); });
  }
  authors.forEach(function (a) {
    a.addEventListener('mouseenter', function () { mark(a.getAttribute('data-a').split(','), a); });
    a.addEventListener('mouseleave', clear);
  });
  affils.forEach(function (l) {
    l.addEventListener('mouseenter', function () { mark([l.getAttribute('data-n')], l); });
    l.addEventListener('mouseleave', clear);
  });

  // Pointing at a mark in the framework comparison brings out that framework's column.
  var cmp = document.querySelector('table.compare');
  if (cmp) {
    var marks = [].slice.call(cmp.querySelectorAll('[data-c]'));
    var point = function (c) {
      cmp.classList.toggle('pointing', c !== null);
      marks.forEach(function (m) { m.classList.toggle('hot', m.getAttribute('data-c') === c); });
    };
    cmp.addEventListener('mouseover', function (e) {
      var m = e.target.closest ? e.target.closest('[data-c]') : null;
      point(m ? m.getAttribute('data-c') : null);
    });
    cmp.addEventListener('mouseleave', function () { point(null); });
  }

  // A chart with one table body for each agent model shows one at a time, chosen with the buttons above it.
  [].slice.call(document.querySelectorAll('[data-sets]')).forEach(function (box) {
    var seg = box.querySelector('.seg');
    var sets = [].slice.call(box.querySelectorAll('[data-set]'));
    if (!seg || sets.length < 2) return;
    var btns = [].slice.call(seg.querySelectorAll('button'));
    var holder = box.querySelector('.chart-scroll');
    var show = function (k) {
      sets.forEach(function (t) { t.hidden = t.getAttribute('data-set') !== k; });
      btns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-show') === k ? 'true' : 'false'); });
    };
    seg.hidden = false;
    box.classList.add('toggled');
    var tallest = 0;                      // keep the height of the tallest set, so the page does not jump
    sets.forEach(function (t) { show(t.getAttribute('data-set')); tallest = Math.max(tallest, holder.offsetHeight); });
    if (tallest) holder.style.minHeight = tallest + 'px';
    show('0');
    btns.forEach(function (b) { b.addEventListener('click', function () { show(b.getAttribute('data-show')); }); });
  });

  // A figure opens large in place: a copy of its SVG, so it stays sharp at any size.
  var viewer = document.getElementById('viewer');
  if (viewer && viewer.showModal) {
    var stage = viewer.querySelector('.viewer-inner');
    var open = function (box) {
      var svg = box.querySelector('svg');
      if (!svg) return;
      stage.innerHTML = '';
      stage.appendChild(svg.cloneNode(true));
      viewer.showModal();
    };
    document.addEventListener('click', function (e) {
      var box = e.target.closest ? e.target.closest('[data-zoom]') : null;
      if (box) open(box);
    });
    document.addEventListener('keydown', function (e) {
      if ((e.key === 'Enter' || e.key === ' ') && document.activeElement && document.activeElement.hasAttribute('data-zoom')) {
        e.preventDefault(); open(document.activeElement);
      }
    });
    viewer.addEventListener('click', function () { viewer.close(); });
  }

  // Copy the BibTeX entry.
  [].slice.call(document.querySelectorAll('[data-copy]')).forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = document.getElementById(btn.getAttribute('data-copy')).textContent;
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1600); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { select(); });
      } else { select(); }
      function select() {
        var r = document.createRange(); r.selectNodeContents(document.getElementById(btn.getAttribute('data-copy')));
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      }
    });
  });
})();
