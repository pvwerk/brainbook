"""Zweck: Der Setzer - aus Scan, Buch und Notizen die KARTE.md bauen."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from . import buch, chronik, konfig, korrektur, notizen, scan

SPITZE_DATEIEN = 18        # Dateien mit Symbolen in der Karte
MAX_SYMBOLE = 22           # Symbole je Datei in der Karte


def _pruefmarke(kopf: dict) -> str:
    """Zeigt in der Karte, wie gut ein Kapitel abgesichert ist."""
    teile = []
    schreiber = str(kopf.get("schreiber", ""))
    if schreiber == "2":
        if str(kopf.get("einstimmig")) == "True":
            teile.append("2 Schreiber einstimmig")
        else:
            teile.append("2 Schreiber, bereinigt")
    elif schreiber == "1":
        teile.append("nur 1 Schreiber")
    if str(kopf.get("strittig", "0")) not in ("0", "", "None"):
        teile.append(f"{kopf['strittig']} strittig")
    if str(kopf.get("chronik_vollstaendig")) == "False":
        teile.append("Chronik lückenhaft")
    return f" _[{', '.join(teile)}]_" if teile else ""


def _zeit(stempel: int | float) -> str:
    return datetime.fromtimestamp(stempel).strftime("%Y-%m-%d %H:%M")


def _tabelle(zeilen: list[tuple[str, str]], kopf: tuple[str, str]) -> list[str]:
    if not zeilen:
        return []
    breite = max([len(kopf[0])] + [len(a) for a, _ in zeilen])
    aus = [f"| {kopf[0]:<{breite}} | {kopf[1]} |",
           f"| {'-' * breite} | {'-' * 40} |"]
    for a, b in zeilen:
        aus.append(f"| {a:<{breite}} | {b} |")
    return aus


def _baum(dateien: list[dict], nutzung_dateien: dict) -> list[str]:
    """Ordnerbaum mit Zweck je Datei, nach Ordnern gruppiert."""
    nach_ordner: dict[str, list[dict]] = {}
    for d in dateien:
        ordner = str(Path(d["pfad"]).parent)
        ordner = "" if ordner == "." else ordner
        nach_ordner.setdefault(ordner, []).append(d)

    aus: list[str] = []
    for ordner in sorted(nach_ordner, key=lambda o: (o != "", o)):
        eintraege = sorted(nach_ordner[ordner], key=lambda d: d["pfad"])
        if ordner:
            anzahl = len(eintraege)
            zeilen = sum(d["zeilen"] for d in eintraege)
            aus.append("")
            aus.append(f"**`{ordner}/`** — {anzahl} Dateien, {zeilen} Zeilen")
        else:
            aus.append("")
            aus.append("**Wurzel**")
        aus.append("")
        for d in eintraege:
            name = Path(d["pfad"]).name
            marken = []
            if d.get("einstieg"):
                marken.append("Einstieg")
            zugriffe = nutzung_dateien.get(d["pfad"], 0)
            if zugriffe >= 5:
                marken.append(f"{zugriffe}x angefasst")
            if d.get("eingehend", 0) >= 3:
                marken.append(f"{d['eingehend']} Verweise")
            anhang = f"  _[{', '.join(marken)}]_" if marken else ""
            zweck = d.get("zweck") or ""
            if zweck:
                aus.append(f"- `{name}` — {zweck}{anhang}")
            else:
                aus.append(f"- `{name}`{anhang}")
    return aus


def _symbole(dateien: list[dict], nutzung_dateien: dict) -> list[str]:
    rang = sorted(
        (d for d in dateien if d.get("symbole")),
        key=lambda d: -(d.get("rang", 0) + nutzung_dateien.get(d["pfad"], 0)),
    )[:SPITZE_DATEIEN]
    aus: list[str] = []
    for d in rang:
        aus.append("")
        aus.append(f"### `{d['pfad']}`")
        if d.get("zweck"):
            aus.append(f"_{d['zweck']}_")
        aus.append("")
        aus.append("```")
        for s in d["symbole"][:MAX_SYMBOLE]:
            doku = ""
            if s.get("doku"):
                doku = "   # " + s["doku"][0][:70]
            aus.append(f"{s['zeile']:>5}  {s['art']} {s['name']}{doku}")
        if len(d["symbole"]) > MAX_SYMBOLE:
            aus.append(f"       ... {len(d['symbole']) - MAX_SYMBOLE} weitere")
        aus.append("```")
    return aus


def _symboldatei_schreiben(modell: dict, wurzel: Path) -> None:
    """Vollstaendige Symbolliste getrennt ablegen, damit KARTE.md lesbar bleibt."""
    zeilen = [f"# Symbole: {modell['name']}", "",
              f"Stand {_zeit(modell['gescannt'])}. Vollstaendig; die KARTE.md "
              f"zeigt nur die wichtigsten Dateien.", ""]
    for d in sorted(modell["dateien"], key=lambda x: x["pfad"]):
        if not d.get("symbole"):
            continue
        zeilen.append(f"## {d['pfad']}")
        if d.get("zweck"):
            zeilen.append(f"_{d['zweck']}_")
        zeilen.append("")
        zeilen.append("```")
        for s in d["symbole"]:
            zeilen.append(f"{s['zeile']:>5}  {s['art']} {s['name']}")
        zeilen.append("```")
        zeilen.append("")
    ordner = wurzel / ".landkarte"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "symbole.md").write_text("\n".join(zeilen), "utf-8")


def bauen(wurzel: Path, modell: dict | None = None,
          nutzungsdaten: dict | None = None) -> dict:
    """KARTE.md, .landkarte/karte.json und .landkarte/symbole.md schreiben."""
    wurzel = wurzel.resolve()
    if wurzel in konfig.NIEMALS_PROJEKT:
        raise ValueError(f"{wurzel} ist ein Sammelordner, kein Projekt")
    modell = modell or scan.projekt_scannen(wurzel)
    nutzungsdaten = nutzungsdaten if nutzungsdaten is not None else chronik.nutzung()
    nutz_dateien = (nutzungsdaten.get("dateien") or {}).get(str(wurzel), {})

    notiz = notizen.laden(wurzel)
    kapitel = buch.kapitel_sammeln(wurzel)
    # spaet eingebunden: der Testleser bindet umgekehrt diese Datei ein
    from . import testleser as _tl
    schlagworte = _tl.schlagworte_laden(wurzel)

    # Fallen und Regeln: aus Notizen und aus allen Kapiteln zusammenziehen
    fallen = list(notiz.get("Fallen", []))
    regeln = list(notiz.get("Regeln", []))
    offen = list(notiz.get("Offen", []))
    for k in kapitel:
        for f in k.get("fallen", []):
            fallen.append(f"{f}  _({k['kopf'].get('datum','')})_")
        for r in k.get("regeln", []):
            regeln.append(f"{r}  _({k['kopf'].get('datum','')})_")
        for o in k.get("offen", []):
            offen.append(f"{o}  _({k['kopf'].get('datum','')})_")

    korrekturen = korrektur.laden(wurzel)
    fallen = korrektur.anwenden(fallen, korrekturen)
    regeln = korrektur.anwenden(regeln, korrekturen)
    offen = korrektur.anwenden(offen, korrekturen)

    git = modell.get("git") or {}
    z: list[str] = []
    z.append(f"# Landkarte: {modell['name']}")
    z.append("")
    if modell.get("zweck"):
        z.append(f"> {modell['zweck']}")
        z.append("")
    kopfteile = [
        f"Stand **{_zeit(modell['gescannt'])}**",
        f"{modell['anzahl_dateien']} Dateien",
        f"{modell['anzahl_zeilen']} Zeilen",
    ]
    if git.get("commit"):
        schmutz = f", {git['schmutzig']} geändert" if git.get("schmutzig") else ""
        kopfteile.append(f"git `{git.get('zweig','?')}@{git['commit']}`{schmutz}")
    z.append(" · ".join(kopfteile))
    z.append("")
    z.append(f"`{modell['wurzel']}`")
    z.append("")
    if git.get("letzter"):
        z.append(f"Letzter Commit: {git['letzter']}")
        z.append("")
    ausgelassen = modell.get("ausgelassen") or []
    if ausgelassen:
        z.append("Ausgelassen (von Git ignoriert oder in "
                 "`.landkarte/ignorieren.txt`): "
                 + ", ".join(f"`{x}`" for x in ausgelassen[:12]))
        z.append("")
    z.append("<!-- Diese Datei wird von `landkarte` erzeugt. Handschriftliches "
             "gehört in .landkarte/notizen.md, das bleibt beim Neubau erhalten. -->")
    z.append("")

    # --------------------------------------------------------- Spickzettel
    z.append("## Spickzettel")
    z.append("")
    befehle = modell.get("befehle") or []
    if befehle:
        z.append("**Befehle**")
        z.append("")
        z += _tabelle([(f"`{b['wie']}`", b["was"]) for b in befehle],
                      ("Befehl", "wofür"))
        z.append("")
    adressen = modell.get("adressen") or []
    if adressen:
        z.append("**Adressen und Hosts**")
        z.append("")
        for a in adressen:
            z.append(f"- `{a}`")
        z.append("")
    if notiz.get("Zugaenge"):
        z.append("**Zugänge** (nur Zeiger, nie Werte)")
        z.append("")
        for eintrag in notiz["Zugaenge"]:
            z.append(f"- {eintrag}")
        z.append("")

    # --------------------------------------------------------------- Fallen
    z.append("## Fallen")
    z.append("")
    if fallen:
        z.append("Hier wurde schon Zeit verloren. Vor dem Anfassen lesen.")
        z.append("")
        for f in fallen:
            z.append(f"- {f}")
    else:
        z.append("_Noch keine erfasst._")
    z.append("")

    z.append("## Regeln")
    z.append("")
    if regeln:
        for r in regeln:
            z.append(f"- {r}")
    else:
        z.append("_Noch keine._")
    z.append("")

    # ----------------------------------------------------------- Inhalt/Buch
    if kapitel:
        z.append("## Buch")
        z.append("")
        z.append(f"{len(kapitel)} Kapitel in `.landkarte/buch/`, neueste zuerst.")
        z.append("")
        z += _tabelle(
            [(f"`{k['datei']}`",
              f"{k['kopf'].get('titel','?')} — {k['kopf'].get('dauer','?')}, "
              f"{k['kopf'].get('fehlschlaege','0')} Fehlschläge"
              + _pruefmarke(k['kopf']))
             for k in kapitel[:25]],
            ("Kapitel", "Inhalt"))
        z.append("")
        if schlagworte:
            z.append("**Schlagworte zu den Kapiteln** — vom Testleser "
                     "nachgetragen, weil das Kapitel ohne sie nicht gefunden "
                     "wurde (`.landkarte/schlagworte.md`)")
            z.append("")
            for datei, begriffe in schlagworte.items():
                if begriffe:
                    z.append(f"- `{datei}`: " + ", ".join(begriffe))
            z.append("")

    # ----------------------------------------------------------- Wo liegt was
    z.append("## Wo liegt was")
    z += _baum(modell["dateien"], nutz_dateien)
    z.append("")

    # ------------------------------------------------------------- Symbole
    z.append("## Symbole der wichtigsten Dateien")
    z.append("")
    z.append("Python exakt über den Syntaxbaum; andere Sprachen über Textregeln, "
             "also oberste Ebene zuverlässig, Verschachteltes nicht. "
             "Vollständig in `.landkarte/symbole.md`.")
    z += _symbole(modell["dateien"], nutz_dateien)
    z.append("")

    # ----------------------------------------------------------- Verflechtung
    kanten = modell.get("kanten") or {}
    if kanten:
        z.append("## Verflechtung")
        z.append("")
        wichtig = sorted(kanten.items(), key=lambda kv: -len(kv[1]))[:20]
        for quelle, ziele in wichtig:
            z.append(f"- `{quelle}` → " + ", ".join(f"`{x}`" for x in ziele[:8]))
        z.append("")

    # ----------------------------------------------------------------- Offen
    z.append("## Offene Punkte")
    z.append("")
    if offen:
        for o in offen:
            z.append(f"- {o}")
        z.append("")
    marken = modell.get("markierungen") or []
    if marken:
        z.append("**Markierungen im Code**")
        z.append("")
        for m in marken[:30]:
            z.append(f"- `{m['pfad']}:{m['zeile']}` {m['art']}: {m['text']}")
        z.append("")
    if not offen and not marken:
        z.append("_Keine._")
        z.append("")

    if korrekturen:
        z.append("## Berichtigungen")
        z.append("")
        z.append("Später als falsch erkannt. Das Original bleibt im Kapitel "
                 "stehen, hier steht der richtige Sachverhalt.")
        z.append("")
        for k in reversed(korrekturen):
            z.append(f"- ~~{k['falsch'][:160]}~~")
            z.append(f"  **Richtig:** {k['richtig']}"
                     + (f" — {k['grund']}" if k.get("grund") else "")
                     + f"  _({k['datum']})_")
        z.append("")

    text = "\n".join(z) + "\n"
    (wurzel / "KARTE.md").write_text(text, "utf-8")

    ordner = wurzel / ".landkarte"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "karte.json").write_text(
        json.dumps(modell, ensure_ascii=False, indent=1), "utf-8")
    _symboldatei_schreiben(modell, wurzel)
    notizen.anlegen_wenn_fehlt(wurzel)

    # Zwischenspeicher fuer Suche und Regal
    konfig.PROJEKT_CACHE.mkdir(parents=True, exist_ok=True)
    knapp = {
        "name": modell["name"], "wurzel": modell["wurzel"],
        "zweck": modell["zweck"], "gescannt": modell["gescannt"],
        "anzahl_dateien": modell["anzahl_dateien"],
        "anzahl_zeilen": modell["anzahl_zeilen"], "git": modell["git"],
        "befehle": modell["befehle"], "adressen": modell["adressen"],
        "kapitel": len(kapitel), "fallen": len(fallen),
        "schlagworte": [
            {"kapitel_pfad": str(buch.buchordner(wurzel) / datei),
             "kapiteldatei": datei, "begriffe": begriffe}
            for datei, begriffe in schlagworte.items() if begriffe],
        "dateien": [{"pfad": d["pfad"], "zweck": d["zweck"],
                     "rang": d.get("rang", 0),
                     "symbole": [{"zeile": s["zeile"], "art": s["art"],
                                  "name": s["name"]} for s in d["symbole"]]}
                    for d in modell["dateien"] if d["symbole"] or d["zweck"]],
    }
    (konfig.PROJEKT_CACHE / f"{konfig.slug(wurzel)}.json").write_text(
        json.dumps(knapp, ensure_ascii=False), "utf-8")

    return {"karte": str(wurzel / "KARTE.md"), "dateien": modell["anzahl_dateien"],
            "dauer_ms": modell["dauer_ms"], "kapitel": len(kapitel),
            "fallen": len(fallen)}
