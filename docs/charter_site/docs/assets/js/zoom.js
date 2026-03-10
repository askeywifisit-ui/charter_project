// Enable click-to-zoom on documentation images (MkDocs Material).
// Requires medium-zoom loaded via mkdocs.yml extra_javascript.

(function () {
  function init() {
    if (!window.mediumZoom) return;

    // Main article content images
    window.mediumZoom("article img", {
      margin: 24,
      background: "#000000AA",
      scrollOffset: 64,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
