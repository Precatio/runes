// English chosen earlier: keep the page hidden until it is translated (at most 3 s), so that the Swedish original does
// not flash by (src/components/LanguageContext.tsx); a Swedish article stays hidden until its English edition is shown
// instead. Loaded before hydration from app/layout.tsx. The English editions (/en/…) are rendered in English for every
// reader, so they are never hidden.
// ?sv on a Swedish page is "Läs på svenska" from an English edition opened in a new tab (components/LanguageToggle.tsx,
// SwedishEditionLink): it makes Swedish the reader's choice, so that the page is not forwarded back to English, and is
// then taken off the address, so that a copied link does not carry it.
try {
  var d = document.documentElement, q = location.search;
  if (/^\/en(\/|$)/.test(location.pathname)) d.lang = "en";
  else if (/[?&]sv(=[^&]*)?(&|$)/.test(q)) {
    try { localStorage.setItem("vitki_lang", "sv"); } catch (e) {}
    var rest = q.replace(/([?&])sv(=[^&]*)?(&|$)/, function (m, a, v, end) { return end ? a : ""; });
    history.replaceState(history.state, "", location.pathname + rest + location.hash);
  } else if (localStorage.getItem("vitki_lang") === "en") {
    d.lang = "en";
    d.classList.add("i18n-pending");
    setTimeout(function () { d.classList.remove("i18n-pending"); }, 3000);
  }
} catch (e) {}
