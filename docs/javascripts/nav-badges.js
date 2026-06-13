// Pin a notification-style count badge on left-nav items that gained NEW entries in the
// latest update (data from nav-counts.js, regenerated each build by scripts/gen_catalog.py).
// Matching uses the link's RESOLVED href (a.href), so it works regardless of the relative
// form the nav uses on any given page, the EN/JP locale prefix, or the Pages repo subpath.
(function () {
  function decorate() {
    var counts = window.NAV_NEW_COUNTS || {};
    // Longest keys first so a task path never matches its area's "index.html" key.
    var keys = Object.keys(counts).sort(function (a, b) { return b.length - a.length; });
    if (!keys.length) return;
    // ONLY the left navigation (.md-nav--primary). The right-hand Table of Contents is
    // .md-nav--secondary and its links share the task page's path, which would otherwise
    // make every section heading inherit the task's count.
    document.querySelectorAll(".md-nav--primary a.md-nav__link[href]").forEach(function (a) {
      var path;
      try { path = new URL(a.href).pathname; } catch (e) { return; }
      for (var i = 0; i < keys.length; i++) {
        if (path.endsWith(keys[i])) {
          // Anchor to the full-width LINK ROW (the nested container, else the leaf link),
          // not the whole <li> — an expanded <li> is tall, which drops the badge. The row is
          // one line, so top:50% centres the badge on the label at any depth, and its right
          // edge is the same column-wide for every item.
          var row = a.closest(".md-nav__container") || a;
          if (row.querySelector(":scope > .nav-badge")) break;
          row.style.position = "relative";
          a.classList.add("nav-badged");   // reserves right padding so a long label doesn't run under the badge
          var b = document.createElement("span");
          b.className = "nav-badge";
          b.textContent = counts[keys[i]];
          b.title = counts[keys[i]] + " new this update";
          row.appendChild(b);
          break;
        }
      }
    });
  }
  document.addEventListener("DOMContentLoaded", decorate);
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(decorate);   // Material instant navigation
  }
})();
