"""Zweck: Falsches Wissen richtigstellen, ohne das Original zu löschen.

Das Rohprotokoll und die Kapitel werden nie verändert - sonst verliert der
Schiedsrichter die Grundlage, an der er Streitfälle entscheidet. Stattdessen
kommt ein Korrektureintrag daneben: der falsche Satz wird in Karte und Auszug
durchgestrichen gezeigt, mit dem richtigen Sachverhalt dahinter.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date
from pathlib import Path

DATEI = "korrekturen.jsonl"


def pfad(wurzel: Path) -> Path:
    return wurzel / ".landkarte" / DATEI


def _kern(text: str) -> str:
    """Vergleichsform: ohne Auszeichnung, ohne Datumsanhang, zusammengezogen."""
    t = re.sub(r"_\(\d{4}-\d{2}-\d{2}\)_\s*$", "", text)
    t = re.sub(r"[*_`~]", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def anlegen(wurzel: Path, falsch: str, richtig: str, grund: str = "") -> Path:
    p = pfad(wurzel)
    p.parent.mkdir(parents=True, exist_ok=True)
    eintrag = {
        "zeit": int(time.time()),
        "datum": date.today().isoformat(),
        "falsch": falsch.strip(),
        "kern": _kern(falsch),
        "richtig": richtig.strip(),
        "grund": grund.strip(),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    return p


def laden(wurzel: Path) -> list[dict]:
    p = pfad(wurzel)
    if not p.exists():
        return []
    aus = []
    try:
        for zeile in p.read_text("utf-8").splitlines():
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                aus.append(json.loads(zeile))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return aus


def anwenden(eintraege: list[str], korrekturen: list[dict],
             fuer_auszug: bool = False) -> list[str]:
    """Falsche Einträge markieren oder (für den Auszug) ersetzen."""
    if not korrekturen:
        return eintraege
    aus: list[str] = []
    for eintrag in eintraege:
        kern = _kern(eintrag)
        treffer = None
        for k in korrekturen:
            if not k.get("kern"):
                continue
            if k["kern"] in kern or kern in k["kern"] or (
                    len(k["kern"]) > 25 and k["kern"][:40] in kern):
                treffer = k
                break
        if not treffer:
            aus.append(eintrag)
            continue
        if fuer_auszug:
            aus.append(f"{treffer['richtig']}  [berichtigt {treffer['datum']}]")
        else:
            grund = f" — {treffer['grund']}" if treffer.get("grund") else ""
            aus.append(f"~~{eintrag}~~  \n  **Richtig:** {treffer['richtig']}"
                       f"  _(berichtigt {treffer['datum']}{grund})_")
    return aus
