"""Zweck: Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen.

Die einzige Stelle im Werkzeug, die ein Sprachmodell braucht: aus Fakten
("Datei X geaendert, Befehl Y schlug fehl") wird Bedeutung ("Ziel war Z,
Falle war Q, Regel daraus ist R"). Alles andere rechnet.

Der Aufruf bekommt bewusst nur den verdichteten Bericht, nicht das ganze
Sitzungsprotokoll: wenige Kilobyte statt Megabyte, damit es Bruchteile
eines Cents kostet.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import date, datetime
from pathlib import Path

from . import chronik, konfig

STANDARD_MODELL = "sonnet"

ANWEISUNG = """Du schreibst das Kapitel eines Arbeitsbuchs. Jedes Kapitel haelt \
eine Arbeitssitzung so fest, dass ein spaeterer Leser in zwei Minuten versteht, \
was getan wurde und welche Fallen es gab.

Unten steht das MASCHINENPROTOKOLL einer Sitzung: welche Dateien angefasst, \
welche Befehle ausgefuehrt wurden und welche fehlschlugen. Es ist die einzige \
Quelle. Schreibe ausschliesslich, was daraus hervorgeht.

Harte Regeln:
- Nichts erfinden. Was das Protokoll nicht sagt, steht nicht im Kapitel.
- Wenn du etwas nur vermutest, schreibe es als Vermutung oder lass es weg.
- Keine Passwoerter, Token, Schluessel oder Zugangsdaten uebernehmen, auch \
wenn sie im Protokoll stehen. Stattdessen: "Zugangsdaten in <Datei>".
- Deutsch. Knapp. Keine Einleitung, keine Zusammenfassung am Ende.
- Genau die vorgegebene Struktur, keine zusaetzlichen Ueberschriften.

Antworte NUR mit dem Kapitel in genau diesem Aufbau:

TITEL: <eine Zeile, max 60 Zeichen, was in dieser Sitzung geschah>

## Ziel
<1-3 Saetze: woran gearbeitet wurde. Aus den Dateien und Befehlen ableiten.>

## Vorgehen
<3-8 Stichpunkte in zeitlicher Reihenfolge: was gemacht wurde, mit Dateinamen.>

## Fallen
<Je Fehlschlag ein Stichpunkt, Form: **kurze Benennung** -- was schiefging und \
woran es lag. Nur echte Fehlschlaege aus dem Protokoll. Wenn keine: "keine">

## Regeln daraus
<Stichpunkte: was man beim naechsten Mal wissen muss, damit die Falle nicht \
wiederkommt. Nur was aus den Fallen folgt. Wenn keine: "keine">

## Offen
<Stichpunkte: was erkennbar unfertig blieb. Wenn nichts erkennbar: "nichts erkennbar">
"""


def _dauer(sek: float) -> str:
    sek = int(sek)
    if sek < 60:
        return f"{sek}s"
    stunden, rest = divmod(sek, 3600)
    minuten = rest // 60
    return f"{stunden}h {minuten}min" if stunden else f"{minuten}min"


def bericht_text(bericht: dict) -> str:
    """Den verdichteten Bericht als Text fuer das Modell."""
    z = []
    z.append(f"Projekt: {bericht.get('projekt')}")
    beginn = bericht.get("beginn") or 0
    ende = bericht.get("ende") or 0
    if beginn:
        z.append("Beginn: " + datetime.fromtimestamp(beginn).strftime("%Y-%m-%d %H:%M"))
        z.append("Dauer: " + _dauer(ende - beginn))
    z.append(f"Werkzeugaufrufe: {bericht.get('aufrufe')}")
    mit = bericht.get("projekte_beteiligt") or {}
    if len(mit) > 1:
        z.append("Weitere beteiligte Ordner: " +
                 ", ".join(k for k in list(mit)[1:6] if k))

    z.append("\nGEAENDERTE DATEIEN (geschrieben oder bearbeitet; "
             "Datei: Anzahl Schreibzugriffe):")
    fehler_je_datei = bericht.get("fehler_je_datei") or {}
    for datei, anzahl in (bericht.get("geaendert") or {}).items():
        z.append(f"  {datei}: {anzahl}{_gescheitert(datei, fehler_je_datei)}")
    if not bericht.get("geaendert"):
        z.append("  (keine - in dieser Sitzung wurde keine Datei geaendert)")

    z.append("\nNUR GELESENE DATEIEN (nicht geaendert; Datei: Anzahl Lesezugriffe):")
    nur_gelesen = {d: n for d, n in (bericht.get("gelesen") or {}).items()
                   if d not in (bericht.get("geaendert") or {})}
    for datei, anzahl in nur_gelesen.items():
        z.append(f"  {datei}: {anzahl}{_gescheitert(datei, fehler_je_datei)}")
    if not nur_gelesen:
        z.append("  (keine)")

    z.append("\nAUSGEFUEHRTE BEFEHLE:")
    for b in (bericht.get("befehle") or [])[:50]:
        z.append(f"  $ {b}")
    if not bericht.get("befehle"):
        z.append("  (keine)")

    z.append("\nFEHLSCHLAEGE (das Wichtigste - hier lagen die Fallen), "
             "in zeitlicher Reihenfolge:")
    for f in bericht.get("fehlschlaege") or []:
        ziel = f" [{f['ziel']}]" if f.get("ziel") else ""
        z.append(f"  #{f.get('nummer')} nach {f.get('nach_sekunden')} s "
                 f"{f.get('werkzeug')}{ziel}: {f.get('fehler')}")
    if not bericht.get("fehlschlaege"):
        z.append("  (keine)")

    z.append("\nWAS DAS PROTOKOLL NICHT ENTHAELT - darueber keine Aussage treffen:")
    z.append("  - die Reihenfolge der Zugriffe INNERHALB einer Datei")
    z.append("  - ob ein Fehlschlag spaeter behoben wurde")
    z.append("  - den Inhalt der Dateien und was inhaltlich geaendert wurde")
    z.append("  - das Ziel der Sitzung, falls es sich nicht aus den Dateien ergibt")
    return "\n".join(z)


def _gescheitert(datei: str, fehler_je_datei: dict) -> str:
    anzahl = fehler_je_datei.get(datei, 0)
    if not anzahl:
        return ""
    return f"  (davon {anzahl} GESCHEITERT)"


ZUSATZPFADE = ("~/.local/bin", "/opt/homebrew/bin", "/usr/local/bin",
               "~/.bun/bin", "~/.npm-global/bin")


def _pfad_ergaenzen(pfad: str) -> str:
    """Die ueblichen Orte anhaengen, falls der PATH beschnitten ist."""
    teile = [p for p in pfad.split(os.pathsep) if p]
    for zusatz in ZUSATZPFADE:
        aufgeloest = str(Path(zusatz).expanduser())
        if aufgeloest not in teile and Path(aufgeloest).is_dir():
            teile.append(aufgeloest)
    return os.pathsep.join(teile)


def _programm_finden(name: str) -> str:
    """Einen Programmnamen zu einem Pfad machen.

    Ein launchd-Dienst hat einen beschnittenen PATH, und `/bin/sh -lc` liest
    unter zsh weder ~/.zprofile noch ~/.zshrc. Dann liegt `claude` in
    ~/.local/bin und wird nicht gefunden - aufgefallen am 09.11.2026 im
    Dienst-Log: "Testleser fehlgeschlagen: claude nicht im PATH".
    """
    if os.sep in name:
        return name
    import shutil
    gefunden = shutil.which(name)
    if gefunden:
        return gefunden
    for ordner in ZUSATZPFADE:
        kandidat = Path(ordner).expanduser() / name
        if kandidat.is_file() and os.access(kandidat, os.X_OK):
            return str(kandidat)
    return name


def _claude_rufen(anfrage: str, modell: str) -> tuple[bool, str]:
    """Ein Sprachmodell mit einer Textaufgabe rufen.

    Der Befehl steht in der Konfiguration (`modell_befehl`), damit das Werkzeug
    nicht an Claude Code haengt: wer `codex exec`, `llm`, `ollama` oder ein
    eigenes Skript hat, traegt es dort ein. Erwartet wird: Anfrage auf stdin,
    Antwort auf stdout.
    """
    umgebung = dict(os.environ)
    umgebung["LANDKARTE_SCHREIBER"] = "1"
    vorlage = konfig.laden().get("modell_befehl") or []
    if not vorlage:
        return False, ("kein modell_befehl eingetragen - "
                       "siehe landkarte einrichten --hilfe-modell")
    befehl = [teil.replace("{modell}", modell) for teil in vorlage]
    befehl[0] = _programm_finden(befehl[0])
    umgebung["PATH"] = _pfad_ergaenzen(umgebung.get("PATH", ""))
    try:
        ergebnis = subprocess.run(
            befehl, input=anfrage, capture_output=True, text=True,
            timeout=300, env=umgebung, cwd=str(Path.home()),
        )
    except FileNotFoundError:
        return False, f"{befehl[0]} nicht im PATH gefunden"
    except subprocess.TimeoutExpired:
        return False, "Zeitueberschreitung nach 300 s"
    if ergebnis.returncode != 0:
        return False, (ergebnis.stderr or ergebnis.stdout or "unbekannt")[:500]
    return True, ergebnis.stdout.strip()


def _titel_trennen(rohtext: str) -> tuple[str, str]:
    titel = ""
    zeilen = rohtext.splitlines()
    rest: list[str] = []
    for i, zeile in enumerate(zeilen):
        treffer = re.match(r"^\s*(?:TITEL|Titel)\s*:\s*(.+)$", zeile)
        if treffer and not titel:
            titel = treffer.group(1).strip().strip("*# ")
            rest = zeilen[i + 1:]
            break
    if not titel:
        return "", rohtext.strip()
    return titel[:80], "\n".join(rest).strip()


def _dateiname(datum: str, titel: str, sitzung: str) -> str:
    kern = re.sub(r"[^\w\s-]", "", titel.lower())
    kern = re.sub(r"\s+", "-", kern.strip())[:50].strip("-")
    if not kern:
        kern = sitzung[:8]
    return f"{datum}-{kern}.md"


def buchordner(projekt_wurzel: Path) -> Path:
    return projekt_wurzel / ".landkarte" / "buch"


def kapitel_schreiben(sitzung: str, modell: str | None = None,
                      trocken: bool = False) -> dict:
    """Ein Kapitel fuer eine Sitzung erzeugen und ablegen."""
    bericht = chronik.sitzung_verdichten(sitzung)
    if not bericht:
        return {"ok": False, "grund": "keine Chronik zu dieser Sitzung"}
    projekt = bericht.get("projekt") or ""
    wurzel = Path(projekt)
    if not projekt or not wurzel.is_dir():
        return {"ok": False, "grund": f"Projektordner nicht auffindbar: {projekt}"}

    konf = konfig.laden()
    modell = modell or konf.get("schreiber_modell", STANDARD_MODELL)
    anfrage = ANWEISUNG + "\n\n=== MASCHINENPROTOKOLL ===\n" + bericht_text(bericht)

    if trocken:
        return {"ok": True, "trocken": True, "anfrage": anfrage,
                "zeichen": len(anfrage)}

    erfolg, antwort = _claude_rufen(anfrage, modell)
    if not erfolg:
        return {"ok": False, "grund": "Schreiber fehlgeschlagen: " + antwort}

    titel, koerper = _titel_trennen(antwort)
    if not titel:
        titel = f"Sitzung {datetime.fromtimestamp(bericht['beginn']).strftime('%d.%m. %H:%M')}"
    datum = datetime.fromtimestamp(bericht.get("beginn") or time.time()).strftime("%Y-%m-%d")

    ordner = buchordner(wurzel)
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / _dateiname(datum, titel, sitzung)

    kopf = {
        "sitzung": sitzung,
        "datum": datum,
        "projekt": wurzel.name,
        "titel": titel,
        "aufrufe": bericht.get("aufrufe"),
        "dauer": _dauer((bericht.get("ende") or 0) - (bericht.get("beginn") or 0)),
        "fehlschlaege": len(bericht.get("fehlschlaege") or []),
        "dateien": list((bericht.get("dateien") or {}).keys())[:15],
        "modell": modell,
    }
    inhalt = ["---"]
    for schluessel, wert in kopf.items():
        if isinstance(wert, list):
            inhalt.append(f"{schluessel}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in wert)}]")
        else:
            inhalt.append(f"{schluessel}: {json.dumps(wert, ensure_ascii=False) if isinstance(wert, str) else wert}")
    inhalt.append("---")
    inhalt.append("")
    inhalt.append(f"# {titel}")
    inhalt.append("")
    inhalt.append(koerper)
    inhalt.append("")
    ziel.write_text("\n".join(inhalt), "utf-8")

    chronik.abgeschlossen_merken(sitzung, {
        "kapitel": str(ziel), "titel": titel, "projekt": str(wurzel),
        "geschrieben": int(time.time()), "modell": modell,
    })
    return {"ok": True, "kapitel": str(ziel), "titel": titel, "projekt": str(wurzel)}


# ------------------------------------------------------- Kapitel wieder lesen

KOPF_MUSTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def kapitel_lesen(pfad: Path) -> dict:
    """Ein Kapitel in Kopfdaten und Abschnitte zerlegen."""
    try:
        text = pfad.read_text("utf-8")
    except OSError:
        return {}
    kopf: dict = {}
    treffer = KOPF_MUSTER.match(text)
    koerper = text
    if treffer:
        for zeile in treffer.group(1).splitlines():
            if ":" not in zeile:
                continue
            schluessel, _, wert = zeile.partition(":")
            wert = wert.strip()
            if wert.startswith("[") and wert.endswith("]"):
                try:
                    kopf[schluessel.strip()] = json.loads(wert)
                except json.JSONDecodeError:
                    kopf[schluessel.strip()] = []
            else:
                kopf[schluessel.strip()] = wert.strip('"')
        koerper = text[treffer.end():]

    abschnitte: dict[str, list[str]] = {}
    aktuell = ""
    for zeile in koerper.splitlines():
        if zeile.startswith("## "):
            aktuell = zeile[3:].strip()
            abschnitte[aktuell] = []
        elif aktuell:
            abschnitte[aktuell].append(zeile)
    for k in abschnitte:
        abschnitte[k] = [z for z in abschnitte[k]]
    return {"pfad": str(pfad), "kopf": kopf, "abschnitte": abschnitte,
            "datei": pfad.name}


def _punkte(zeilen: list[str]) -> list[str]:
    aus = []
    for z in zeilen:
        s = z.strip()
        if s.startswith(("- ", "* ")):
            rein = s[2:].strip()
            if rein and rein.lower() not in ("keine", "nichts erkennbar", "keine."):
                aus.append(rein)
    return aus


def kapitel_sammeln(projekt_wurzel: Path) -> list[dict]:
    ordner = buchordner(projekt_wurzel)
    if not ordner.exists():
        return []
    aus = []
    for p in sorted(ordner.glob("*.md"), reverse=True):
        k = kapitel_lesen(p)
        if k:
            k["fallen"] = _punkte(k["abschnitte"].get("Fallen", []))
            k["regeln"] = _punkte(k["abschnitte"].get("Regeln daraus", []))
            k["offen"] = _punkte(k["abschnitte"].get("Offen", []))
            aus.append(k)
    return aus
