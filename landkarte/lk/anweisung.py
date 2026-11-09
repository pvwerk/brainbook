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
Sekunden und wird mit jeder Nutzung genauer.

### Sag jedes Mal, ob die Bibliothek etwas hergab

Bei **jeder** Anfrage beginnt die Antwort mit einer dieser Zeilen — so ist auf
den ersten Blick zu sehen, ob die Bibliothek benutzt wurde und ob sie etwas
wusste:

```
bb false                  nichts in der Bibliothek gefunden
bb true 7 Einträge        7 Fundstellen gefunden und benutzt
```

Die Zahl wird nicht geschätzt. `landkarte bb <begriff>` schlägt nach **und**
gibt die Zeile fertig aus:

```sh
landkarte bb "mahnung"
→ bb true 19 Einträge
```

Steht da `bb false`, ist das ein Befund und keine Panne: die Bibliothek hat
eine Lücke. Was dann erarbeitet wird, gehört mit `landkarte notiz` oder
`landkarte merke` hinein, damit beim nächsten Mal `bb true` dasteht.

### Nach einer langen Aufgabe: Bilanz

Am Ende einer längeren Aufgabe kommt eine Zeile dazu — wie oft die Bibliothek
in dieser Sitzung überhaupt etwas geliefert hat:

```sh
landkarte bb --bilanz
→ bb 12 uses
```

Gezählt werden ergiebige Abfragen, nachgereichte Verzeichniseinträge und die
Male, in denen der Platzanweiser angehalten und die Auskunft mitgegeben hat.

## Zugangsdaten gehören in den Tresor, nicht in den Text

Passwörter, Token und Schlüssel werden **nie** ausgeschrieben — weder in eine
Antwort noch in eine Datei noch in eine Befehlszeile. Sie liegen verschlüsselt
im Tresor und werden von dort geholt:

```sh
landkarte tresor liste              was drin ist (ohne die Geheimnisse)
landkarte tresor einlegen <name>    ablegen, Eingabe verdeckt
landkarte tresor holen <name>       herausholen, nur zum Weiterreichen
```

Weitergereicht wird über **stdin oder eine Umgebungsvariable**, nie als
Argument auf der Kommandozeile — dort steht es in der Prozessliste und im
Sitzungsprotokoll:

```sh
landkarte tresor holen nas-passwort | ssh server "..."     richtig
ssh server --password "$(landkarte tresor holen nas)"      falsch
```

Die **Tresorwache** läuft bei jeder Eingabe mit. Erkennt sie Zugangsdaten,
legt sie diese ab und ersetzt sie im Sitzungsprotokoll durch `[Tresor: name]`.

**Sie ist die einzige Stelle, die am Sitzungsprotokoll etwas ändern darf.**
Sonst wird daran nichts gelöscht, nichts umgeschrieben, nichts gekürzt — von
niemandem und aus keinem Grund. Wer aufräumen will, nimmt
`landkarte tresor saeubern`; das ersetzt nur Geheimnisse und legt vorher eine
Kopie in `~/.Papierkorb-Claude/tresorwache/`.

## Offene Punkte stehen im Verzeichnis, nicht im Kopf

Was nicht fertig wurde, wird aufgeschrieben — sonst ist es nach der Sitzung
weg:

```sh
landkarte aufgaben                        alle offenen Punkte
landkarte aufgaben eintragen "..."        einen Punkt aufnehmen
landkarte aufgaben erledigt <kennung>     abhaken
```

Gesammelt wird aus `OFFEN.md`, `TODO.md`, unerledigten `- [ ]`-Haken und
eigenen Einträgen. Wird ein Punkt in seiner Datei erledigt, verschwindet er
hier von selbst. **Am Ende einer Aufgabe gehört jeder nicht fertiggestellte
Punkt dort hinein** — ausdrücklich benannt, nicht stillschweigend liegen
gelassen."""


def block() -> str:
    return f"{ANFANG}\n\n{UEBERSCHRIFT}\n\n{TEXT}\n\n{ENDE}"


def kurzfassung() -> str:
    """Eine Zeile fuer Hooks und Alarmmeldungen."""
    return ("Vor dem Lesen von Code: `landkarte bb <begriff>` - das Verzeichnis "
            "nennt Projekt, Teil und Datei:Zeile und liefert die Signalzeile "
            "(`bb true N Eintraege` / `bb false`) fuer die Antwort gleich mit. "
            "Erst wenn es nichts hergibt, selbst suchen.")


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
