// English chosen earlier: keep the page hidden until it is translated (at most 3 s), so that the Swedish original does
// not flash by (src/components/LanguageContext.tsx). Loaded before hydration from app/layout.tsx.
try {
  if (localStorage.getItem("vitki_lang") === "en") {
    var d = document.documentElement;
    d.lang = "en";
    d.classList.add("i18n-pending");
    setTimeout(function () { d.classList.remove("i18n-pending"); }, 3000);
  }
} catch (e) {}
