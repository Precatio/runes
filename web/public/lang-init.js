// English chosen earlier: keep the page hidden until it is translated (at most 3 s), so that the Swedish original does
// not flash by (src/components/LanguageContext.tsx). Loaded before hydration from app/layout.tsx. The English edition
// of an article (/en/…) is English for every reader.
try {
  var d = document.documentElement;
  if (/^\/en(\/|$)/.test(location.pathname)) d.lang = "en";
  if (localStorage.getItem("vitki_lang") === "en") {
    d.lang = "en";
    d.classList.add("i18n-pending");
    setTimeout(function () { d.classList.remove("i18n-pending"); }, 3000);
  }
} catch (e) {}
