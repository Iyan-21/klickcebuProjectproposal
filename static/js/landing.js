// Cursor-reactive parallax for the landing page hero "glass lens" visual.
// Each element with [data-depth] drifts slightly toward/away from the cursor,
// with larger depth values moving further, giving a subtle layered-glass feel.
(function () {
  var hero = document.getElementById('hero');
  if (!hero) return;

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) return;

  var layers = Array.prototype.slice.call(hero.querySelectorAll('[data-depth]')).map(function (el) {
    return { el: el, depth: parseFloat(el.getAttribute('data-depth')) || 40, tx: 0, ty: 0, cx: 0, cy: 0 };
  });
  if (!layers.length) return;

  var targetX = 0, targetY = 0;
  var raf = null;

  function onMove(e) {
    var rect = hero.getBoundingClientRect();
    var nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;   // -1..1
    var ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;   // -1..1
    targetX = Math.max(-1, Math.min(1, nx));
    targetY = Math.max(-1, Math.min(1, ny));
    if (!raf) raf = requestAnimationFrame(tick);
  }

  function onLeave() {
    targetX = 0;
    targetY = 0;
    if (!raf) raf = requestAnimationFrame(tick);
  }

  function tick() {
    var settled = true;
    layers.forEach(function (layer) {
      var wantX = targetX * (layer.depth * 0.38);
      var wantY = targetY * (layer.depth * 0.38);
      layer.cx += (wantX - layer.cx) * 0.16;
      layer.cy += (wantY - layer.cy) * 0.16;
      if (Math.abs(wantX - layer.cx) > 0.05 || Math.abs(wantY - layer.cy) > 0.05) settled = false;
      layer.el.style.transform = 'translate(' + layer.cx.toFixed(2) + 'px, ' + layer.cy.toFixed(2) + 'px)';
    });
    if (!settled) {
      raf = requestAnimationFrame(tick);
    } else {
      raf = null;
    }
  }

  hero.addEventListener('mousemove', onMove);
  hero.addEventListener('mouseleave', onLeave);
})();