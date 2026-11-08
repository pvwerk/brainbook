"""Zweck: Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt.

Harte Grenze: 10 000 Zeichen nimmt der Hook an, Ziel sind 4 000. Es muss das
Nötigste sein, damit kein Kontext verschwendet wird, aber genug, dass vor dem
ersten Werkzeugaufruf klar ist, wo was liegt und wo die Fallen sind.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import buch, chronik, konfig, korrektur, notizen, regalwart

GRENZE = 7500


def _kuerzen(zeilen: list[str], grenze: int = GRENZE) -> str:
    text = "\n".join(zeilen)
    if len(text) <= grenze:
        return text
    aus: list[str] = []
    laenge = 0
    for z in zeilen:
        if laenge + len(z) + 1 > grenze - 80:
            aus.append("")
            aus.append("… gekürzt. Vollständig in KARTE.md.")
            break
        aus.append(z)
        laenge += len(z) + 1
    return "\n".join(aus)


def bauen(wurzel: Path) -> str:
    """Auszug für ein Projekt. Leerer Text, wenn es keine Karte gibt."""
    wurzel = wurzel.resolve()
    karte_json = wurzel / ".landkarte" / "karte.json"
    if not karte_json.exists():
        return ""
    try:
        modell = json.loads(karte_json.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""

    notiz = notizen.laden(wurzel)
    kapitel = buch.kapitel_sammeln(wurzel)
    nutz = chronik.nutzung(zurueck=60)
    nutz_dateien = (nutz.get("dateien") or {}).get(str(wurzel), {})

    alter_tage = (datetime.now() - datetime.fromtimestamp(modell["gescannt"])).days
    z: list[str] = []
    z.append(f"LANDKARTE {modell['name']} — {modell['wurzel']}")
    if modell.get("zweck"):
        z.append(modell["zweck"])
    git = modell.get("git") or {}
    kopf = [f"{modell['anzahl_dateien']} Dateien", f"{modell['anzahl_zeilen']} Zeilen"]
    if git.get("commit"):
        kopf.append(f"git {git.get('zweig','?')}@{git['commit']}")
        if git.get("schmutzig"):
            kopf.append(f"{git['schmutzig']} ungesichert")
    kopf.append(f"Karte {alter_tage} Tage alt" if alter_tage else "Karte von heute")
    z.append(" · ".join(kopf))
    z.append("")

    befehle = modell.get("befehle") or []
    if befehle:
        z.append("BEFEHLE")
        for b in befehle[:12]:
            z.append(f"  {b['wie']}   # {b['was']}")
        z.append("")

    adressen = modell.get("adressen") or []
    if adressen:
        z.append("ADRESSEN: " + " · ".join(adressen[:8]))
        z.append("")

    korrekturen = korrektur.laden(wurzel)
    fallen = list(notiz.get("Fallen", []))
    for k in kapitel:
        fallen += k.get("fallen", [])
    fallen = korrektur.anwenden(fallen, korrekturen, fuer_auszug=True)
    if fallen:
        z.append("FALLEN — hier ging schon Zeit verloren:")
        for f in fallen[:14]:
            z.append(f"  - {f}")
        z.append("")

    regeln = list(notiz.get("Regeln", []))
    for k in kapitel:
        regeln += k.get("regeln", [])
    regeln = korrektur.anwenden(regeln, korrekturen, fuer_auszug=True)
    if regeln:
        z.append("REGELN aus früheren Sitzungen:")
        for r in regeln[:12]:
            z.append(f"  - {r}")
        z.append("")

    if notiz.get("Zugaenge"):
        z.append("ZUGAENGE (Zeiger): " + " · ".join(notiz["Zugaenge"][:6]))
        z.append("")

    dateien = modell.get("dateien") or []
    rang = sorted(dateien,
                  key=lambda d: -(d.get("rang", 0) + nutz_dateien.get(d["pfad"], 0) * 1.5))
    z.append("WICHTIGSTE DATEIEN")
    for d in rang[:16]:
        zweck = d.get("zweck") or ""
        zusatz = ""
        if nutz_dateien.get(d["pfad"], 0) >= 5:
            zusatz = f" [{nutz_dateien[d['pfad']]}x]"
        z.append(f"  {d['pfad']}{zusatz}" + (f" — {zweck}" if zweck else ""))
    z.append("")

    offen = list(notiz.get("Offen", []))
    for k in kapitel[:3]:
        offen += k.get("offen", [])
    if offen:
        z.append("OFFEN")
        for o in offen[:10]:
            z.append(f"  - {o}")
        z.append("")

    if kapitel:
        z.append(f"BUCH: {len(kapitel)} Kapitel in .landkarte/buch/ — zuletzt "
                 f"\"{kapitel[0]['kopf'].get('titel','?')}\" "
                 f"({kapitel[0]['kopf'].get('datum','?')})")
        z.append("")

    z.append("Mehr: KARTE.md (Inhaltsverzeichnis) · .landkarte/symbole.md "
             "(alle Symbole) · landkarte finde <begriff> (über alle Projekte) · "
             "landkarte notiz \"...\" (Falle oder Entscheidung festhalten)")
    return _kuerzen(z)
