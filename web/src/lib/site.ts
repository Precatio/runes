// The site's public address and name, for metadata, the sitemap and structured data (override with NEXT_PUBLIC_SITE_URL)
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "https://vitkirunor.se").replace(/\/$/, "");
export const SITE_NAME = "Vitki";
export const SITE_DESCRIPTION =
  "Utforska Sveriges runstenar: mönsterkarta, ristare, stilgrupper, Samnordisk runtextdatabas, 3D-analys av huggspår " +
  "och statistik i R. En öppen och fri forskningsplattform för runologi och runinskrifter.";
export const KEYWORDS = [
  "runstenar", "runsten", "runinskrifter", "runor", "runologi", "runforskning", "vikingatid", "Rundata",
  "Samnordisk runtextdatabas", "runristare", "Öpir", "stilgrupper", "Gräslund", "runstenskarta", "kristnandet",
  "fornlämningar", "3D-skanning", "huggspår", "runestones", "runic inscriptions", "Viking Age", "runology",
];
