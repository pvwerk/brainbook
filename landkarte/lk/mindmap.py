"""Zweck: Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver.

Bewusst ohne CDN und ohne Fremdbibliothek: die Karte zeigt Projektstruktur,
und die soll beim Öffnen keine Verbindung nach aussen aufbauen.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

KOPF = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mindmap __NAME__</title>
<style>
:root {
  --grund: #fbfaf7; --schrift: #1b1a17; --matt: #6b6762; --linie: #d8d3ca;
  --ordner: #8a5a2b; --datei: #2f6f6f; --einstieg: #a8321e; --feld: #fff;
  --rand: #e4dfd6; --verweis: #bcb5a9;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-thema="hell"]) {
    --grund: #16181a; --schrift: #ecebe8; --matt: #9a9590; --linie: #343a3e;
    --ordner: #d9a066; --datei: #6fc2bd; --einstieg: #e2705a; --feld: #1e2124;
    --rand: #2e3337; --verweis: #3b4248;
  }
}
* { box-sizing: border-box; }
html, body { margin:0; height:100%; background:var(--grund); color:var(--schrift);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; }
#huelle { display:flex; height:100vh; }
#leinwand { flex:1; position:relative; overflow:hidden; cursor:grab; }
#leinwand.zieht { cursor:grabbing; }
svg { width:100%; height:100%; display:block; }
#kopf { position:absolute; top:0; left:0; right:0; padding:12px 16px;
  display:flex; gap:10px; align-items:center; flex-wrap:wrap;
  background:linear-gradient(var(--grund), transparent); pointer-events:none; }
#kopf > * { pointer-events:auto; }
h1 { font-size:15px; margin:0; font-weight:650; letter-spacing:-.01em; }
#kopf .matt { color:var(--matt); font-size:12px; }
button, input {
  font:inherit; font-size:12px; padding:5px 10px; border:1px solid var(--rand);
  background:var(--feld); color:var(--schrift); border-radius:7px; cursor:pointer; }
button:hover { border-color:var(--matt); }
input { cursor:text; min-width:150px; }
#tafel { width:330px; border-left:1px solid var(--rand); background:var(--feld);
  padding:18px; overflow-y:auto; }
#tafel h2 { font-size:14px; margin:0 0 4px; word-break:break-all; }
#tafel .pfad { color:var(--matt); font-size:11px; margin-bottom:12px;
  word-break:break-all; font-family:ui-monospace, SFMono-Regular, Menlo, monospace; }
#tafel .zweck { margin-bottom:14px; }
#tafel h3 { font-size:11px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--matt); margin:16px 0 6px; }
#tafel ul { margin:0; padding-left:0; list-style:none; }
#tafel li { font-family:ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size:11.5px; padding:2px 0; border-bottom:1px solid var(--rand); }
#tafel li .nr { color:var(--matt); display:inline-block; min-width:34px;
  text-align:right; margin-right:8px; }
#tafel li .art { color:var(--matt); }
.knoten { cursor:pointer; }
.knoten text { font-size:11px; fill:var(--schrift); }
.knoten.ordner text { font-weight:650; fill:var(--ordner); font-size:12px; }
.knoten.einstieg text { fill:var(--einstieg); font-weight:600; }
.knoten.blass { opacity:.18; }
.knoten.gewaehlt circle { stroke:var(--schrift); stroke-width:2.5; }
.ast { fill:none; stroke:var(--linie); }
.verweis { fill:none; stroke:var(--verweis); stroke-width:1; opacity:.5; }
@media (max-width:820px) { #tafel { display:none; } }
</style></head><body>
<div id="huelle">
  <div id="leinwand">
    <div id="kopf">
      <h1>__NAME__</h1>
      <span class="matt">__STAND__</span>
      <input id="filter" placeholder="filtern …">
      <button id="verweise">Verweise</button>
      <button id="zurueck">zurücksetzen</button>
    </div>
    <svg id="bild"><g id="welt"></g></svg>
  </div>
  <aside id="tafel"><p class="matt">Einen Knoten anklicken.</p></aside>
</div>
<script id="daten" type="application/json">__DATEN__</script>
<script>
const daten = JSON.parse(document.getElementById('daten').textContent);
const welt = document.getElementById('welt');
const SVG = 'http://www.w3.org/2000/svg';
const el = (n, a) => { const e = document.createElementNS(SVG, n);
  for (const k in (a||{})) e.setAttribute(k, a[k]); return e; };

/* ---- Baum aus den Pfaden ---- */
const wurzel = { name: daten.name, art: 'wurzel', kinder: [], tiefe: 0 };
const ordner = new Map([['', wurzel]]);
function ordnerHolen(pfad) {
  if (ordner.has(pfad)) return ordner.get(pfad);
  const teile = pfad.split('/');
  const eltern = ordnerHolen(teile.slice(0, -1).join('/'));
  const k = { name: teile[teile.length-1], art:'ordner', pfad, kinder:[],
              tiefe: eltern.tiefe + 1 };
  eltern.kinder.push(k); ordner.set(pfad, k); return k;
}
for (const d of daten.dateien) {
  const teile = d.pfad.split('/');
  const eltern = ordnerHolen(teile.slice(0, -1).join('/'));
  eltern.kinder.push({ name: teile[teile.length-1], art:'datei', ...d,
                       kinder: [], tiefe: eltern.tiefe + 1 });
}
(function sortieren(k){ k.kinder.sort((a,b)=>
   (a.art===b.art? a.name.localeCompare(b.name) : a.art==='ordner'?-1:1));
   k.kinder.forEach(sortieren); })(wurzel);

/* ---- radiale Anordnung: jedes Blatt bekommt einen Winkelplatz ---- */
let blattZaehler = 0;
const blaetter = [];
(function zaehlen(k){ if(!k.kinder.length){ k.platz = blattZaehler++;
   blaetter.push(k); return; } k.kinder.forEach(zaehlen); })(wurzel);
const gesamt = Math.max(blattZaehler, 1);
const RADIUS = Math.max(240, gesamt * 7);
(function legen(k){
  if (!k.kinder.length) {
    k.winkel = (k.platz + 0.5) / gesamt * Math.PI * 2 - Math.PI/2;
  } else {
    k.kinder.forEach(legen);
    k.winkel = k.kinder.reduce((s,x)=>s+x.winkel,0) / k.kinder.length;
  }
  const r = k.tiefe === 0 ? 0 : RADIUS * (k.tiefe / (maxTiefe()||1));
  k.x = Math.cos(k.winkel) * r; k.y = Math.sin(k.winkel) * r; k.r = r;
})(wurzel);
function maxTiefe(){ let m=0; (function g(k){ m=Math.max(m,k.tiefe);
  k.kinder.forEach(g); })(wurzel); return m; }

const alle = []; (function sammeln(k){ alle.push(k); k.kinder.forEach(sammeln); })(wurzel);
const nachPfad = new Map(alle.filter(k=>k.pfad).map(k=>[k.pfad,k]));

/* ---- Äste ---- */
const astGruppe = el('g'); welt.appendChild(astGruppe);
for (const k of alle) for (const kind of k.kinder) {
  astGruppe.appendChild(el('path', { class:'ast',
    d:`M${k.x},${k.y}Q${(k.x+kind.x)/2*1.15},${(k.y+kind.y)/2*1.15} ${kind.x},${kind.y}`,
    'stroke-width': Math.max(0.6, 2.2 - k.tiefe * 0.5) }));
}

/* ---- Verweise ---- */
const verweisGruppe = el('g', { opacity: 0 }); welt.appendChild(verweisGruppe);
for (const [von, nach] of Object.entries(daten.kanten || {})) {
  const a = nachPfad.get(von); if (!a) continue;
  for (const zielPfad of nach) {
    const b = nachPfad.get(zielPfad); if (!b) continue;
    verweisGruppe.appendChild(el('path', { class:'verweis',
      d:`M${a.x},${a.y}Q0,0 ${b.x},${b.y}` }));
  }
}

/* ---- Knoten ---- */
const knotenGruppe = el('g'); welt.appendChild(knotenGruppe);
for (const k of alle) {
  const klassen = ['knoten', k.art].concat(k.einstieg ? ['einstieg'] : []);
  const g = el('g', { class: klassen.join(' '),
                      transform:`translate(${k.x},${k.y})` });
  const gross = k.art === 'wurzel' ? 9 : k.art === 'ordner' ? 5.5 : 3.5;
  g.appendChild(el('circle', { r: gross,
    fill: k.art==='ordner'||k.art==='wurzel' ? 'var(--ordner)'
         : k.einstieg ? 'var(--einstieg)' : 'var(--datei)' }));
  if (k.art !== 'wurzel') {
    const links = Math.cos(k.winkel) < 0;
    const t = el('text', { x: links ? -(gross+5) : gross+5, dy:'0.33em',
      'text-anchor': links ? 'end' : 'start',
      transform:`rotate(${(k.winkel*180/Math.PI) + (links?180:0)})` });
    t.textContent = k.name.length > 30 ? k.name.slice(0,29)+'…' : k.name;
    g.appendChild(t);
  } else {
    const t = el('text', { dy:'-16', 'text-anchor':'middle',
                           style:'font-size:15px;font-weight:700' });
    t.textContent = k.name; g.appendChild(t);
  }
  g.addEventListener('click', e => { e.stopPropagation(); waehlen(k, g); });
  k.form = g; knotenGruppe.appendChild(g);
}

/* ---- Tafel ---- */
const tafel = document.getElementById('tafel');
let gewaehlt = null;
function waehlen(k, g) {
  if (gewaehlt) gewaehlt.classList.remove('gewaehlt');
  gewaehlt = g; g.classList.add('gewaehlt');
  const teile = [`<h2>${k.name}</h2>`];
  if (k.pfad) teile.push(`<div class="pfad">${k.pfad}</div>`);
  if (k.zweck) teile.push(`<div class="zweck">${k.zweck}</div>`);
  if (k.art === 'ordner' || k.art === 'wurzel') {
    const n = []; (function z(x){ if(x.art==='datei') n.push(x);
      x.kinder.forEach(z); })(k);
    teile.push(`<h3>${n.length} Dateien</h3><ul>` +
      n.slice(0,80).map(x=>`<li>${x.name}</li>`).join('') + '</ul>');
  }
  if (k.symbole && k.symbole.length) {
    teile.push(`<h3>${k.symbole.length} Symbole</h3><ul>` +
      k.symbole.map(s=>`<li><span class="nr">${s.zeile}</span>` +
        `<span class="art">${s.art}</span> ${s.name}</li>`).join('') + '</ul>');
  }
  if (k.zeilen) teile.push(`<h3>Umfang</h3><div>${k.zeilen} Zeilen</div>`);
  tafel.innerHTML = teile.join('');
}

/* ---- Verschieben und Zoomen ---- */
let zoom = 0.85, vx = 0, vy = 0;
const bild = document.getElementById('bild');
const leinwand = document.getElementById('leinwand');
function zeichnen() {
  const b = leinwand.clientWidth/2, h = leinwand.clientHeight/2;
  welt.setAttribute('transform', `translate(${b+vx},${h+vy}) scale(${zoom})`);
}
let zieht = false, zx = 0, zy = 0;
leinwand.addEventListener('pointerdown', e => {
  zieht = true; zx = e.clientX - vx; zy = e.clientY - vy;
  leinwand.classList.add('zieht'); leinwand.setPointerCapture(e.pointerId); });
leinwand.addEventListener('pointermove', e => {
  if (!zieht) return; vx = e.clientX - zx; vy = e.clientY - zy; zeichnen(); });
leinwand.addEventListener('pointerup', () => {
  zieht = false; leinwand.classList.remove('zieht'); });
leinwand.addEventListener('wheel', e => {
  e.preventDefault();
  zoom = Math.min(5, Math.max(0.12, zoom * (e.deltaY < 0 ? 1.12 : 0.893)));
  zeichnen(); }, { passive:false });
document.getElementById('zurueck').onclick = () => {
  zoom = 0.85; vx = 0; vy = 0; zeichnen(); };
let verweiseAn = false;
document.getElementById('verweise').onclick = () => {
  verweiseAn = !verweiseAn;
  verweisGruppe.setAttribute('opacity', verweiseAn ? 1 : 0); };
document.getElementById('filter').addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase();
  for (const k of alle) {
    if (!k.form || k.art === 'wurzel') continue;
    const treffer = !q || (k.pfad||k.name).toLowerCase().includes(q) ||
      (k.zweck||'').toLowerCase().includes(q) ||
      (k.symbole||[]).some(s => s.name.toLowerCase().includes(q));
    k.form.classList.toggle('blass', !treffer);
  }
});
window.addEventListener('resize', zeichnen);
zeichnen();
</script></body></html>
"""


def bauen(modell: dict, ziel: Path) -> Path:
    """HTML-Mindmap aus einem Scan-Modell schreiben."""
    dateien = []
    for d in modell["dateien"]:
        if d["pfad"].startswith(".landkarte/"):
            continue
        dateien.append({
            "pfad": d["pfad"],
            "zweck": d.get("zweck", ""),
            "zeilen": d.get("zeilen", 0),
            "einstieg": bool(d.get("einstieg")),
            "symbole": [{"zeile": s["zeile"], "art": s["art"], "name": s["name"]}
                        for s in d.get("symbole", [])][:60],
        })
    daten = {
        "name": modell["name"],
        "wurzel": modell["wurzel"],
        "dateien": dateien,
        "kanten": modell.get("kanten", {}),
    }
    stand = datetime.fromtimestamp(modell["gescannt"]).strftime("%d.%m.%Y %H:%M")
    html = (KOPF
            .replace("__NAME__", modell["name"])
            .replace("__STAND__", f"{stand} · {modell['anzahl_dateien']} Dateien")
            .replace("__DATEN__", json.dumps(daten, ensure_ascii=False)
                     .replace("</script", "<\\/script")))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(html, "utf-8")
    return ziel


def mermaid(modell: dict, grenze: int = 60) -> str:
    """Kleiner Graph als Mermaid-Text - für schnelles Einfügen in Notizen."""
    dateien = sorted(modell["dateien"], key=lambda d: -d.get("rang", 0))[:grenze]
    erlaubt = {d["pfad"] for d in dateien}
    kennung: dict[str, str] = {}
    z = ["graph LR"]
    for i, d in enumerate(dateien):
        k = f"n{i}"
        kennung[d["pfad"]] = k
        beschriftung = d["pfad"].replace('"', "'")
        z.append(f'  {k}["{beschriftung}"]')
    for quelle, ziele in (modell.get("kanten") or {}).items():
        if quelle not in erlaubt:
            continue
        for ziel in ziele:
            if ziel in erlaubt:
                z.append(f"  {kennung[quelle]} --> {kennung[ziel]}")
    return "\n".join(z)
