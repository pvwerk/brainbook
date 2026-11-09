"""Zweck: Die eine Regel, die vor jeder Aenderung gilt - an einer Stelle.

Drei Stellen brauchen denselben Wortlaut, und er darf nicht auseinanderlaufen:

  * die Anweisungsdatei des Menschen (CLAUDE.md, AGENTS.md, ...)
  * der Platzanweiser, der eine KI stoppt, die ihn nicht beachtet
  * die Vorstellung beim ersten Start

Darum steht er hier und nur hier. Eingehaengt wird er als markierter Block,
damit ein zweites Einbauen ihn ersetzt statt ihn zu verdoppeln, und damit
alles, was der Mensch selbst geschrieben hat, unangetastet bleibt.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

ANFANG = "<!-- landkarte:anfang - von `landkarte anweisung` gepflegt -->"
ENDE = "<!-- landkarte:ende -->"

UEBERSCHRIFT = "## Projektgedächtnis zuerst (Priorität 1)"

TEXT = """Wenn an einem **bestehenden Projekt** etwas angepasst oder geändert werden
soll, wird **zuerst** im Brainbook und in der Bibliothek nachgesehen, wo die
Sache liegt. Nicht anfangen, den Code zu lesen.

```sh
landkarte wo <begriff>      # Regal → Buch → Seite, also Projekt → Teil → Datei:Zeile
```

`<begriff>` darf alles sein: das eigene Wort dafür („ETM CRM"), ein
Dateiname, ein Funktionsname, eine Tabelle, ein Thema. Das Brainbook
übersetzt eigene Begriffe in Projektnamen, deshalb funktioniert auch, was
nirgends im Code steht.

Erst wenn das nichts hergibt, wird gesucht und gelesen. Was dabei auffällt,
gehört zurück in die Bibliothek — sonst muss es beim nächsten Mal wieder
erarbeitet werden:

```sh
landkarte notiz "Falle: ..." --art falle
landkarte merke "<mein Wort>" --ist <projektordner>
```

**Warum:** Code jedes Mal neu zu lesen kostet jedes Mal von vorn — bei einem
gewachsenen Projekt sind das Minuten bis Stunden, und das Gelesene ist nach
der Sitzung wieder weg. Das Verzeichnis beantwortet dieselbe Frage in
Sekunden und wird mit jeder Nutzung genauer."""


def block() -> str:
    return f"{ANFANG}\n\n{UEBERSCHRIFT}\n\n{TEXT}\n\n{ENDE}"


def kurzfassung() -> str:
    """Eine Zeile fuer Hooks und Alarmmeldungen."""
    return ("Vor dem Lesen von Code: `landkarte wo <begriff>` - das Verzeichnis "
            "nennt Projekt, Teil und Datei:Zeile. Erst wenn es nichts hergibt, "
            "selbst suchen.")


def enthalten(datei: Path) -> bool:
    try:
        return ANFANG in datei.read_text("utf-8", errors="replace")
    except OSError:
        return False


def einhaengen(datei: Path, sicherung: bool = True, oben: bool = True) -> str:
    """Den Block in eine Markdown-Datei einhaengen.

    Gibt zurueck: "angelegt", "ersetzt", "oben eingesetzt" oder "unveraendert".
    Vorhandener Text wird nie veraendert - nur der eigene Block dazwischen.

    `oben` setzt den Block direkt unter die Titelzeile. Das ist Absicht: eine
    Regel, die als Erstes gelten soll, darf nicht am Dateiende stehen, wo sie
    hinter allem anderen gelesen wird.
    """
    datei = Path(datei).expanduser()
    neu = block()

    if not datei.exists():
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(f"# Anweisungen\n\n{neu}\n", "utf-8")
        return "angelegt"

    vorhanden = datei.read_text("utf-8", errors="replace")
    if ANFANG in vorhanden and ENDE in vorhanden:
        vorne = vorhanden.split(ANFANG)[0]
        hinten = vorhanden.split(ENDE, 1)[1]
        ersetzt = vorne + neu + hinten
        if ersetzt == vorhanden:
            return "unveraendert"
        if sicherung:
            _sichern(datei)
        datei.write_text(ersetzt, "utf-8")
        return "ersetzt"

    if sicherung:
        _sichern(datei)
    zeilen = vorhanden.splitlines()
    if oben and zeilen and zeilen[0].startswith("# "):
        # Unter die Titelzeile, vor allem anderen.
        rest = zeilen[1:]
        while rest and not rest[0].strip():
            rest.pop(0)
        datei.write_text("\n".join([zeilen[0], "", neu, ""] + rest) + "\n", "utf-8")
        return "oben eingesetzt"
    if oben:
        datei.write_text(neu + "\n\n" + vorhanden, "utf-8")
        return "oben eingesetzt"
    getrennt = ("" if vorhanden.endswith("\n\n")
                else ("\n" if vorhanden.endswith("\n") else "\n\n"))
    datei.write_text(vorhanden + getrennt + neu + "\n", "utf-8")
    return "ergaenzt"


def _sichern(datei: Path) -> Path | None:
    """Eine Kopie in den Papierkorb legen, bevor eine fremde Datei angefasst wird."""
    try:
        ordner = Path.home() / ".Papierkorb-Claude" / "landkarte-anweisung"
        ordner.mkdir(parents=True, exist_ok=True)
        ziel = ordner / f"{datei.name}.{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(datei, ziel)
        return ziel
    except OSError:
        return None


def zieldatei(ki: str = "") -> Path:
    """Wohin die Regel bei dieser KI gehoert.

    Nur Claude Code liest eine Datei im Heimverzeichnis von selbst. Bei allen
    anderen entsteht eine Datei, die der Mensch seiner KI vorlegt.
    """
    kennung = (ki or "").strip().lower()
    if kennung in ("claude-code", "claude", "claudecode"):
        return Path.home() / ".claude" / "CLAUDE.md"
    if kennung == "codex":
        return Path.home() / ".codex" / "AGENTS.md"
    return Path.home() / ".landkarte" / "ANWEISUNG.md"
