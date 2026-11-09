"""Zweck: Haelt eine KI an, die Code liest, ohne vorher nachzuschlagen.

Der Platzanweiser steht am Eingang. Wer ins Regal greift, ohne ins
Verzeichnis gesehen zu haben, wird einmal angehalten - und bekommt die
Auskunft gleich mitgeliefert, damit das Anhalten niemanden aufhaelt.

Danach schweigt er und reicht nur noch nach: zu jeder neuen Datei, die zum
ersten Mal aufgeschlagen wird, den Zweck und die Symbole aus dem
Inhaltsverzeichnis. Das ist der Teil, den eine KI sonst durch Lesen
erarbeiten muesste.

Drei Regeln, von denen keine aufgeweicht wird:
  * Pro Projekt und Sitzung wird hoechstens EINMAL angehalten. Ein Waechter,
    der dauernd blockiert, wird abgeschaltet - und dann wirkt er nie.
  * Angehalten wird nur, wo es auch eine Auskunft gibt: ohne KARTE.md
    schweigt er.
  * Jeder Fehler endet in "durchlassen". Ein kaputter Waechter darf keine
    Sitzung lahmlegen.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import konfig

ZUSTAND = konfig.LK_HEIM / "nachgeschlagen.json"
VERFALL = 3 * 24 * 3600          # Sitzungen aelter als drei Tage wegwerfen

# Werkzeuge, bei denen jemand im Regal greift
LESEWERKZEUGE = {"Read", "Grep", "Glob", "Edit", "MultiEdit", "NotebookEdit",
                 "Bash"}

# Bash ist ausdruecklich dabei, und zwar aus Erfahrung: beim ersten Live-Test
# hat die KI den Waechter mit `cat -n datei.py` umgangen. Eine Tuer, die man
# nicht bewacht, ist die Tuer, die benutzt wird - zumal manche Umgebungen der
# KI vorgeben, Dateien mit cat und grep zu lesen statt mit dem Lesewerkzeug.
LESEBEFEHLE = {"cat", "head", "tail", "sed", "awk", "nl", "bat", "less",
               "more", "grep", "egrep", "fgrep", "rg", "ag", "ack", "view",
               "strings", "xxd", "od", "pr", "fold", "column", "tac", "rev"}

# Eigene Befehle sind kein heimliches Lesen, sondern Arbeit mit der
# Bibliothek. Geprueft wird NUR das Befehlswort, nie der ganze Befehlstext:
# sonst haette jeder Pfad, in dem "landkarte" vorkommt, die Wache
# ausgeschaltet - und das ist genau der Ordner des Werkzeugs selbst.
EIGENE = {"landkarte", "brainbook", "platzanweiser"}

# Welche Befehle als Nachschlagen zaehlen, entscheiden die Befehle selbst:
# sie rufen nachgeschlagen_merken(). Absichtlich NICHT dabei ist `digest` -
# den legt der Sitzungsstart-Hook von selbst vor, und was von selbst kommt,
# ist kein Nachschlagen.


# ------------------------------------------------------------------ Zustand

def sitzung() -> str:
    for name in ("LANDKARTE_SITZUNG", "CLAUDE_CODE_SESSION_ID",
                 "CLAUDE_SESSION_ID"):
        wert = os.environ.get(name)
        if wert:
            return wert
    return "ohne-sitzung"


def _laden() -> dict:
    try:
        daten = json.loads(ZUSTAND.read_text("utf-8"))
    except (OSError, ValueError):
        return {"sitzungen": {}}
    if not isinstance(daten, dict) or "sitzungen" not in daten:
        return {"sitzungen": {}}
    jetzt = time.time()
    daten["sitzungen"] = {
        k: v for k, v in daten["sitzungen"].items()
        if isinstance(v, dict) and jetzt - v.get("zeit", 0) < VERFALL}
    return daten


def _schreiben(daten: dict) -> None:
    try:
        ZUSTAND.parent.mkdir(parents=True, exist_ok=True)
        vorlaeufig = ZUSTAND.with_suffix(".json.neu")
        vorlaeufig.write_text(json.dumps(daten, ensure_ascii=False), "utf-8")
        vorlaeufig.replace(ZUSTAND)
    except OSError:
        pass


def _eintrag(daten: dict, kennung: str) -> dict:
    sitzungen = daten.setdefault("sitzungen", {})
    eintrag = sitzungen.setdefault(kennung, {})
    eintrag["zeit"] = time.time()
    eintrag.setdefault("nachgeschlagen", [])
    eintrag.setdefault("gestoppt", [])
    eintrag.setdefault("gezeigt", [])
    return eintrag


def nachgeschlagen_merken(projekt: str = "",
                          treffer: int | None = None) -> None:
    """Festhalten, dass in dieser Sitzung nachgeschlagen wurde.

    Wird von den Nachschlagebefehlen selbst gerufen - nicht aus dem Hook.
    So zaehlt nur echtes Nachschlagen, egal ob es die KI oder der Mensch tat.

    `treffer` ist die Zahl der Fundstellen. Daraus entsteht die Bilanz, die
    eine KI am Ende einer langen Aufgabe als `bb N uses` ausgibt - gezaehlt,
    nicht geschaetzt.
    """
    try:
        daten = _laden()
        eintrag = _eintrag(daten, sitzung())
        eintrag["nachgeschlagen"] = sorted(
            set(eintrag["nachgeschlagen"]) | {projekt or "*"})
        eintrag["abfragen"] = int(eintrag.get("abfragen", 0)) + 1
        if treffer is not None:
            eintrag["treffer"] = int(eintrag.get("treffer", 0)) + int(treffer)
            if treffer > 0:
                eintrag["ergiebig"] = int(eintrag.get("ergiebig", 0)) + 1
        _schreiben(daten)
    except Exception:                                 # noqa: BLE001
        pass


def bilanz(kennung: str = "") -> dict:
    """Wie oft diese Sitzung die Bibliothek benutzt hat - fuer `bb N uses`.

    Als Nutzung zaehlt alles, wobei die Bibliothek etwas geliefert hat:
    ergiebige Abfragen, nachgereichte Verzeichniseintraege und die Male, wo
    der Platzanweiser angehalten und die Auskunft mitgegeben hat.
    """
    eintrag = _laden()["sitzungen"].get(kennung or sitzung(), {})
    ergiebig = int(eintrag.get("ergiebig", 0))
    gezeigt = len(eintrag.get("gezeigt", []))
    gestoppt = len(eintrag.get("gestoppt", []))
    return {
        "abfragen": int(eintrag.get("abfragen", 0)),
        "ergiebig": ergiebig,
        "treffer": int(eintrag.get("treffer", 0)),
        "nachgereicht": gezeigt,
        "angehalten": gestoppt,
        "uses": ergiebig + gezeigt + gestoppt,
    }


def hat_nachgeschlagen(projekt: str, kennung: str = "") -> bool:
    eintrag = _laden()["sitzungen"].get(kennung or sitzung(), {})
    gesehen = set(eintrag.get("nachgeschlagen", []))
    return bool(gesehen & {projekt, "*"})


# ------------------------------------------------------------------ Auskunft

def _projektwurzel(pfad: Path) -> Path | None:
    stelle = pfad if pfad.is_dir() else pfad.parent
    for kandidat in [stelle, *stelle.parents]:
        if kandidat in konfig.NIEMALS_PROJEKT:
            return None
        if (kandidat / "KARTE.md").exists():
            return kandidat
    return None


def _karte(wurzel: Path) -> dict:
    try:
        return json.loads((wurzel / ".landkarte" / "karte.json")
                          .read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _datei_auskunft(karte: dict, relativ: str) -> list[str]:
    for d in karte.get("dateien", []):
        if d.get("pfad") == relativ:
            zeilen = []
            if d.get("zweck"):
                zeilen.append(f"Zweck: {d['zweck']}")
            symbole = d.get("symbole") or []
            if symbole:
                kurz = ", ".join(
                    f"{s.get('name')}:{s.get('zeile')}" if isinstance(s, dict)
                    else str(s) for s in symbole[:12])
                zeilen.append(f"Darin: {kurz}")
            return zeilen
    return []


def auskunft(wurzel: Path, ziel: Path | None, begriff: str) -> str:
    """Was die Bibliothek zu dieser Stelle sagt - ohne eine Datei zu lesen."""
    from . import notizen, suche
    karte = _karte(wurzel)
    zeilen = [f"Regal: {karte.get('name', wurzel.name)} — {wurzel}"]
    if karte.get("zweck"):
        zeilen.append(f"       {karte['zweck']}")

    if ziel is not None:
        try:
            relativ = str(ziel.resolve().relative_to(wurzel.resolve()))
        except ValueError:
            relativ = ziel.name
        eigen = _datei_auskunft(karte, relativ)
        if eigen:
            zeilen += ["", f"Seite {relativ}:"] + [f"  {z}" for z in eigen]

    if begriff:
        try:
            treffer = suche.finden(begriff, projekt=karte.get("name") or None,
                                   grenze=8)
        except Exception:                             # noqa: BLE001
            treffer = []
        if treffer:
            zeilen += ["", f'Inhaltsverzeichnis zu "{begriff}":']
            for t in treffer[:8]:
                ort = str(t["ort"]).replace(str(konfig.HEIM), "~")
                zeilen.append(f"  {t['art']:<12} {ort}")
                if t.get("text"):
                    zeilen.append(f"  {'':<12} {t['text'][:90]}")

    try:
        notiert = notizen.laden(wurzel)
    except Exception:                                 # noqa: BLE001
        notiert = {}
    fallen = notiert.get("Fallen") or notiert.get("fallen") or []
    if fallen:
        zeilen += ["", "Schon bekannte Fallen in diesem Projekt:"]
        zeilen += [f"  - {f[:150]}" for f in fallen[:5]]
    return "\n".join(zeilen)


# -------------------------------------------------------------------- Wache

def _aus_befehl(befehl: str) -> tuple[Path | None, str]:
    """Liest dieser Shell-Befehl eine Quelldatei? Dann welche.

    Zerlegt an Pipe, && und ; und sieht sich jedes Stueck einzeln an - sonst
    rutscht `cd X && cat y.py` durch.
    """
    import re as _re
    import shlex

    for stueck in _re.split(r"\|\||\||&&|;|\n", befehl):
        stueck = stueck.strip()
        if not stueck:
            continue
        try:
            woerter = shlex.split(stueck)
        except ValueError:
            woerter = stueck.split()
        if not woerter:
            continue
        erstes = Path(woerter[0]).name
        if erstes in ("sudo", "command", "env", "time", "nohup", "xargs"):
            woerter = woerter[1:]
            erstes = Path(woerter[0]).name if woerter else ""
        if erstes in EIGENE:
            return None, ""           # eigener Befehl: das IST Nachschlagen
        if erstes not in LESEBEFEHLE:
            continue
        for wort in woerter[1:]:
            if wort.startswith("-"):
                continue
            pfad = Path(wort).expanduser()
            if pfad.is_file():
                return pfad, pfad.stem
    return None, ""


def _ziel_aus_eingabe(werkzeug: str, eingabe: dict) -> tuple[Path | None, str]:
    """Welche Stelle wird angefasst und mit welchem Begriff."""
    if werkzeug == "Bash":
        befehl = eingabe.get("command")
        if not isinstance(befehl, str) or not befehl:
            return None, ""
        return _aus_befehl(befehl)
    for feld in ("file_path", "notebook_path", "path"):
        wert = eingabe.get(feld)
        if isinstance(wert, str) and wert:
            pfad = Path(wert).expanduser()
            begriff = eingabe.get("pattern") or pfad.stem
            return pfad, str(begriff)[:60]
    muster = eingabe.get("pattern")
    if isinstance(muster, str) and muster:
        return None, muster[:60]
    return None, ""


def pruefen(werkzeug: str, eingabe: dict, kennung: str = "",
            ordner: str = "") -> dict:
    """Die Entscheidung des Platzanweisers.

    Rueckgabe:
      {}                            durchlassen, nichts sagen
      {"hinweis": "..."}            durchlassen, Auskunft beilegen
      {"stopp": True, "grund": ...} anhalten, Auskunft als Begruendung
    """
    if werkzeug not in LESEWERKZEUGE:
        return {}
    if not konfig.laden().get("wache", True):
        return {}                     # per `landkarte wache --aus` abgeschaltet
    kennung = kennung or sitzung()
    ziel, begriff = _ziel_aus_eingabe(werkzeug, eingabe)
    if werkzeug == "Bash":
        # Ohne erkannte Quelldatei nichts tun: sonst wuerde jedes `ls` im
        # Projektordner anhalten, und der Waechter waere eine Plage.
        stelle = ziel
    else:
        stelle = ziel or (Path(ordner).expanduser() if ordner else None)
    if stelle is None:
        return {}

    # Die Bibliothek selbst zu lesen ist Nachschlagen, nicht Umgehen.
    text = str(stelle)
    if "/.landkarte/" in text or stelle.name in ("KARTE.md", "LANDKARTE.md"):
        nachgeschlagen_merken(str(_projektwurzel(stelle) or ""))
        return {}

    wurzel = _projektwurzel(stelle)
    if wurzel is None:
        return {}                     # kein kartografiertes Projekt
    projekt = str(wurzel)

    daten = _laden()
    eintrag = _eintrag(daten, kennung)
    schon_nachgeschlagen = bool(set(eintrag["nachgeschlagen"]) & {projekt, "*"})
    schon_gestoppt = projekt in eintrag["gestoppt"]

    if not schon_nachgeschlagen and not schon_gestoppt:
        eintrag["gestoppt"] = sorted(set(eintrag["gestoppt"]) | {projekt})
        _schreiben(daten)
        return {"stopp": True, "grund": _stopptext(wurzel, ziel, begriff)}

    # Ab hier nur noch nachreichen, und jede Datei nur einmal.
    if ziel is None:
        return {}
    marke = f"{projekt}|{ziel}"
    if marke in eintrag["gezeigt"]:
        return {}
    karte = _karte(wurzel)
    try:
        relativ = str(ziel.resolve().relative_to(wurzel.resolve()))
    except ValueError:
        return {}
    eigen = _datei_auskunft(karte, relativ)
    if not eigen:
        return {}
    eintrag["gezeigt"] = (eintrag["gezeigt"] + [marke])[-400:]
    _schreiben(daten)
    return {"hinweis": f"Aus dem Inhaltsverzeichnis zu {relativ}: "
                       + " | ".join(eigen)}


def _stopptext(wurzel: Path, ziel: Path | None, begriff: str) -> str:
    from . import anweisung
    kopf = ("Angehalten vom Platzanweiser: in diesem Projekt wurde in dieser "
            "Sitzung noch nicht im Verzeichnis nachgesehen, und es gibt eines. "
            + anweisung.kurzfassung())
    return (kopf + "\n\n" + auskunft(wurzel, ziel, begriff)
            + "\n\nDer naechste Zugriff geht durch - angehalten wird pro "
              "Projekt und Sitzung nur einmal. Wer lieber selbst nachschlaegt: "
              "`landkarte wo " + (begriff or "<begriff>") + "`.")
