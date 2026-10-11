(function () {
  var btn = document.getElementById('toTop');
  if (!btn) return;
  var toggle = function () {
    btn.classList.toggle('is-visible', window.scrollY > 400);
  };
  window.addEventListener('scroll', toggle, { passive: true });
  toggle();
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

// Shares the 'theme' key with shubham-lonkar.github.io (same origin), so the choice carries over.
(function () {
  var root = document.documentElement;
  var btn = document.getElementById('themeToggle');
  var icon = document.getElementById('themeToggleIcon');
  if (!btn) return;

  var applyTheme = function (theme) {
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme');
    }
    btn.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
    btn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
    icon.innerHTML = theme === 'light' ? '&#9790;' : '&#9728;';
  };

  applyTheme(root.getAttribute('data-theme') === 'light' ? 'light' : 'dark');

  btn.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    applyTheme(next);
    try {
      localStorage.setItem('theme', next);
    } catch (e) {}
  });
})();

// Full-screen viewer. Without JS, each thumbnail still links to its full-size image.
(function () {
  var dialog = document.getElementById('lightbox');
  var items = Array.prototype.slice.call(document.querySelectorAll('.gallery-item'));
  if (!dialog || !dialog.showModal || !items.length) return;

  var img = document.getElementById('lightboxImg');
  var count = document.getElementById('lightboxCount');
  var gear = document.getElementById('lightboxGear');
  var exposure = document.getElementById('lightboxExposure');
  var current = 0;

  var preload = function (i) {
    var item = items[(i + items.length) % items.length];
    var pre = new Image();
    pre.sizes = '100vw';
    pre.srcset = item.dataset.srcset;
  };

  var show = function (i) {
    current = (i + items.length) % items.length;
    var item = items[current];
    var thumb = item.querySelector('img');
    img.removeAttribute('srcset');
    img.src = thumb.currentSrc || thumb.src; // already loaded, so something shows instantly
    img.srcset = item.dataset.srcset;
    img.alt = thumb.alt;
    count.textContent = (current + 1) + ' / ' + items.length;
    gear.textContent = [item.dataset.camera, item.dataset.lens].filter(Boolean).join(' · ');
    exposure.textContent = item.dataset.exposure;
    preload(current + 1);
    preload(current - 1);
  };

  items.forEach(function (item, i) {
    item.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
      e.preventDefault();
      show(i);
      dialog.showModal();
    });
  });

  document.getElementById('lightboxPrev').addEventListener('click', function () { show(current - 1); });
  document.getElementById('lightboxNext').addEventListener('click', function () { show(current + 1); });
  document.getElementById('lightboxClose').addEventListener('click', function () { dialog.close(); });

  dialog.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') show(current - 1);
    if (e.key === 'ArrowRight') show(current + 1);
  });

  // Clicking the empty space around the photo closes the viewer.
  dialog.addEventListener('click', function (e) {
    if (e.target === dialog || e.target.classList.contains('lightbox-figure')) dialog.close();
  });

  dialog.addEventListener('close', function () {
    items[current].focus({ preventScroll: true });
  });

  var startX = null;
  var startY = null;
  dialog.addEventListener('touchstart', function (e) {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  }, { passive: true });
  dialog.addEventListener('touchend', function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    var dy = e.changedTouches[0].clientY - startY;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
    startX = null;
  }, { passive: true });
})();
