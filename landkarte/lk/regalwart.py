"""Zweck: Der Regalwart - beschriftet und sortiert die Regale, erkennt neue.

Er loest das Verwechslungsproblem: pvwerk-crm, etm-gutachten und
PVWERK-CRM-tablet-app heissen aehnlich und gehoeren in verschiedene Regale.
Wer im falschen Regal nachsieht, findet etwas - nur das Falsche, und merkt es
nicht.

Dafuer fuehrt er drei Listen:
  1. Regal          welches Projekt
  2. Fach           welcher Teil des Projekts
  3. Inhalt         die genaue Stelle

Ausserdem schreibt er mit, wann ein Regal neu aufgebaut wurde und wann eines
verschwunden ist - damit nachvollziehbar bleibt, warum ein Buch wo steht.
"""

from __future__ import annotations

import difflib
import json
import re
import time
from datetime import datetime
from pathlib import Path

from . import konfig

REGALE = konfig.LK_HEIM / "regale.json"
JOURNAL = konfig.LK_HEIM / "regal-journal.md"

# Woerter, die kein Regal beschreiben und daher nicht als Alias taugen
FUELLWOERTER = {"app", "tool", "projekt", "project", "neu", "new", "test",
                "alt", "old", "backup", "kopie", "main", "src"}


UMSCHRIFT = str.maketrans({
    "\u00e4": "ae", "\u00f6": "oe", "\u00fc": "ue", "\u00df": "ss",
    "\u00c4": "ae", "\u00d6": "oe", "\u00dc": "ue",
    "\u00e9": "e", "\u00e8": "e", "\u00ea": "e", "\u00e1": "a",
    "\u00e0": "a", "\u00e2": "a", "\u00ed": "i", "\u00f3": "o",
    "\u00fa": "u", "\u00f1": "n", "\u00e7": "c",
})


def _normal(text: str) -> str:
    """Vergleichsform. Umlaute werden umgeschrieben, nicht verworfen -
    sonst wird aus "Kuechen-Lastmonitor" ein "k chen lastmonitor"."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower().translate(UMSCHRIFT)).strip()


def _wortteile(name: str) -> list[str]:
    teile = [t for t in re.split(r"[-_\s.]+", name.lower().translate(UMSCHRIFT))
             if t]
    return [t for t in teile if len(t) > 1]


def aliase_bilden(wurzel: Path, modell: dict, handgesetzt: list[str]) -> list[str]:
    """Namen, unter denen ein Projekt gemeint sein kann."""
    name = wurzel.name
    aus = {name.lower(), _normal(name)}
    teile = _wortteile(name)
    if teile:
        aus.add(" ".join(teile))
        # einzelne aussagekraeftige Wortteile als Alias, z.B. "gutachten"
        for t in teile:
            if len(t) >= 4 and t not in FUELLWOERTER:
                aus.add(t)
    # Titel aus der README
    fuer_titel = wurzel / "README.md"
    if fuer_titel.exists():
        try:
            for zeile in fuer_titel.read_text("utf-8", errors="replace").splitlines()[:12]:
                if zeile.startswith("# "):
                    titel = _normal(zeile[2:])
                    if 3 < len(titel) < 60:
                        aus.add(titel)
                    break
        except OSError:
            pass
    for h in handgesetzt:
        aus.add(_normal(h))
    aus.discard("")
    return sorted(aus)


def gruppe_bestimmen(wurzel: Path, konf: dict) -> str:
    handgesetzt = (konf.get("gruppen") or {})
    for muster, gruppe in handgesetzt.items():
        if muster.lower() in str(wurzel).lower():
            return gruppe
    teile = _wortteile(wurzel.name)
    if not teile:
        return "Sonstiges"
    erstes = teile[0]
    if erstes in FUELLWOERTER and len(teile) > 1:
        erstes = teile[1]
    return erstes.upper() if len(erstes) <= 6 else erstes.capitalize()


def _aehnlich(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normal(a), _normal(b)).ratio()


def verwechslungsgefahr(regale: dict) -> dict[str, list[str]]:
    """Projektpaare, die man verwechseln kann - nach Name und nach Aliasen."""
    pfade = list(regale)
    gefahr: dict[str, list[str]] = {p: [] for p in pfade}
    for i, a in enumerate(pfade):
        for b in pfade[i + 1:]:
            na, nb = regale[a]["name"], regale[b]["name"]
            punkte = _aehnlich(na, nb)
            gemeinsam = (set(_wortteile(na)) & set(_wortteile(nb))) - FUELLWOERTER
            if punkte >= 0.62 or len(gemeinsam) >= 1:
                gefahr[a].append(b)
                gefahr[b].append(a)
    return gefahr


def faecher_bilden(modell: dict) -> list[dict]:
    """Liste 2: die Teile eines Projekts - oberste Ordnerebene mit Zweck."""
    nach_fach: dict[str, dict] = {}
    for d in modell.get("dateien", []):
        teile = Path(d["pfad"]).parts
        fach = teile[0] if len(teile) > 1 else "(Wurzel)"
        if fach == ".landkarte":
            continue
        eintrag = nach_fach.setdefault(fach, {
            "name": fach, "dateien": 0, "zeilen": 0, "zweck": "",
            "wichtigste": [], "symbole": 0})
        eintrag["dateien"] += 1
        eintrag["zeilen"] += d.get("zeilen", 0)
        eintrag["symbole"] += len(d.get("symbole", []))
        eintrag["wichtigste"].append((d.get("rang", 0), d["pfad"],
                                     d.get("zweck", "")))

    for fach, eintrag in nach_fach.items():
        eintrag["wichtigste"].sort(key=lambda x: -x[0])
        # Zweck des Fachs: eigene README, sonst Zweck der wichtigsten Datei
        fuer_zweck = ""
        for rang, pfad, zweck in eintrag["wichtigste"]:
            if Path(pfad).name.lower() in ("readme.md", "index.md", "notes.md"):
                fuer_zweck = zweck
                break
        if not fuer_zweck:
            for rang, pfad, zweck in eintrag["wichtigste"]:
                if zweck:
                    fuer_zweck = zweck
                    break
        eintrag["zweck"] = fuer_zweck
        eintrag["wichtigste"] = [p for _, p, _ in eintrag["wichtigste"][:5]]
    return sorted(nach_fach.values(), key=lambda f: (-f["symbole"], -f["dateien"]))


def laden() -> dict:
    if not REGALE.exists():
        return {"gepflegt": 0, "regale": {}}
    try:
        return json.loads(REGALE.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"gepflegt": 0, "regale": {}}


def pflegen(modelle: dict[str, dict]) -> dict:
    """Regale beschriften, neue aufbauen, verschwundene vermerken.

    modelle: {pfad: knappes Scan-Modell}
    """
    konf = konfig.laden()
    zustand = laden()
    alt = zustand.get("regale", {})
    jetzt = int(time.time())
    neu: dict[str, dict] = {}
    ereignisse: list[str] = []

    handgesetzte_aliase = konf.get("aliase") or {}

    for pfad, modell in modelle.items():
        wurzel = Path(pfad)
        vorher = alt.get(pfad)
        eintrag = {
            "name": modell.get("name") or wurzel.name,
            "pfad": pfad,
            "gruppe": gruppe_bestimmen(wurzel, konf),
            "aliase": aliase_bilden(wurzel, modell,
                                    handgesetzte_aliase.get(pfad, [])
                                    or handgesetzte_aliase.get(wurzel.name, [])),
            "zweck": modell.get("zweck", ""),
            "faecher": faecher_bilden(modell),
            "dateien": modell.get("anzahl_dateien", 0),
            "zeilen": modell.get("anzahl_zeilen", 0),
            "kapitel": modell.get("kapitel", 0),
            "erstmals_gesehen": (vorher or {}).get("erstmals_gesehen", jetzt),
            "zuletzt_gesehen": jetzt,
            "verschwunden": False,
        }
        neu[pfad] = eintrag
        if not vorher:
            ereignisse.append(
                f"**Regal aufgebaut:** `{eintrag['name']}` in Gruppe "
                f"{eintrag['gruppe']} — {eintrag['dateien']} Dateien, "
                f"{len(eintrag['faecher'])} Fächer. Aliase: "
                f"{', '.join(eintrag['aliase'][:6])}")
        else:
            alte_faecher = {f["name"] for f in vorher.get("faecher", [])}
            neue_faecher = {f["name"] for f in eintrag["faecher"]} - alte_faecher
            weg = alte_faecher - {f["name"] for f in eintrag["faecher"]}
            if neue_faecher:
                ereignisse.append(f"**Neues Fach** in `{eintrag['name']}`: "
                                  + ", ".join(sorted(neue_faecher)))
            if weg:
                ereignisse.append(f"**Fach verschwunden** in `{eintrag['name']}`: "
                                  + ", ".join(sorted(weg)))

    # verschwundene Regale behalten, aber kennzeichnen
    for pfad, vorher in alt.items():
        if pfad in neu:
            continue
        vorher["verschwunden"] = True
        if not Path(pfad).is_dir():
            if not vorher.get("abgemeldet"):
                ereignisse.append(f"**Regal verschwunden:** `{vorher.get('name')}` "
                                  f"({pfad}) ist nicht mehr da")
                vorher["abgemeldet"] = jetzt
        neu[pfad] = vorher

    gefahr = verwechslungsgefahr({p: e for p, e in neu.items()
                                  if not e.get("verschwunden")})
    for pfad, andere in gefahr.items():
        neu[pfad]["verwechselbar_mit"] = andere
        if andere and not alt.get(pfad, {}).get("verwechselbar_mit"):
            namen = ", ".join(Path(a).name for a in andere)
            ereignisse.append(f"**Verwechslungsgefahr** bei `{neu[pfad]['name']}`: "
                              f"heißt ähnlich wie {namen}")

    zustand = {"gepflegt": jetzt, "regale": neu}
    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    REGALE.write_text(json.dumps(zustand, ensure_ascii=False, indent=1), "utf-8")

    if ereignisse:
        kopf = "" if JOURNAL.exists() else (
            "# Regal-Journal\n\nWas der Regalwart verändert hat. Nur angehängt.\n")
        with JOURNAL.open("a", encoding="utf-8") as f:
            if kopf:
                f.write(kopf)
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for e in ereignisse:
                f.write(f"- {e}\n")
    return {"regale": len(neu), "ereignisse": ereignisse}


# ----------------------------------------------------------- Dreistufig suchen


def regal_finden(begriff: str, hier: Path | None = None) -> list[dict]:
    """Liste 1: welches Projekt ist gemeint."""
    zustand = laden()
    begriff_n = _normal(begriff)
    worte = set(begriff_n.split())
    treffer: list[dict] = []
    hier_pfad = str(hier.resolve()) if hier else ""

    for pfad, e in zustand.get("regale", {}).items():
        if e.get("verschwunden"):
            continue
        punkte = 0.0
        grund = ""
        for alias in e.get("aliase", []):
            if alias == begriff_n:
                punkte = max(punkte, 100); grund = f"Alias „{alias}\""
            elif begriff_n and begriff_n in alias:
                punkte = max(punkte, 80); grund = grund or f"Alias „{alias}\""
            elif alias in begriff_n:
                punkte = max(punkte, 70); grund = grund or f"Alias „{alias}\""
            else:
                gemeinsam = worte & set(alias.split())
                if gemeinsam:
                    punkte = max(punkte, 45 + 10 * len(gemeinsam))
                    grund = grund or f"Wörter {', '.join(sorted(gemeinsam))}"
        if _normal(e.get("gruppe", "")) in worte:
            punkte = max(punkte, 60); grund = grund or f"Gruppe {e['gruppe']}"
        if e.get("zweck") and begriff_n and begriff_n in _normal(e["zweck"]):
            punkte = max(punkte, 50); grund = grund or "Zweckbeschreibung"
        if punkte <= 0:
            continue
        if hier_pfad and (hier_pfad == pfad or hier_pfad.startswith(pfad + "/")):
            punkte += 25
            grund += " · du arbeitest hier"
        treffer.append({"pfad": pfad, "name": e["name"], "gruppe": e.get("gruppe"),
                        "zweck": e.get("zweck", ""), "punkte": punkte,
                        "grund": grund,
                        "verwechselbar_mit": [Path(x).name for x in
                                              e.get("verwechselbar_mit", [])],
                        "faecher": e.get("faecher", [])})
    treffer.sort(key=lambda t: -t["punkte"])
    return treffer


def fach_finden(pfad: str, begriff: str) -> list[dict]:
    """Liste 2: welcher Teil des Projekts."""
    zustand = laden()
    e = zustand.get("regale", {}).get(pfad)
    if not e:
        return []
    begriff_n = _normal(begriff)
    worte = set(begriff_n.split())
    aus = []
    for fach in e.get("faecher", []):
        punkte = 0.0
        name_n = _normal(fach["name"])
        if begriff_n and (begriff_n in name_n or name_n in begriff_n):
            punkte = 90
        elif worte & set(name_n.split()):
            punkte = 60
        elif fach.get("zweck") and begriff_n and begriff_n in _normal(fach["zweck"]):
            punkte = 50
        if punkte:
            aus.append({**fach, "punkte": punkte})
    if not aus:                      # kein Namenstreffer: nach Gewicht anbieten
        aus = [{**f, "punkte": 0} for f in e.get("faecher", [])[:6]]
    aus.sort(key=lambda f: (-f["punkte"], -f.get("symbole", 0)))
    return aus
