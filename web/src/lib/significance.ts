// p-values for the orthographic similarity (see METHODS.md, section 6)
export const fmtP = (v: number | null | undefined) =>
  v == null ? "–" : v < 0.001 ? "< 0,001" : v.toFixed(3).replace(".", ",");

export const SIMILARITY_HELP =
  "Likhet = cosinuslikhet (0–1) mellan inskriftens ortografiska profil och ristarens medelprofil. " +
  "p = andelen av andra ristares inskrifter som är minst lika lika ristarens profil; justerat p tar hänsyn till " +
  "att den mest lika av alla ristare väljs (Bonferroni). Ett lågt justerat p betyder att likheten är ovanligt hög.";
