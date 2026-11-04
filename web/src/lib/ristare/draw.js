// Ritkoden för ristarsidan (app/(app)/ristare/page.tsx och artefakten "Ristarna en i taget"): fingeravtryck, heatmap sten
// mot drag, kärna/spann/ytterkant, karta, profilen mot attribueringsmodellen, likhet mellan stenarna, listor och metod.
// Data: utdata/ristare/sida_data.py (profiler ur r/carver_profile.R, förslag ur r/attribution_candidates.R, provningen ur
// r/attribution_audit.R). Varje figur tar bredden från sin panel, så att ytan används; renderCarver ritar om allt.

const NS = "http://www.w3.org/2000/svg";
export const KL = ["kärna", "inom spannet", "ytterkant", "som grannarna", "kan inte avgöras"];
const KCOL = { "kärna": "var(--rp-rust)", "inom spannet": "var(--rp-rust2)", "ytterkant": "var(--rp-sand)", "som grannarna": "var(--rp-slate)", "kan inte avgöras": "var(--rp-empty)" };
const SETS = ["signerad", "signerad utanför profilen", "attribuerad", "osäker"];
const SETLABEL = { "signerad": "Signerade", "signerad utanför profilen": "Signerade, utanför profilen", "attribuerad": "Attribuerade", "osäker": "Delad eller osäker", "granne": "Grannstenar" };
export const VARIANTS = { med: "Standardprofil", utan_rodballe: "Utan Röd-Balles två (Vs 15, Vs 24)" };
const fmt = (x, d = 2) => x == null ? "–" : x.toFixed(d).replace(".", ",").replace("-", "−");
const pct = x => x == null ? "–" : Math.round(x * 100) + " %";
const esc = s => String(s ?? "").replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
export const slug = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

/** Grannstenarna kommer kompakt ([id, plats, socken, lat, lon, stil, värde, antal drag, klass]); en gång per sida. */
export function preparePage(PAGE) {
  if (PAGE._prepared) return PAGE;
  PAGE.carvers.forEach(c => Object.values(c.variants).forEach(v => {
    v.stones = v.stones.concat(v.nb.map(a => ({ id: a[0], place: a[1], parish: a[2], lat: a[3], lon: a[4], style: a[5], score: a[6], n: a[7], klass: a[8], set: "granne" })));
  }));
  PAGE._prepared = true;
  return PAGE;
}

/** Ritar ristare nummer C (variant V) i root. setVariant(v) anropas när en variantknapp trycks. */
export function renderCarver(root, PAGE, AUDIT, C, V, setVariant, state = {}) {
  const $ = id => root.querySelector("#" + id);
  const carver = PAGE.carvers[C], WHO = carver.name;
  const D = carver.variants[V] || carver.variants.med;
  const tip = root.querySelector(".rp-tip");

  function el(tag, attrs = {}, parent) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  }
  const txt = (parent, x, y, s, attrs = {}) => { const t = el("text", { x, y, ...attrs }, parent); t.textContent = s; return t; };
  const size = (svg, W, H) => { svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("width", W); svg.setAttribute("height", H); };
  const avail = (svg, min = 320) => Math.max(min, Math.floor((svg.parentElement && svg.parentElement.clientWidth) || 1100) - 4);
  function moveTip(ev) {
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + w > innerWidth - 8) x = ev.clientX - w - 14;
    if (y + h > innerHeight - 8) y = ev.clientY - h - 14;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  }
  function hover(node, html) {
    node.addEventListener("mouseenter", ev => { tip.innerHTML = html(); tip.hidden = false; moveTip(ev); });
    node.addEventListener("mousemove", moveTip);
    node.addEventListener("mouseleave", () => { tip.hidden = true; });
  }
  const stoneTip = s => `<b>${esc(s.id)}</b> · <span translate="no">${esc(s.place)}${s.parish ? ", " + esc(s.parish) : ""}</span><br>${SETLABEL[s.set]} · ${esc(s.style || "ingen stilgrupp")}${s.material ? " · " + esc(s.material) : ""}<br>` +
    `Värde ${fmt(s.score)}${s.follows != null ? " · följer " + pct(s.follows) : ""} · ${s.n} avläsbara drag<br><span class="rp-dim">${s.klass}</span>` +
    (s.modell != null ? `<br>Modellen: ${pct(s.modell)} ${esc(WHO)}` : "");
  const own = () => D.stones.filter(s => s.set !== "granne");
  const ordered = () => own().slice().sort((a, b) => SETS.indexOf(a.set) - SETS.indexOf(b.set) || (b.score ?? -9) - (a.score ?? -9));
  const inProfile = s => D.profil === "signerade" ? s.set === "signerad" : (s.set === "signerad" || s.set === "attribuerad");
  const flagged = s => (inProfile(s) && s.klass === "som grannarna") || (WHO === "Balle" && (s.id === "Vs 15" || s.id === "Vs 24"));
  const pillBg = k => `color-mix(in oklab, ${KCOL[k]} 25%, white)`;

  function header() {
    const n = D.n, sg = n["signerad"] || 0, at = n["attribuerad"] || 0, us = n["osäker"] || 0;
    $("rp-h1").textContent = `${WHO} – vilka stenar följer hans drag?`;
    const per = D.period && D.period[0] != null ? ` Hans stenar dateras efter stil till omkring ${D.period[0]}–${D.period[1]}.` : "";
    $("rp-lede").textContent =
      `${WHO} har ${sg + at} stenar med säker ristare i Rundata (${sg} signerade, ${at} attribuerade) och ${us} som han delar med någon annan eller som är osäkra.${per} ` +
      `Här jämförs hans stenar med samtida grannstenar inom ${D.km} km, och varje sten prövas: ligger den mitt i hans sätt att skriva, i ytterkanten eller bland grannarna?`;
    $("rp-warn").innerHTML = D.profil === "signerade" ? "" :
      `<div class="rp-warnbox"><b>Profilen bygger på attribuerade stenar.</b> ${esc(WHO)} har ${sg === 0 ? "inga signerade stenar" : sg >= 5 ? sg + " signerade stenar, men de skiljer sig från grannarna i färre än åtta drag" : "bara " + sg + " signerade stenar, färre än fem"}. Profilen byggs därför av alla hans säkra stenar, också dem som forskningen tillskrivit honom efter stil och stavning. Sidan visar då hur samstämmig den gruppen är och vilka stenar som skiljer sig, men den prövar inte attribueringarna mot ett facit.</div>`;
    const meas = own().filter(s => s.klass !== "kan inte avgöras" && !inProfile(s) && s.set === "attribuerad");
    const inner = meas.filter(s => s.klass === "kärna" || s.klass === "inom spannet").length;
    const F = carver.forslag;
    const items = [[D.profil === "signerade" ? sg : sg + at, D.profil === "signerade" ? "signerade stenar bygger profilen" : "säkra stenar bygger profilen"],
      [D.traits.length, "drag i fingeravtrycket"]];
    if (D.profil === "signerade") items.push([inner + " av " + meas.length, "mätbara attribuerade i kärnan eller inom spannet"]);
    if (F && F.rows.length) items.push([F.rows.length, "stenar utan ristare som appen tror är hans"]);
    items.push([n["granne"] || 0, "grannstenar att jämföra med"]);
    $("rp-facts").innerHTML = items.map(([b, s]) => `<div class="rp-fact"><b>${b}</b><span>${s}</span></div>`).join("");
    const vs = Object.keys(carver.variants), box = $("rp-variants");
    box.hidden = vs.length < 2;
    box.innerHTML = vs.map(v => `<button type="button" data-v="${v}" aria-pressed="${v === V}">${VARIANTS[v] || v}</button>`).join("");
    box.querySelectorAll("button").forEach(b => b.addEventListener("click", () => setVariant(b.dataset.v)));
    $("rp-fp-note").textContent = D.profil === "signerade"
      ? `De drag där de signerade stenarna skiljer sig tydligast från grannarna: andelen hos ristaren (rost) mot andelen hos grannstenarna (grå). Överst det han gör oftare, nederst det han gör mer sällan.`
      : `De drag där ristarens stenar skiljer sig tydligast från grannarna: andelen hos ristaren (rost) mot andelen hos grannstenarna (grå). Överst det han gör oftare, nederst det han gör mer sällan.`;
    $("rp-map-note").textContent = `Ristarens stenar färgade efter klass; ring = signerad, romb = delad eller osäker; streckad rostring = sten som appen föreslår; små grå prickar är grannstenarna inom ${D.km} km. Streckade linjer är de gamla landens gränser där Vitki har dem.`;
    $("rp-nb-h").textContent = `Grannar som liknar ${WHO}`;
  }

  function suggestions() {
    const F = carver.forslag, rows = F ? F.rows : [], box = $("rp-sg");
    $("rp-sg-h").textContent = `Stenar som appen tror att ${WHO} ristade`;
    const inModel = AUDIT.q2.per_carver.some(r => r.carver === WHO);
    $("rp-sg-note").innerHTML = !inModel
      ? `${esc(WHO)} har färre än åtta säkra stenar och finns inte i attribueringsmodellen, så appen kan inte föreslå stenar åt honom än.`
      : `Runstenar utan säker ristare där Vitkis attribueringsmodell sätter ${esc(WHO)} främst. Procenten är omkalibrerade efter provningen mot de signerade stenarna, där modellen hade rätt först på ${pct(AUDIT.q1.top1[0])} av dem. ` +
        `Stenar där modellen är så osäker att det lika gärna kan vara en ristare den inte känner är bortsorterade${F && F.n_blocked ? ` (${F.n_blocked} stenar)` : ""}. ` +
        `Kolumnen <b>Profilen</b> visar hur stenen ligger mot fingeravtrycket nedan, en andra och delvis oberoende bedömning.`;
    if (!inModel) { box.innerHTML = ""; return; }
    if (!rows.length) { box.innerHTML = `<div class="rp-empty">Modellen sätter inte ${esc(WHO)} främst på någon sten utan ristare, utom där den är för osäker.</div>`; return; }
    const byId = Object.fromEntries(D.stones.map(s => [s.id, s]));
    const show = state.allSuggestions ? rows : rows.slice(0, 15);
    const strength = p => p >= 0.8 ? "stark" : p >= 0.6 ? "trolig" : "möjlig";
    const tr = r => {
      const st = byId[r.id];
      const prof = st && st.score != null ? `<span class="rp-pill" style="background:${pillBg(st.klass)}">${st.klass}</span>` : `<span class="rp-dim">${st ? "för lite text" : "inte bland grannarna"}</span>`;
      const note = r.rundata ? `Rundata nämner: <span translate="no">${esc(r.rundata.split(";").join(", "))}</span>` : "";
      return `<tr><td class="rp-mono">${esc(r.id)}</td><td translate="no">${esc(r.place)}${r.parish ? `<br><span class="rp-dim rp-small">${esc(r.parish)}</span>` : ""}</td>` +
        `<td><span class="rp-barp" style="width:${Math.round(r.p * 60)}px"></span>${pct(r.p)} <span class="rp-dim rp-small">${strength(r.p)}</span></td>` +
        `<td><span translate="no">${esc(r.second)}</span> <span class="rp-dim">${pct(r.p2)}</span></td><td>${prof}</td><td class="rp-dim rp-small">${note}</td></tr>`;
    };
    box.innerHTML = `<div class="rp-scroll"><table class="rp-list"><thead><tr><th>Sten</th><th>Plats</th><th>Modellen</th><th>Näst troligast</th><th>Profilen</th><th></th></tr></thead><tbody>${show.map(tr).join("")}</tbody>` +
      `<caption>${rows.length} stenar. Ett förslag, inte en attribuering: ornamentik och runformer, forskarnas viktigaste belägg, saknas i modellen.</caption></table></div>` +
      (rows.length > 15 ? `<button class="rp-more" type="button">${state.allSuggestions ? "Visa färre" : `Visa alla ${rows.length}`}</button>` : "");
    const more = box.querySelector(".rp-more");
    if (more) more.addEventListener("click", () => { state.allSuggestions = !state.allSuggestions; suggestions(); });
  }


  function bygdBox() {
    const box = $("rp-bygd");
    if (!box) return;
    const rows = carver.bygd;
    if (rows == null) { box.innerHTML = ""; box.hidden = true; return; }
    box.hidden = false;
    const T = PAGE.bygd_test, t = T && T.per_carver[WHO];
    const test = T ? `I provningen höjde den träffen i medel per ristare från ${pct(T.half2_macro[0])} till ${pct(T.half2_macro[1])}` +
      (t ? `; för ${esc(WHO)} hade den rätt på ${pct(t.bygd)} av hans ${t.n} signerade stenar, huvudmodellen på ${pct(t.main)}.` : ".") : "";
    const tr = r => `<tr><td class="rp-mono">${esc(r.id)}</td><td translate="no">${esc(r.place)}${r.parish ? `<br><span class="rp-dim rp-small">${esc(r.parish)}</span>` : ""}</td>` +
      `<td><span class="rp-barp" style="width:${Math.round(r.p * 60)}px;background:var(--rp-sand)"></span>${pct(r.p)}</td>` +
      `<td>${r.main_top ? `<span translate="no">${esc(r.main_top)}</span> <span class="rp-dim">${pct(r.main_p)}</span>${r.main_blocked ? ` <span class="rp-dim rp-small">(spärrad)</span>` : ""}` : "–"}</td>` +
      `<td class="rp-dim rp-small">${r.rundata ? `Rundata nämner: <span translate="no">${esc(r.rundata.split(";").join(", "))}</span>` : ""}</td></tr>`;
    box.innerHTML = `<h3 class="rp-h3">Andra bedömning: bygdsmodellen</h3>` +
      `<p class="rp-note"><b>Den här modellen klarade inte den låsta prövningen och används inte som appens bedömning.</b> Den visas för de små ristarna, där huvudmodellen nästan aldrig träffar. Den väger in var ristaren verkade och när, och hittar därför oftare rätt ristare för små verkstäder, men dess procent är mindre pålitliga. ${test}</p>` +
      (rows.length ? `<div class="rp-scroll"><table class="rp-list"><thead><tr><th>Sten</th><th>Plats</th><th>Bygdsmodellen</th><th>Huvudmodellen</th><th></th></tr></thead><tbody>${rows.map(tr).join("")}</tbody>` +
        `<caption>${rows.length} stenar där bygdsmodellen sätter ristaren först med minst 50 %.</caption></table></div>`
        : `<div class="rp-empty">Bygdsmodellen sätter inte ristaren först med minst 50 % på någon sten utan ristare.</div>`);
  }

  function fingerprint() {
    const svg = $("rp-fp"); svg.innerHTML = "";
    const T = D.traits;
    if (!T.length) { size(svg, 600, 40); txt(svg, 0, 24, "Inga drag skiljer sig tillräckligt från grannarna.", { "font-size": 14, fill: "var(--rp-ink2)" }); return; }
    const W = avail(svg, 520), L = Math.min(300, Math.round(W * 0.36)), R = 70, rowH = 26, top = 28, H = top + T.length * rowH + 30;
    size(svg, W, H);
    const x = v => L + v * (W - L - R);
    for (let v = 0; v <= 1.001; v += 0.25) {
      el("line", { x1: x(v), x2: x(v), y1: top - 8, y2: H - 26, stroke: "var(--rp-rule)" }, svg);
      txt(svg, x(v), H - 10, pct(v), { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)" });
    }
    const firstLess = T.findIndex(t => t.lor < 0);
    T.forEach((t, i) => {
      const y = top + i * rowH + rowH / 2;
      if (i === firstLess && i > 0) el("line", { x1: 0, x2: W, y1: y - rowH / 2, y2: y - rowH / 2, stroke: "var(--rp-ink3)", "stroke-dasharray": "3 3" }, svg);
      txt(svg, L - 12, y + 4, t.label, { "text-anchor": "end", "font-size": 13 });
      el("line", { x1: x(t.pn), x2: x(t.pc), y1: y, y2: y, stroke: "var(--rp-rust2)", "stroke-width": 2 }, svg);
      el("circle", { cx: x(t.pn), cy: y, r: 5, fill: "var(--rp-slate)", stroke: "white", "stroke-width": 2 }, svg);
      el("circle", { cx: x(t.pc), cy: y, r: 6, fill: "var(--rp-rust)", stroke: "white", "stroke-width": 2 }, svg);
      txt(svg, W - R + 10, y + 4, (t.lor > 0 ? "×" : "÷") + fmt(Math.exp(Math.abs(t.lor)), 1), { "font-size": 12, fill: "var(--rp-ink2)" });
      hover(el("rect", { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: "transparent" }, svg),
        () => `<b>${esc(t.label)}</b><br>${esc(WHO)}: ${t.kc} av ${t.nc} (${pct(t.pc)})<br>Grannar: ${t.kn} av ${t.nn} (${pct(t.pn)})<br>Oddsen ${t.lor > 0 ? "gånger" : "delat med"} ${fmt(Math.exp(Math.abs(t.lor)), 1)}` + (t.dup.length ? `<br><span class="rp-dim">Räknas ihop med: ${esc(t.dup.join(", "))}</span>` : ""));
    });
    txt(svg, L - 12, 14, "Gör oftare än grannarna ↓", { "text-anchor": "end", "font-size": 12, fill: "var(--rp-rust)" });
    txt(svg, W - R + 10, 14, "odds", { "font-size": 12, fill: "var(--rp-ink2)" });
    el("circle", { cx: L + 6, cy: 10, r: 5, fill: "var(--rp-rust)" }, svg); txt(svg, L + 16, 14, WHO, { "font-size": 12, fill: "var(--rp-ink2)" });
    const gx = L + 32 + WHO.length * 7;
    el("circle", { cx: gx, cy: 10, r: 5, fill: "var(--rp-slate)" }, svg); txt(svg, gx + 10, 14, "grannar", { "font-size": 12, fill: "var(--rp-ink2)" });
  }

  function heatmap() {
    const svg = $("rp-hm"); svg.innerHTML = "";
    const T = D.traits, S = ordered();
    const L = 150, top = 210, barW = 170, gap = 14;
    const cw = Math.max(18, Math.min(44, Math.floor((avail(svg) - L - gap - barW - 40) / Math.max(1, T.length)))), ch = 16;
    let y = top, last = null; const rows = [];
    S.forEach(s => { if (s.set !== last) { y += last ? 20 : 0; rows.push({ head: s.set, y }); y += 18; last = s.set; } rows.push({ s, y }); y += ch; });
    const W = L + T.length * cw + gap + barW + 40, H = y + 20;
    size(svg, W, H);
    T.forEach((t, j) => txt(svg, 0, 0, t.label, { "font-size": 12, transform: `translate(${L + j * cw + cw / 2 + 4},${top - 8}) rotate(-55)`, fill: t.lor > 0 ? "var(--rp-ink)" : "var(--rp-ink2)" }));
    const x0 = L + T.length * cw + gap, sx = v => x0 + (v + 0.6) / 1.3 * barW;
    rows.forEach(r => {
      if (r.head) { txt(svg, 0, r.y + 12, SETLABEL[r.head] + " (" + S.filter(s => s.set === r.head).length + ")", { "font-size": 13, "font-weight": 600 }); return; }
      const s = r.s;
      txt(svg, L - 10, r.y + ch - 3.5, s.id, { "text-anchor": "end", "font-size": 12, "font-family": "var(--rp-mono)" });
      s.cells.forEach((v, j) => {
        const t = T[j], follow = v == null ? null : (t.lor > 0 ? v === 1 : v === 0);
        hover(el("rect", { x: L + j * cw + 1, y: r.y + 1, width: cw - 2, height: ch - 2, rx: 3, fill: follow == null ? "var(--rp-empty)" : follow ? "var(--rp-rust)" : "var(--rp-slate2)" }, svg),
          () => `<b>${esc(s.id)}</b> · ${esc(t.label)}<br>${v == null ? "Går inte att avläsa" : (v === 1 ? "Ja" : "Nej") + " – " + (follow ? "som " + esc(WHO) : "som grannarna")}<br><span class="rp-dim">${esc(WHO)} ${pct(t.pc)}, grannar ${pct(t.pn)}</span>`);
      });
      const zero = sx(0);
      if (s.score != null) {
        const a = sx(Math.max(-0.6, Math.min(0.7, s.score)));
        hover(el("rect", { x: Math.min(a, zero), y: r.y + 2, width: Math.max(1.5, Math.abs(a - zero)), height: ch - 4, rx: 2, fill: KCOL[s.klass] }, svg), () => stoneTip(s));
      } else txt(svg, zero + 6, r.y + ch - 3.5, "för lite text", { "font-size": 11, fill: "var(--rp-ink3)" });
    });
    el("line", { x1: sx(0), x2: sx(0), y1: top - 4, y2: H - 16, stroke: "var(--rp-ink3)" }, svg);
    txt(svg, sx(0), top - 8, "0", { "text-anchor": "middle", "font-size": 11, fill: "var(--rp-ink2)" });
    txt(svg, sx(0.7), top - 8, "mer lik →", { "text-anchor": "end", "font-size": 11, fill: "var(--rp-ink2)" });
    txt(svg, sx(-0.6), top - 8, "← grannar", { "font-size": 11, fill: "var(--rp-ink2)" });
    $("rp-hm-legend").innerHTML =
      `<span><i style="background:var(--rp-rust)"></i>gör som ${esc(WHO)}</span><span><i style="background:var(--rp-slate2)"></i>gör som grannarna</span><span><i style="background:var(--rp-empty);border:1px solid var(--rp-rule)"></i>går inte att avläsa</span>` +
      KL.slice(0, 4).map(k => `<span><i style="background:${KCOL[k]}"></i>${k}</span>`).join("");
  }

  function dots() {
    const svg = $("rp-dots"); svg.innerHTML = "";
    const groups = SETS.filter(g => D.stones.some(s => s.set === g)).concat(["granne"]);
    const W = avail(svg, 560), L = Math.min(220, Math.round(W * 0.24)), R = 30, rowH = 66, top = 40, H = top + groups.length * rowH + 34;
    size(svg, W, H);
    const all = D.stones.filter(s => s.score != null).map(s => s.score);
    if (!all.length) return;
    const lo = Math.min(-0.7, Math.min(...all)), hi = Math.max(0.8, Math.min(1.6, Math.max(...all)));
    const x = v => L + (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * (W - L - R);
    const g = D.granser;
    [[lo, g.spann, "som grannarna"], [g.spann, g.grannar_p90, "ytterkant"], [g.grannar_p90, g.karna, "inom spannet"], [g.karna, hi, "kärna"]].forEach(([a, b, k]) => {
      if (a == null || b == null || b <= a) return;
      el("rect", { x: x(a), y: top - 18, width: x(b) - x(a), height: H - top - 16, fill: KCOL[k], opacity: 0.12 }, svg);
      txt(svg, (x(a) + x(b)) / 2, top - 24, k, { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)" });
    });
    [g.spann, g.grannar_p90, g.karna].forEach(v => v != null && el("line", { x1: x(v), x2: x(v), y1: top - 18, y2: H - 34, stroke: "var(--rp-ink3)", "stroke-dasharray": "3 3" }, svg));
    for (let v = Math.ceil(lo * 2) / 2; v <= hi; v += 0.5) txt(svg, x(v), H - 12, fmt(v, 1), { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)" });
    groups.forEach((gname, i) => {
      const yc = top + i * rowH + rowH / 2, ss = D.stones.filter(s => s.set === gname && s.score != null);
      txt(svg, L - 14, yc + 4, `${SETLABEL[gname]} (${ss.length})`, { "text-anchor": "end", "font-size": 13 });
      ss.forEach((s, k) => {
        const jit = ((k * 37) % 23) / 23 - 0.5, isN = gname === "granne", cy = yc + jit * (rowH - 22);
        hover(el("circle", { cx: x(s.score), cy, r: isN ? 3 : 5.5, fill: isN ? "var(--rp-ink3)" : KCOL[s.klass], opacity: isN ? 0.45 : 1, stroke: isN ? "none" : "white", "stroke-width": 1.5 }, svg), () => stoneTip(s));
        if (!isN && flagged(s)) txt(svg, x(s.score), cy - 9, s.id, { "text-anchor": "middle", "font-size": 11, "font-family": "var(--rp-mono)" });
      });
    });
  }

  function map() {
    const svg = $("rp-map"); svg.innerHTML = "";
    const K = PAGE.karta, [x0, y0, x1, y1] = D.bbox, k = Math.cos((y0 + y1) / 2 * Math.PI / 180);
    const W = avail(svg, 300), sc = W / ((x1 - x0) * k), H = Math.min(Math.round(W * 1.5), Math.round((y1 - y0) * sc));
    size(svg, W, H);
    const P = ([lon, lat]) => [((lon - x0) * k * sc).toFixed(1), ((y1 - lat) * sc).toFixed(1)];
    const inBox = ring => ring.some(([a, b]) => a >= x0 - 1 && a <= x1 + 1 && b >= y0 - 1 && b <= y1 + 1);
    el("rect", { x: 0, y: 0, width: W, height: H, rx: 18, fill: "var(--rp-sea)" }, svg);
    const id = "rp-mclip-" + C;
    const clip = el("clipPath", { id }, el("defs", {}, svg)); el("rect", { x: 0, y: 0, width: W, height: H, rx: 18 }, clip);
    const g = el("g", { "clip-path": `url(#${id})` }, svg);
    K.coast.filter(inBox).forEach(r => el("path", { d: "M" + r.map(P).join("L") + "Z", fill: "white", stroke: "var(--rp-rule)" }, g));
    K.folk.filter(f => inBox(f.ring)).forEach(f => el("path", { d: "M" + f.ring.map(P).join("L") + "Z", fill: "none", stroke: "var(--rp-ink3)", "stroke-dasharray": "4 3", "stroke-width": 1 }, g));
    K.labels.filter(l => l.lon > x0 && l.lon < x1 && l.lat > y0 && l.lat < y1).forEach(l => { const [x, y] = P([l.lon, l.lat]); txt(g, x, y, l.label, { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink3)", "font-style": "italic" }); });
    D.stones.filter(s => s.set === "granne" && s.lat != null).forEach(s => { const [x, y] = P([s.lon, s.lat]); el("circle", { cx: x, cy: y, r: 1.8, fill: "var(--rp-ink3)", opacity: 0.5 }, g); });
    const F = carver.forslag;
    (F ? F.rows : []).filter(r => r.lat != null).forEach(r => {
      const [x, y] = P([r.lon, r.lat]);
      hover(el("circle", { cx: x, cy: y, r: 6, fill: "none", stroke: "var(--rp-rust)", "stroke-width": 2, "stroke-dasharray": "2.5 2" }, g),
        () => `<b>${esc(r.id)}</b> · ${esc(r.place)}<br>Modellen föreslår ${esc(WHO)}: ${pct(r.p)}<br><span class="rp-dim">ingen säker ristare i Rundata</span>`);
    });
    own().filter(s => s.lat != null).sort((a, b) => KL.indexOf(b.klass) - KL.indexOf(a.klass)).forEach(s => {
      const [x, y] = P([s.lon, s.lat]), signed = s.set.startsWith("signerad");
      const m = s.set === "osäker"
        ? el("rect", { x: x - 4.5, y: y - 4.5, width: 9, height: 9, transform: `rotate(45 ${x} ${y})`, fill: KCOL[s.klass], stroke: "var(--rp-ink)", "stroke-width": 0.8 }, g)
        : el("circle", { cx: x, cy: y, r: signed ? 6.5 : 5, fill: KCOL[s.klass], stroke: signed ? "var(--rp-ink)" : "white", "stroke-width": signed ? 1.6 : 1.2 }, g);
      hover(m, () => stoneTip(s));
      if (flagged(s)) txt(g, +x + 9, +y + 4, s.id, { "font-size": 11, "font-family": "var(--rp-mono)" });
    });
  }

  function scatter() {
    const svg = $("rp-sc"); svg.innerHTML = "";
    const S = own().filter(s => s.score != null && s.modell != null);
    const a = AUDIT.q1.per_carver.find(r => r.carver === WHO), b = AUDIT.q2.per_carver.find(r => r.carver === WHO);
    $("rp-audit").innerHTML = b ? `I provningen mot facit (hela socknar utelämnade) hade modellen rätt ristare först på ${a ? `<b>${pct(a.top1)}</b> av hans ${a.n} signerade stenar och ` : ""}<b>${pct(b.top1_attr)}</b> av hans ${b.n_attr} attribuerade. Över alla 117 signerade stenar: ${pct(AUDIT.q1.top1[0])}.` :
      `${esc(WHO)} har färre än åtta säkra stenar och finns inte i attribueringsmodellen.`;
    if (!S.length) { size(svg, 10, 10); return; }
    const W = avail(svg, 300), H = Math.round(Math.min(460, Math.max(300, W * 0.8))), L = 54, B = 46, T = 14, R = 14;
    size(svg, W, H);
    const lo = -0.6, hi = 0.8;
    const x = v => L + (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * (W - L - R), y = v => T + (1 - v) * (H - T - B);
    for (let v = 0; v <= 1.001; v += 0.25) { el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: "var(--rp-rule)" }, svg); txt(svg, L - 8, y(v) + 4, pct(v), { "text-anchor": "end", "font-size": 12, fill: "var(--rp-ink2)" }); }
    for (let v = -0.5; v <= hi; v += 0.25) txt(svg, x(v), H - B + 18, fmt(v, 2), { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)" });
    el("line", { x1: x(0), x2: x(0), y1: T, y2: H - B, stroke: "var(--rp-ink3)", "stroke-dasharray": "3 3" }, svg);
    txt(svg, (L + W - R) / 2, H - 8, "följer profilen →", { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)" });
    txt(svg, 14, (T + H - B) / 2, `modellen säger ${WHO}`, { "text-anchor": "middle", "font-size": 12, fill: "var(--rp-ink2)", transform: `rotate(-90 14 ${(T + H - B) / 2})` });
    S.forEach(s => {
      const signed = s.set.startsWith("signerad");
      hover(el("circle", { cx: x(s.score), cy: y(s.modell), r: signed ? 6.5 : 5, fill: KCOL[s.klass], stroke: signed ? "var(--rp-ink)" : "white", "stroke-width": signed ? 1.6 : 1.2 }, svg), () => stoneTip(s));
      if (flagged(s)) txt(svg, x(s.score) + 9, y(s.modell) + 4, s.id, { "font-size": 11, "font-family": "var(--rp-mono)" });
    });
  }

  function similarity() {
    const svg = $("rp-sim"); svg.innerHTML = "";
    const ids = D.sim.ids, M = D.sim.m, n = ids.length;
    if (n < 3) { size(svg, 600, 40); txt(svg, 0, 24, "För få stenar med tillräckligt många avläsbara drag.", { "font-size": 14, fill: "var(--rp-ink2)" }); $("rp-sim-legend").innerHTML = ""; return; }
    const L = 104, T = 104;
    // Rutorna fyller bredden, men högst 26 px; matrisen hålls kvadratisk och centreras när den blir smalare än panelen
    const c = Math.max(9, Math.min(26, Math.floor((avail(svg) - L - 10) / n)));
    const W = L + n * c + 10, H = T + n * c + 10;
    size(svg, W, H);
    const byId = Object.fromEntries(own().map(s => [s.id, s]));
    const ramp = v => v == null ? "var(--rp-empty)" : `color-mix(in oklab, var(--rp-rust) ${Math.round(Math.max(0, (v - 0.3) / 0.7) * 100)}%, white)`;
    const fs = Math.min(12, c - 1);
    ids.forEach((id, i) => {
      const s = byId[id], mark = s.set.startsWith("signerad") ? "●" : s.set === "osäker" ? "◆" : "";
      txt(svg, L - 6, T + i * c + c / 2 + fs / 2 - 1.5, id + (mark ? " " + mark : ""), { "text-anchor": "end", "font-size": fs, "font-family": "var(--rp-mono)", fill: s.set.startsWith("signerad") ? "var(--rp-ink)" : "var(--rp-ink2)" });
      txt(svg, 0, 0, id, { "font-size": fs, "font-family": "var(--rp-mono)", transform: `translate(${L + i * c + c / 2 + fs / 3},${T - 6}) rotate(-60)`, fill: "var(--rp-ink2)" });
      M[i].forEach((v, j) => {
        const r = el("rect", { x: L + j * c, y: T + i * c, width: c - 1, height: c - 1, rx: c > 14 ? 2 : 0, fill: ramp(v) }, svg);
        if (i !== j) hover(r, () => `<b>${esc(id)}</b> och <b>${esc(ids[j])}</b><br>${v == null ? "för få gemensamma drag" : "gör lika i " + pct(v) + " av dragen"}`);
      });
    });
    $("rp-sim-legend").innerHTML = [0.4, 0.6, 0.8, 1].map(v => `<span><i style="background:${ramp(v)};border:1px solid var(--rp-rule)"></i>${pct(v)} lika</span>`).join("") + `<span>● signerad · ◆ delad eller osäker</span>`;
  }

  function lists() {
    const edge = own().filter(s => s.klass === "ytterkant" || s.klass === "som grannarna").sort((a, b) => a.score - b.score);
    const grp = s => ({ "signerad": "signerad", "signerad utanför profilen": "signerad, utanför profilen", "attribuerad": "attribuerad", "osäker": "delad/osäker" }[s.set]);
    const row = s => `<tr><td class="rp-mono">${esc(s.id)}</td><td translate="no">${esc(s.place)}</td><td>${grp(s)}</td><td>${esc(s.style || "–")}</td><td>${fmt(s.score)}</td><td><span class="rp-pill" style="background:${pillBg(s.klass)}">${s.klass}</span></td></tr>`;
    $("rp-edge").innerHTML = edge.length ? `<div class="rp-scroll"><table class="rp-list"><thead><tr><th>Sten</th><th>Plats</th><th>Grupp</th><th>Stil</th><th>Värde</th><th>Klass</th></tr></thead><tbody>${edge.map(row).join("")}</tbody></table></div>` : `<div class="rp-empty">Ingen av stenarna ligger i ytterkanten eller bland grannarna.</div>`;
    const nb = D.stones.filter(s => s.set === "granne" && s.score != null && s.n >= 10).sort((a, b) => b.score - a.score).slice(0, 10);
    $("rp-nb").innerHTML = nb.length ? `<div class="rp-scroll"><table class="rp-list"><thead><tr><th>Sten</th><th>Plats</th><th>Stil</th><th>Drag</th><th>Värde</th></tr></thead><tbody>${nb.map(s => `<tr><td class="rp-mono">${esc(s.id)}</td><td translate="no">${esc(s.place)}</td><td>${esc(s.style || "–")}</td><td>${s.n}</td><td>${fmt(s.score)}</td></tr>`).join("")}</tbody><caption>Bara stenar med minst tio avläsbara drag.</caption></table></div>` : `<div class="rp-empty">Inga grannstenar med minst tio avläsbara drag.</div>`;
  }

  function method() {
    const dups = D.traits.filter(t => t.dup.length).map(t => `<span>${esc(t.label)}</span> = ${t.dup.map(x => `<span>${esc(x)}</span>`).join(" = ")}`).join("<br>");
    const cant = own().filter(s => s.klass === "kan inte avgöras").length;
    const items = [
      D.profil === "signerade"
        ? `<b>Profilen byggs bara av de signerade stenarna.</b> De attribuerade har runologerna tillskrivit ${esc(WHO)} efter drag som ornamentik och stavning; att använda dem i profilen vore att låta svaret bestämma frågan.`
        : `<b>Profilen byggs av alla säkra stenar</b> (signerade och attribuerade), eftersom de signerade är för få (färre än fem, eller för få drag som skiljer dem från grannarna). Det är ett mått på hur samstämmig gruppen är, inte en oberoende prövning.`,
      `<b>Grannarna</b> är alla andra stenar inom ${D.km} km från någon av ristarens stenar${D.period && D.period[0] != null ? `, med en stildatering som överlappar hans (${D.period[0]}–${D.period[1]})` : ""}.`,
      `<b>Ett drag kommer med</b> om det går att avläsa på tillräckligt många av profilens stenar, skiljer sig med minst dubbla eller halva oddsen från grannarna och inte är en ren slump (Fishers test, p &lt; 0,10). Drag som nästan alltid följs åt räknas en gång.${dups ? `<br><span class="rp-dim">${dups}</span>` : ""}`,
      `<b>Värdet per sten</b> är medelvärdet av hur mycket varje avläsbart drag talar för ${esc(WHO)} mot grannarna. Noll betyder att stenen inte lutar åt något håll.`,
      `<b>Appens förslag</b> kommer från attribueringsmodellen (random forest över plats, stil, stavning, formler och runpar), omkalibrerad efter provningen mot de signerade stenarna; spärren för okända ristare sorterar bort stenar där förstavalet är för svagt.`,
      `<b>Ornamentiken ingår inte</b> utöver stilgruppen, och runformerna inte alls: forskarnas viktigaste belägg för attribueringarna saknas alltså här. En attribuerad sten bland ”som grannarna” är ett skäl att titta igen, inte ett bevis för att attribueringen är fel.`,
    ];
    if (WHO === "Balle") items.push(`<b>Röd-Balle:</b> Vs 15 och Vs 24 är signerade <i>roþbaliʀ</i>, och en del runologer tvivlar på att han är samma person som Balle. Båda hamnar i ytterkanten med alla 20 i profilen, och bland grannarna när profilen byggs av de övriga 18. Men de står i Västmanland och tillhör den senare stilgruppen Pr4, så skillnaden kan också vara bygdens och tidens.`);
    if (cant) items.push(`${cant} av stenarna har för lite läsbar text för att mätas.`);
    $("rp-method").innerHTML = items.map(s => `<li>${s}</li>`).join("");
  }

  header(); suggestions(); bygdBox(); fingerprint(); heatmap(); dots(); map(); scatter(); similarity(); lists(); method();
}
