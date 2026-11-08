"""Zweck: Chronik rückwirkend aus den Sitzungsprotokollen von Claude Code füllen.

Der Chronist schreibt erst mit, seit der Hook läuft. Auf der Platte liegen
aber Monate an Sitzungsprotokollen. Die werden hier nachgetragen, damit die
Bibliothek nicht leer startet.

Nachgetragene Einträge werden mit `q: "transkript"` gekennzeichnet. Das ist
wichtig: sie dürfen die Gegenprobe des Chronisten nicht bestätigen, denn sie
stammen aus derselben Quelle, gegen die geprüft wird.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import chronik, konfig, schwaerzen as _schw

MAX_JE_SITZUNG = 20000

FELDER = ("file_path", "path", "command", "pattern", "url", "notebook_path",
          "prompt", "query")


def _zeitstempel(text: str) -> int:
    if not text:
        return 0
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0


def transkripte(zurueck_tage: int = 365) -> list[Path]:
    wurzel = konfig.HEIM / ".claude" / "projects"
    if not wurzel.is_dir():
        return []
    grenze = time.time() - zurueck_tage * 86400
    aus: list[Path] = []
    for ordner, _unter, dateien in os.walk(wurzel):
        for name in dateien:
            if not name.endswith(".jsonl"):
                continue
            p = Path(ordner) / name
            try:
                if p.stat().st_mtime >= grenze:
                    aus.append(p)
            except OSError:
                continue
    return sorted(aus, key=lambda p: p.stat().st_mtime, reverse=True)


def eine_sitzung_lesen(pfad: Path) -> list[dict]:
    """Werkzeugaufrufe einer Protokolldatei als Chronik-Einträge."""
    aufrufe: dict[str, dict] = {}
    fehler: dict[str, str] = {}
    try:
        with pfad.open("r", encoding="utf-8", errors="replace") as f:
            for zeile in f:
                if '"tool_use"' not in zeile and '"tool_result"' not in zeile:
                    continue
                try:
                    e = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                if e.get("isSidechain"):
                    continue
                inhalt = (e.get("message") or {}).get("content")
                if not isinstance(inhalt, list):
                    continue
                for block in inhalt:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        if len(aufrufe) >= MAX_JE_SITZUNG:
                            continue
                        eingabe = block.get("input") or {}
                        ziel = ""
                        for feld in FELDER:
                            wert = eingabe.get(feld)
                            if wert:
                                ziel = str(wert)
                                break
                        aufrufe[block.get("id", "")] = {
                            "t": _zeitstempel(e.get("timestamp", "")),
                            "s": e.get("sessionId") or e.get("session_id") or "",
                            "i": block.get("id", ""),
                            "p": e.get("cwd", ""),
                            "w": block.get("name", ""),
                            "d": (_schw.schwaerzen(ziel) or "")[:300],
                            "q": "transkript",
                        }
                    elif block.get("type") == "tool_result" and block.get("is_error"):
                        rohtext = block.get("content")
                        if isinstance(rohtext, list):
                            rohtext = " ".join(
                                str(x.get("text", "")) for x in rohtext
                                if isinstance(x, dict))
                        fehler[block.get("tool_use_id", "")] = (
                            _schw.schwaerzen(str(rohtext)) or "")[:600]
    except OSError:
        return []
    aufrufe.pop("", None)
    for kennung, text in fehler.items():
        if kennung in aufrufe:
            aufrufe[kennung]["f"] = text
    return sorted(aufrufe.values(), key=lambda e: e["t"])


def nachtragen(zurueck_tage: int = 365, grenze: int | None = None) -> dict:
    """Alle Protokolle einlesen und fehlende Einträge in die Chronik schreiben."""
    chronik.CHRONIK.mkdir(parents=True, exist_ok=True)

    # was schon in der Chronik steht, nicht doppelt schreiben
    vorhanden: set[str] = set()
    for e in chronik.eintraege(zurueck=zurueck_tage + 1):
        if e.get("i"):
            vorhanden.add(e["i"])

    dateien = transkripte(zurueck_tage)
    if grenze:
        dateien = dateien[:grenze]

    nach_tag: dict[str, list[dict]] = defaultdict(list)
    sitzungen = 0
    neu = 0
    uebersprungen = 0
    for pfad in dateien:
        eintraege = eine_sitzung_lesen(pfad)
        if not eintraege:
            continue
        sitzungen += 1
        for e in eintraege:
            if e["i"] in vorhanden:
                uebersprungen += 1
                continue
            if not e["t"]:
                continue
            tag = datetime.fromtimestamp(e["t"]).strftime("%Y-%m-%d")
            nach_tag[tag].append(e)
            vorhanden.add(e["i"])
            neu += 1

    for tag, eintraege in nach_tag.items():
        datei = chronik.CHRONIK / f"{tag}.jsonl"
        eintraege.sort(key=lambda e: e["t"])
        with datei.open("a", encoding="utf-8") as f:
            for e in eintraege:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"protokolle": len(dateien), "sitzungen": sitzungen,
            "neu": neu, "schon_vorhanden": uebersprungen,
            "tage": len(nach_tag)}
