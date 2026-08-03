/* Suits AI — shared nav + footer injection, routing, mobile menu.
   Every page gets an identical, correctly-linked nav/footer from one source. */
(function () {
  var MONO =
    '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.1">' +
    '<path d="M20 2 L35 11 V29 L20 38 L5 29 V11 Z"/>' +
    '<text x="20" y="26" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="18" fill="currentColor" stroke="none">S</text></svg>';

  var MOON = '<svg class="moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
  var SUN  = '<svg class="sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>';

  var LEFT = [
    { label: "Home",     href: "index.html" },
    { label: "Practice", href: "practice.html" },
    { label: "Process",  href: "process.html" },
    { label: "Accuracy", href: "accuracy.html" }
  ];
  var RIGHT = [
    { label: "Privacy", href: "privacy.html" },
    { label: "Terms",   href: "disclaimer.html" }
  ];

  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  if (here === "") here = "index.html";

  function linkHTML(item) {
    var active = item.href.toLowerCase() === here ? " is-active" : "";
    return '<a class="link' + active + '" href="' + item.href + '">' + item.label + '</a>';
  }

  function buildNav(variant) {
    var toggle = '<button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle light or dark mode">' + MOON + SUN + '</button>';
    var burger = '<button class="nav-burger" onclick="toggleMenu()" aria-label="Open menu">' +
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>';

    var mobileLinks = LEFT.concat([{ label: "———", href: "" }]).concat(RIGHT)
      .map(function (i) { return i.href ? '<a href="' + i.href + '">' + i.label + '</a>' : '<div class="sep"></div>'; })
      .join("") + '<div class="sep"></div><a href="chat.html">Sign in ↗</a>';

    return '' +
      '<nav class="nav ' + (variant === "over" ? "over" : "") + '">' +
        '<div class="nav-inner">' +
          '<div class="nav-group left">' + LEFT.map(linkHTML).join("") + '</div>' +
          '<a class="monogram" href="index.html" aria-label="Suits AI home">' + MONO + '</a>' +
          '<div class="nav-group right">' + RIGHT.map(linkHTML).join("") + toggle +
            '<a class="signin" href="chat.html">Sign in <span>&#8599;</span></a>' + burger +
          '</div>' +
        '</div>' +
        '<div class="nav-mobile hide" id="navMobile">' + mobileLinks + '</div>' +
      '</nav>';
  }

  function buildFooter() {
    return '' +
      '<footer><div class="wrap">' +
        '<div class="foot-top">' +
          '<div class="foot-links">' +
            '<a href="chat.html">Open the app</a><a href="practice.html">Practice</a>' +
            '<a href="process.html">Process</a><a href="accuracy.html">Accuracy</a>' +
            '<a href="privacy.html">Privacy</a><a href="disclaimer.html">Terms</a>' +
          '</div>' +
          '<div class="socials"><a href="#" aria-label="LinkedIn">in</a><a href="#" aria-label="X">x</a><a href="#" aria-label="Instagram">ig</a></div>' +
        '</div>' +
        '<p class="foot-disclaimer"><b>Important:</b> Suits AI is an automated information and news service. ' +
        'It does not provide legal advice, does not practice law, and is not a law firm. Using it does not create an attorney–client relationship. ' +
        'Information may be inaccurate, incomplete, or out of date, and targets only ~95% accuracy. Do not rely on it as a substitute for a licensed attorney. ' +
        'DaarLabs and DaarForce accept no liability for decisions made based on this service.</p>' +
        '<div class="foot-bottom">' +
          '<span>© 2026 DaarLabs. A DaarLabs &amp; DaarForce product.</span>' +
          '<span>Not affiliated with the television program “Suits” or its rights holders.</span>' +
        '</div>' +
      '</div></footer>';
  }

  window.toggleMenu = function () {
    var m = document.getElementById("navMobile");
    if (m) m.classList.toggle("hide");
  };

  function mount() {
    var navHost = document.getElementById("site-nav");
    if (navHost) navHost.outerHTML = buildNav(navHost.getAttribute("data-variant") || "solid");
    var footHost = document.getElementById("site-footer");
    if (footHost) footHost.outerHTML = buildFooter();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
