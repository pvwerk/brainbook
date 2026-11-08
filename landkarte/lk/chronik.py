"""Zweck: Rohprotokoll aller Werkzeugaufrufe lesen, auswerten, verdichten.

Geschrieben wird die Chronik vom Hook (jq, keine Token). Hier wird sie
nur gelesen: fuer die Nutzungszaehlung des Bibliothekars und als Rohstoff
fuer den Schreiber.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path

from . import konfig, schwaerzen as _schw

CHRONIK = konfig.LK_HEIM / "chronik"
SITZUNGEN = konfig.LK_HEIM / "sitzungen"

DATEI_WERKZEUGE = {"Edit", "Write", "Read", "NotebookEdit", "MultiEdit"}
# Nur diese ändern wirklich etwas. Die Trennung ist nötig, weil ein
# gemeinsamer Topf "geändert und gelesen" nicht entscheidbar ist - der
# Schiedsrichter hat genau das beim ersten echten Lauf gemeldet.
SCHREIB_WERKZEUGE = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

_WURZELN: list[str] | None = None


def _projektwurzeln() -> list[str]:
    """Bekannte Projektwurzeln, laengste zuerst - zum Zuordnen von cwd."""
    global _WURZELN
    if _WURZELN is not None:
        return _WURZELN
    wurzeln: list[str] = []
    if konfig.REGISTER.exists():
        try:
            reg = json.loads(konfig.REGISTER.read_text("utf-8"))
            wurzeln = [p["wurzel"] for p in reg.get("projekte", []) if p.get("wurzel")]
        except (OSError, json.JSONDecodeError, KeyError):
            wurzeln = []
    if not wurzeln and konfig.PROJEKT_CACHE.exists():
        for datei in konfig.PROJEKT_CACHE.glob("*.json"):
            try:
                wurzeln.append(json.loads(datei.read_text("utf-8"))["wurzel"])
            except (OSError, json.JSONDecodeError, KeyError):
                continue
    _WURZELN = sorted(set(wurzeln), key=len, reverse=True)
    return _WURZELN


def projektschluessel(ordner: str) -> str:
    """Unterordner auf die Projektwurzel zurechnen.

    Ohne das zaehlt Arbeit in app/ und in tests/ als zwei verschiedene
    Projekte, und die Rangfolge im Regal wird falsch.
    """
    if not ordner:
        return ""
    for wurzel in _projektwurzeln():
        if ordner == wurzel or ordner.startswith(wurzel + "/"):
            return wurzel
    return ordner


def tage(zurueck: int = 90) -> list[Path]:
    if not CHRONIK.exists():
        return []
    grenze = time.time() - zurueck * 86400
    aus = []
    for p in sorted(CHRONIK.glob("*.jsonl")):
        try:
            if p.stat().st_mtime >= grenze:
                aus.append(p)
        except OSError:
            continue
    return aus


def eintraege(zurueck: int = 90, sitzung: str | None = None,
              projekt: str | None = None):
    """Chronik-Eintraege als Generator."""
    for p in tage(zurueck):
        try:
            with p.open("r", encoding="utf-8", errors="replace") as f:
                for zeile in f:
                    zeile = zeile.strip()
                    if not zeile:
                        continue
                    try:
                        e = json.loads(zeile)
                    except json.JSONDecodeError:
                        continue
                    if sitzung and e.get("s") != sitzung:
                        continue
                    _schw.eintrag_schwaerzen(e)
                    if e.get("p"):
                        e["p"] = projektschluessel(e["p"])
                    if projekt and e.get("p") != projekt:
                        continue
                    yield e
        except OSError:
            continue


def _dateiziel(e: dict) -> str:
    ziel = (e.get("d") or "").strip()
    if not ziel:
        return ""
    if ziel.startswith("/"):
        projekt = e.get("p") or ""
        if projekt and ziel.startswith(projekt + "/"):
            return ziel[len(projekt) + 1:]
        return ziel
    return ziel


def nutzung(zurueck: int = 90) -> dict:
    """Wie oft wurde welches Projekt und welche Datei angefasst."""
    projekte: Counter = Counter()
    projekt_zuletzt: dict[str, int] = {}
    dateien: dict[str, Counter] = {}
    fehler: dict[str, Counter] = {}
    for e in eintraege(zurueck):
        projekt = e.get("p") or ""
        if not projekt:
            continue
        projekte[projekt] += 1
        projekt_zuletzt[projekt] = max(projekt_zuletzt.get(projekt, 0),
                                       int(e.get("t") or 0))
        ziel = _dateiziel(e)
        if ziel and e.get("w") in DATEI_WERKZEUGE:
            dateien.setdefault(projekt, Counter())[ziel] += 1
        if e.get("f"):
            fehler.setdefault(projekt, Counter())[ziel or e.get("w", "?")] += 1
    return {
        "projekte": dict(projekte),
        "zuletzt": projekt_zuletzt,
        "dateien": {k: dict(v) for k, v in dateien.items()},
        "fehler": {k: dict(v) for k, v in fehler.items()},
    }


def sitzung_verdichten(sitzung: str) -> dict:
    """Rohprotokoll einer Sitzung zu einem kompakten Bericht eindicken.

    Das ist die Vorarbeit fuer den Schreiber: aus hunderten Aufrufen
    werden wenige Kilobyte Fakten.
    """
    alle = list(eintraege(zurueck=30, sitzung=sitzung))
    if not alle:
        return {}
    alle.sort(key=lambda e: e.get("t") or 0)
    projekte = Counter(e.get("p") or "" for e in alle)
    hauptprojekt = projekte.most_common(1)[0][0] if projekte else ""

    dateien: Counter = Counter()
    gelesen: Counter = Counter()
    geaendert: Counter = Counter()
    fehler_je_datei: Counter = Counter()
    befehle: list[str] = []
    fehlschlaege: list[dict] = []
    for e in alle:
        ziel = _dateiziel(e)
        if e.get("w") in DATEI_WERKZEUGE and ziel:
            dateien[ziel] += 1
            if e["w"] in SCHREIB_WERKZEUGE:
                geaendert[ziel] += 1
            else:
                gelesen[ziel] += 1
        if e.get("w") == "Bash":
            b = (e.get("d") or "").strip()
            if b and b not in befehle:
                befehle.append(b[:200])
        if e.get("f"):
            if ziel:
                fehler_je_datei[ziel] += 1
            fehlschlaege.append({
                "nummer": len(fehlschlaege) + 1,
                "werkzeug": e.get("w"),
                "ziel": ziel or "",
                "fehler": (e.get("f") or "")[:300],
                "zeit": e.get("t"),
                "nach_sekunden": max(0, int((e.get("t") or 0)
                                            - (alle[0].get("t") or 0))),
            })
    return {
        "sitzung": sitzung,
        "projekt": hauptprojekt,
        "beginn": alle[0].get("t"),
        "ende": alle[-1].get("t"),
        "aufrufe": len(alle),
        "werkzeuge": dict(Counter(e.get("w") or "?" for e in alle).most_common()),
        "dateien": dict(dateien.most_common(40)),
        "geaendert": dict(geaendert.most_common(30)),
        "gelesen": dict(gelesen.most_common(30)),
        "fehler_je_datei": dict(fehler_je_datei),
        "befehle": befehle[:60],
        "fehlschlaege": fehlschlaege[:40],
        "projekte_beteiligt": dict(projekte.most_common()),
    }


def sitzungen_mit_aktivitaet(zurueck: int = 14) -> dict[str, dict]:
    """Je Sitzung: Anzahl Aufrufe, Fehler, Hauptprojekt, letzte Aktivitaet."""
    aus: dict[str, dict] = {}
    for e in eintraege(zurueck):
        s = e.get("s")
        if not s:
            continue
        d = aus.setdefault(s, {"aufrufe": 0, "fehler": 0, "projekte": Counter(),
                               "ende": 0})
        d["aufrufe"] += 1
        if e.get("f"):
            d["fehler"] += 1
        if e.get("p"):
            d["projekte"][e["p"]] += 1
        d["ende"] = max(d["ende"], int(e.get("t") or 0))
    for s, d in aus.items():
        d["projekt"] = d["projekte"].most_common(1)[0][0] if d["projekte"] else ""
        d["projekte"] = dict(d["projekte"])
    return aus


def kapitel_faellig(zurueck: int = 14, min_aufrufe: int = 8) -> list[dict]:
    """Sitzungen, die ein Kapitel verdienen und noch keins haben."""
    SITZUNGEN.mkdir(parents=True, exist_ok=True)
    jetzt = time.time()
    faellig = []
    for s, d in sitzungen_mit_aktivitaet(zurueck).items():
        if (SITZUNGEN / f"{s}.json").exists():
            continue
        if d["aufrufe"] < min_aufrufe and d["fehler"] == 0:
            continue
        # noch laufende Sitzungen auslassen (letzte Aktivitaet < 5 min)
        if jetzt - d["ende"] < 300:
            continue
        if not d["projekt"]:
            continue
        faellig.append({"sitzung": s, **d})
    faellig.sort(key=lambda x: x["ende"])
    return faellig


def abgeschlossen_merken(sitzung: str, inhalt: dict) -> None:
    SITZUNGEN.mkdir(parents=True, exist_ok=True)
    (SITZUNGEN / f"{sitzung}.json").write_text(
        json.dumps(inhalt, ensure_ascii=False, indent=2), "utf-8")
