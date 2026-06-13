// Open every external content link (cards: title, image, arXiv/GitHub/Project/...) in a new tab.
// Internal nav/TOC links (same host) are left alone.
(function () {
  function mark() {
    var host = location.hostname;
    document.querySelectorAll(".md-content a[href]").forEach(function (a) {
      try {
        var u = new URL(a.href, location.href);
        if ((u.protocol === "http:" || u.protocol === "https:") && u.hostname && u.hostname !== host) {
          a.target = "_blank";
          a.rel = "noopener noreferrer";
        }
      } catch (e) { /* ignore malformed hrefs */ }
    });
  }
  // Plain load + Material's instant-navigation observable (if present).
  document.addEventListener("DOMContentLoaded", mark);
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(mark);
  }
})();
