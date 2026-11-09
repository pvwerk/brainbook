"""Zweck: Der Bibliothekar - Projekte finden, nach Nutzung sortieren, Regal schreiben.

Die Reihenfolge im Regal kommt nicht aus einer Schätzung, sondern aus der
Chronik: wie oft und wie kürzlich wurde in einem Projekt tatsächlich
gearbeitet. Was oft gebraucht wird, steht vorn.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from . import chronik, karte, konfig, regalwart, scan


def lesbarkeit(ordner: Path) -> str:
    """"lesbar", "verboten", "fehlt" oder "fehler" - der Unterschied zaehlt.

    Ein Ordner, den man nicht lesen DARF, ist nicht dasselbe wie ein Ordner,
    den es nicht mehr GIBT. Im ersten Fall muss der alte Stand bleiben, im
    zweiten gehoert das Projekt wirklich aus dem Regal.
    """
    try:
        with os.scandir(ordner) as eintraege:
            next(iter(eintraege), None)
        return "lesbar"
    except PermissionError:
        return "verboten"
    except FileNotFoundError:
        return "fehlt"
    except NotADirectoryError:
        return "fehlt"
    except OSError:
        return "fehler"


def projekte_finden(konf: dict | None = None,
                    zugriffsfehler: list[dict] | None = None) -> list[Path]:
    konf = konf or konfig.laden()
    ignorieren = set(konf.get("ignorieren", []))
    nicht = {konfig.ausklappen(p) for p in konf.get("nicht_scannen", [])}
    gefunden: list[Path] = []
    gesehen: set[Path] = set()

    for eintrag in konf.get("wurzeln", []):
        if isinstance(eintrag, str):
            eintrag = {"pfad": eintrag, "tiefe": 1}
        wurzel = konfig.ausklappen(eintrag["pfad"])
        tiefe = int(eintrag.get("tiefe", 1))
        if not wurzel.is_dir():
            continue
        kandidaten = [wurzel] if konfig.ist_projekt(wurzel) else []
        ebene = [wurzel]
        for _ in range(tiefe):
            naechste = []
            for ordner in ebene:
                try:
                    for e in os.scandir(ordner):
                        if not e.is_dir(follow_symlinks=False):
                            continue
                        if e.name in ignorieren or e.name.startswith("."):
                            continue
                        p = Path(e.path)
                        if p in nicht:
                            continue
                        naechste.append(p)
                        if konfig.ist_projekt(p):
                            kandidaten.append(p)
                except OSError as fehler:
                    # NICHT verschlucken. Unter macOS-TCC darf ein
                    # launchd-Dienst ~/Desktop erst mit Festplattenvollzugriff
                    # lesen; wer hier stillschweigend weitergeht, baut ein
                    # halbes Regal und ueberschreibt damit ein ganzes.
                    if zugriffsfehler is not None:
                        zugriffsfehler.append({
                            "ordner": str(ordner),
                            "fehler": type(fehler).__name__})
                    continue
            ebene = naechste
        for p in kandidaten:
            aufgeloest = p.resolve()
            if aufgeloest in gesehen:
                continue
            gesehen.add(aufgeloest)
            gefunden.append(aufgeloest)
    return sorted(gefunden, key=lambda p: str(p))


def rang_berechnen(wurzel: Path, nutz: dict, modell_knapp: dict) -> dict:
    """Platz im Regal: Nutzungshäufigkeit, Aktualität, Größe."""
    schluessel = str(wurzel)
    zugriffe = (nutz.get("projekte") or {}).get(schluessel, 0)
    zuletzt = (nutz.get("zuletzt") or {}).get(schluessel, 0)
    fehler = sum((nutz.get("fehler") or {}).get(schluessel, {}).values())

    tage_her = (time.time() - zuletzt) / 86400 if zuletzt else 999
    frische = max(0.0, 1.0 - min(tage_her, 60) / 60)
    punkte = zugriffe * 1.0 + frische * 150 + min(fehler, 40) * 1.5
    return {
        "punkte": round(punkte, 1),
        "zugriffe": zugriffe,
        "zuletzt": zuletzt,
        "tage_her": round(tage_her, 1) if zuletzt else None,
        "fehler": fehler,
    }


def regal_bauen(neu_scannen: bool = True, nur: list[Path] | None = None) -> dict:
    """Alle Projekte scannen und das Regal (LANDKARTE.md) schreiben."""
    konf = konfig.laden()
    nutz = chronik.nutzung()
    fehler_beim_scan: list[dict] = []
    projekte = (nur if nur is not None
                else projekte_finden(konf, fehler_beim_scan))

    eintraege: list[dict] = []
    for wurzel in projekte:
        cache = konfig.PROJEKT_CACHE / f"{konfig.slug(wurzel)}.json"
        knapp = None
        if neu_scannen:
            try:
                ergebnis = karte.bauen(wurzel, nutzungsdaten=nutz)
            except Exception as fehler:          # einzelnes Projekt darf nicht alles stoppen
                fehler_beim_scan.append({"projekt": str(wurzel),
                                         "fehler": f"{type(fehler).__name__}: {fehler}"})
                continue
        if cache.exists():
            try:
                knapp = json.loads(cache.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                knapp = None
        if knapp is None:
            continue
        knapp["rang"] = rang_berechnen(wurzel, nutz, knapp)
        eintraege.append(knapp)

    if nur is None:
        _verlorene_bewahren(eintraege, nutz, fehler_beim_scan)

    eintraege.sort(key=lambda e: -e["rang"]["punkte"])

    # Der Regalwart beschriftet die Regale, erkennt neue und verschwundene
    pflege = regalwart.pflegen({e["wurzel"]: e for e in eintraege})
    regalzustand = regalwart.laden().get("regale", {})
    for e in eintraege:
        r = regalzustand.get(e["wurzel"], {})
        e["gruppe"] = r.get("gruppe", "")
        e["aliase"] = r.get("aliase", [])
        e["faecher"] = r.get("faecher", [])
        e["verwechselbar_mit"] = [Path(x).name for x in
                                  r.get("verwechselbar_mit", [])]

    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    konfig.REGISTER.write_text(json.dumps({
        "gebaut": int(time.time()),
        "anzahl": len(eintraege),
        "scanfehler": fehler_beim_scan,
        "projekte": [{
            "name": e["name"], "wurzel": e["wurzel"], "zweck": e.get("zweck", ""),
            "rang": e["rang"], "dateien": e.get("anzahl_dateien"),
            "zeilen": e.get("anzahl_zeilen"), "kapitel": e.get("kapitel", 0),
            "fallen": e.get("fallen", 0), "git": e.get("git", {}),
            "gescannt": e.get("gescannt"), "gruppe": e.get("gruppe", ""),
            "aliase": e.get("aliase", []),
            "verwechselbar_mit": e.get("verwechselbar_mit", []),
        } for e in eintraege],
    }, ensure_ascii=False, indent=1), "utf-8")

    ziel = konfig.ausklappen(konf.get("register_ausgabe", "~/Projekte/LANDKARTE.md"))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(_regal_text(eintraege, fehler_beim_scan), "utf-8")

    return {"projekte": len(eintraege), "regal": str(ziel),
            "scanfehler": fehler_beim_scan,
            "regalereignisse": pflege.get("ereignisse", [])}


def _verlorene_bewahren(eintraege: list[dict], nutz: dict,
                        fehler: list[dict]) -> int:
    """Projekte zurueckholen, die nur wegen fehlender Leseerlaubnis fehlen.

    Vorfall 09.11.2026: der naechtliche Dienst baute das Regal auf 6 von 15
    Projekten zusammen - genau die ausserhalb von ~/Desktop. Ursache war
    macOS-TCC. `landkarte wo "Mahnung"` fand danach nichts mehr, obwohl es
    abends noch 16 Stellen fand. Der alte Stand ist besser als keiner.
    """
    if not konfig.REGISTER.exists():
        return 0
    try:
        alt = json.loads(konfig.REGISTER.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    vorhanden = {e.get("wurzel") for e in eintraege}
    bewahrt = 0
    for frueher in alt.get("projekte", []):
        wurzel = frueher.get("wurzel")
        if not wurzel or wurzel in vorhanden:
            continue
        zustand = lesbarkeit(Path(wurzel))
        if zustand in ("lesbar", "fehlt"):
            continue                  # wirklich weg oder gerade nicht gescannt
        cache = konfig.PROJEKT_CACHE / f"{konfig.slug(Path(wurzel))}.json"
        knapp = None
        if cache.exists():
            try:
                knapp = json.loads(cache.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                knapp = None
        if knapp is None:
            knapp = dict(frueher)     # Notnagel: der Registereintrag selbst
        knapp["unlesbar"] = True
        knapp["rang"] = rang_berechnen(Path(wurzel), nutz, knapp)
        eintraege.append(knapp)
        bewahrt += 1
        fehler.append({
            "projekt": wurzel,
            "fehler": f"Ordner nicht lesbar ({zustand}) - alter Stand behalten. "
                      "Unter macOS braucht der Dienst Festplattenvollzugriff: "
                      "Systemeinstellungen > Datenschutz & Sicherheit > "
                      "Festplattenvollzugriff"})
    return bewahrt


def _regal_text(eintraege: list[dict], scanfehler: list[dict]) -> str:
    z = ["# Regal \u2014 alle Projekte", "",
         f"Stand {datetime.now().strftime('%Y-%m-%d %H:%M')} \u00b7 "
         f"{len(eintraege)} Projekte \u00b7 nach Gruppen beschriftet, innerhalb "
         f"einer Gruppe nach tats\u00e4chlicher Nutzung sortiert (Chronik der "
         f"letzten 90 Tage).", "",
         "Erzeugt von `landkarte regal`. Je Projekt liegt die Karte in "
         "`<projekt>/KARTE.md`, das Buch in `<projekt>/.landkarte/buch/`. "
         "Dreistufig nachschlagen: `landkarte wo <begriff>`.", ""]

    # ---------------- Liste 1: Regale, nach Gruppen ----------------
    gruppen: dict[str, list[dict]] = {}
    for e in eintraege:
        gruppen.setdefault(e.get("gruppe") or "Sonstiges", []).append(e)

    z.append("## Liste 1 \u2014 Regale")
    z.append("")
    for gruppe in sorted(gruppen, key=lambda g: (-max(
            x["rang"]["punkte"] for x in gruppen[g]), g)):
        z.append(f"### {gruppe}")
        z.append("")
        z.append("| Projekt | Zuletzt | Zugriffe | Umfang | Kapitel | Fallen |")
        z.append("| --- | --- | --- | --- | --- | --- |")
        for e in gruppen[gruppe]:
            r = e["rang"]
            zuletzt = "\u2014"
            if r.get("zuletzt"):
                tage = r["tage_her"]
                zuletzt = "heute" if tage is not None and tage < 1 else f"vor {int(tage)} T"
            marke = " ⚠︎ alter Stand" if e.get("unlesbar") else ""
            z.append(f"| **{e['name']}**{marke} | {zuletzt} | {r['zugriffe']} | "
                     f"{e.get('anzahl_dateien','?')} Dateien / "
                     f"{e.get('anzahl_zeilen','?')} Z | "
                     f"{e.get('kapitel',0)} | {e.get('fallen',0)} |")
        z.append("")

    verwechselbar = [e for e in eintraege if e.get("verwechselbar_mit")]
    if verwechselbar:
        z.append("### Nicht verwechseln")
        z.append("")
        z.append("Diese Projekte hei\u00dfen \u00e4hnlich. Vor dem Nachsehen pr\u00fcfen, "
                 "in welchem Regal man steht.")
        z.append("")
        for e in verwechselbar:
            z.append(f"- **{e['name']}** \u2194 "
                     + ", ".join(f"`{x}`" for x in e["verwechselbar_mit"]))
        z.append("")

    # ---------------- Liste 2 und 3 je Projekt ----------------
    for e in eintraege:
        r = e["rang"]
        z.append(f"## {e['name']}")
        z.append("")
        if e.get("zweck"):
            z.append(f"> {e['zweck']}")
            z.append("")
        z.append(f"`{e['wurzel']}`")
        z.append("")
        kopf = [f"Gruppe **{e.get('gruppe') or 'Sonstiges'}**"]
        if e.get("aliase"):
            kopf.append("auch genannt: " + ", ".join(f"„{a}\u201c"
                                                     for a in e["aliase"][:6]))
        z.append(" \u00b7 ".join(kopf))
        z.append("")
        if e.get("verwechselbar_mit"):
            z.append(f"**Nicht verwechseln mit:** "
                     + ", ".join(f"`{x}`" for x in e["verwechselbar_mit"]))
            z.append("")
        teile = []
        git = e.get("git") or {}
        if git.get("commit"):
            teile.append(f"git `{git.get('zweig','?')}@{git['commit']}`")
            if git.get("schmutzig"):
                teile.append(f"{git['schmutzig']} ungesichert")
        if git.get("letzter"):
            teile.append(f"zuletzt committet: {git['letzter']}")
        if r.get("zugriffe"):
            teile.append(f"{r['zugriffe']} Werkzeugaufrufe in 90 Tagen")
        if r.get("fehler"):
            teile.append(f"{r['fehler']} Fehlschl\u00e4ge")
        if teile:
            z.append(" \u00b7 ".join(teile))
            z.append("")

        faecher = e.get("faecher") or []
        if faecher:
            z.append("**Liste 2 \u2014 F\u00e4cher**")
            z.append("")
            for f in faecher[:12]:
                beschreibung = f" \u2014 {f['zweck']}" if f.get("zweck") else ""
                z.append(f"- `{f['name']}` ({f['dateien']} Dateien, "
                         f"{f.get('symbole',0)} Symbole){beschreibung}")
            z.append("")

        befehle = e.get("befehle") or []
        if befehle:
            z.append("**Wichtigste Befehle**")
            z.append("")
            for b in befehle[:5]:
                z.append(f"- `{b['wie']}` \u2014 {b['was']}")
            z.append("")
        z.append(f"\u2192 [Liste 3: Inhaltsverzeichnis]({e['wurzel']}/KARTE.md)")
        z.append("")

    if scanfehler:
        z.append("## Projekte, die nicht gescannt werden konnten")
        z.append("")
        for f in scanfehler:
            z.append(f"- `{f['projekt']}` \u2014 {f['fehler']}")
        z.append("")
    return "\n".join(z) + "\n"
