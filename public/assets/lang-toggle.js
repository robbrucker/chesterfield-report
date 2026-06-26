/* The Chesterfield Report - EN/ES language toggle
 * Vanilla JS, no dependencies. Loaded with: <script src="/assets/lang-toggle.js" defer></script>
 */
(function () {
  "use strict";

  // Every reader-facing page has a Spanish version ("/es"+path), except these
  // internal/non-content pages (kept in sync with render._ES_DENY).
  var ES_DENY = ["/404.html", "/offline.html", "/drafts.html", "/preview.html"];

  // --- cookie helpers -------------------------------------------------------
  function readCookie(name) {
    var prefix = name + "=";
    var parts = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(prefix) === 0) {
        return decodeURIComponent(c.substring(prefix.length));
      }
    }
    return null;
  }

  function writeLangCookie(value) {
    var oneYear = 60 * 60 * 24 * 365;
    document.cookie =
      "cr_lang=" + encodeURIComponent(value) +
      "; max-age=" + oneYear +
      "; path=/; SameSite=Lax";
  }

  // --- path helpers ---------------------------------------------------------
  function isSpanishPath(path) {
    return path === "/es" || path.indexOf("/es/") === 0;
  }

  // Normalize an EN path so "/index.html" is treated as the homepage "/".
  function normalizeEnPath(path) {
    if (path === "/index.html") return "/";
    return path;
  }

  // Given an EN path, return its EN-equivalent path stripped of the /es prefix
  // logic. (Input is already an EN path here.)
  function enPathFromEs(path) {
    if (path === "/es" || path === "/es/") return "/";
    if (path.indexOf("/es/") === 0) {
      return path.substring(3); // drop "/es", keep the rest starting at "/"
    }
    return path;
  }

  // true for any reader-facing page (homepage, .html pages, stories, topics),
  // except the internal pages in ES_DENY. Operates on the EN-normalized path.
  function hasRealSpanish(path) {
    var p = normalizeEnPath(path);
    if (p === "/") return true;
    for (var i = 0; i < ES_DENY.length; i++) {
      if (p === ES_DENY[i]) return false;
    }
    if (/\.html$/.test(p)) return true;
    if (p === "/topics/" || p.indexOf("/topics/") === 0) return true;
    if (p.indexOf("/story/") === 0) return true;
    return false;
  }

  // Compute the ES counterpart for an EN path. Falls back to "/es/" when the
  // page has no real Spanish version.
  function esCounterpartFromEn(enPath) {
    var p = normalizeEnPath(enPath);
    if (p === "/") return "/es/";
    if (hasRealSpanish(p)) return "/es" + p;
    return "/es/";
  }

  // --- main -----------------------------------------------------------------
  var rawPath = location.pathname || "/";
  var isSpanish = isSpanishPath(rawPath);

  // The EN-normalized path for the current page (used for hasRealSpanish, etc).
  var enPath = isSpanish ? enPathFromEs(rawPath) : normalizeEnPath(rawPath);

  // Compute counterpart URLs.
  var enUrl, esUrl;
  if (isSpanish) {
    enUrl = enPath;                 // strip /es
    esUrl = rawPath;                // already Spanish; ES points at itself
  } else {
    enUrl = enPath;                 // already English; EN points at itself
    esUrl = esCounterpartFromEn(enPath);
  }

  // --- wire up the toggle ---------------------------------------------------
  function setupToggles() {
    var toggles = document.querySelectorAll(".lang-toggle");
    if (!toggles || !toggles.length) return;

    for (var i = 0; i < toggles.length; i++) {
      var toggle = toggles[i];
      var enLink = toggle.querySelector('a.lang-link[hreflang="en"]');
      var esLink = toggle.querySelector('a.lang-link[hreflang="es"]');

      if (enLink) {
        enLink.setAttribute("href", enUrl);
        if (isSpanish) {
          enLink.classList.remove("is-current");
        } else {
          enLink.classList.add("is-current");
        }
        enLink.addEventListener("click", function () {
          writeLangCookie("en");
        });
      }

      if (esLink) {
        esLink.setAttribute("href", esUrl);
        if (isSpanish) {
          esLink.classList.add("is-current");
        } else {
          esLink.classList.remove("is-current");
        }
        esLink.addEventListener("click", function () {
          writeLangCookie("es");
        });
      }
    }
  }

  setupToggles();

  // --- preference auto-restore ---------------------------------------------
  // If we're on an English page but the saved preference is Spanish, and a real
  // Spanish version exists, redirect to it. Guard against loops.
  if (!isSpanish && readCookie("cr_lang") === "es" && hasRealSpanish(enPath)) {
    var target = esCounterpartFromEn(enPath);
    if (target !== rawPath && !isSpanishPath(rawPath)) {
      location.replace(target);
    }
  }
})();
