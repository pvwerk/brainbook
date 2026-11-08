"""Zweck: Das Werkzeug protokolliert sich selbst - unabhaengig von jeder KI.

Der Chronist haengt an Claude-Code-Hooks. Grok und ChatGPT im Browser haben
keine. Damit das Vorhaben trotzdem von mehreren Leuten mit verschiedenen KIs
verbessert werden kann, protokolliert das Werkzeug seine eigene Benutzung:
welcher Befehl, mit welchem Ergebnis, wie lange, ob er fehlschlug.

Es ist **kontextlos schon beim Schreiben**, nicht erst beim Export. Damit ist
auch das Rohprotokoll harmlos und `--roh` zeigt nichts anderes als die
Exportdatei.

Festgehalten wird: WAS fuer eine Aufgabe (der Befehl), WAS fuer eine Struktur
(Groessenklassen, Sprachen, mit oder ohne Git), WELCHE Fehlerklasse an WELCHER
Stelle im eigenen Code, und wie OFT. Nicht festgehalten wird, WORAN: keine
Projektnamen, keine Dateipfade, keine Dateiinhalte, keine Suchbegriffe, keine
Notizen, keine Fehlermeldungen im Wortlaut.

Fehlermeldungen werden auf ihr Muster zurueckgefuehrt: jede Zeichenkette, jeder
Pfad und jede Zahl wird zu einem Platzhalter. Aus
"KeyError: 'vorlage/layout.html'" wird "KeyError: <text>".

Nichts verlaesst den Rechner von selbst. Der Export ist ein eigener Befehl,
und `brainbook stats --roh` zeigt vorher jede einzelne Zeile.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import secrets
import statistics
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from . import konfig, schwaerzen

ORDNER = konfig.LK_HEIM / "statistik"
FASSUNG = 1

# Begriffe, die nie protokolliert werden - zur Sicherheit doppelt gefiltert
NIE = ("begriff", "text", "falsch", "richtig", "stichwort", "was", "notiz",
       "auch", "kategorie", "verweis", "grund", "datei", "pfad", "projekt",
       "ist", "sitzung", "modell")


def _konf() -> dict:
    return konfig.laden()


def aktiv() -> bool:
    return bool(_konf().get("statistik", True))


def teilnehmer() -> str:
    """Freier Name oder, wenn keiner gesetzt ist, eine zufaellige Kennung."""
    konf = _konf()
    if konf.get("teilnehmer"):
        return str(konf["teilnehmer"])
    kennung = konf.get("teilnehmer_kennung")
    if not kennung:
        kennung = "tn-" + secrets.token_hex(3)
        konf["teilnehmer_kennung"] = kennung
        konfig.schreiben(konf)
    return kennung


def _salz() -> str:
    konf = _konf()
    salz = konf.get("statistik_salz")
    if not salz:
        salz = secrets.token_hex(8)
        konf["statistik_salz"] = salz
        konfig.schreiben(konf)
    return salz


def kurzhash(wert: str) -> str:
    """Gesalzener Kurz-Hash. Erkennt Wiederholung, verraet den Namen nicht."""
    if not wert:
        return ""
    roh = (_salz() + "|" + str(wert)).encode("utf-8")
    return "h" + hashlib.sha256(roh).hexdigest()[:8]


def _klasse(wert: int, grenzen: tuple[int, ...]) -> str:
    """Zahl auf eine Groessenklasse zurueckfuehren."""
    vorher = 0
    for grenze in grenzen:
        if wert < grenze:
            return f"{vorher}-{grenze}" if vorher else f"<{grenze}"
        vorher = grenze
    return f">{grenzen[-1]}"


def struktur(wurzel: str) -> dict:
    """Die FORM eines Projekts, nicht seine Identitaet.

    Gelesen wird der vorhandene Zwischenspeicher - kein zusaetzlicher Scan.
    """
    if not wurzel:
        return {}
    cache = konfig.PROJEKT_CACHE / f"{konfig.slug(Path(wurzel))}.json"
    if not cache.exists():
        return {}
    try:
        knapp = json.loads(cache.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    endungen: dict[str, int] = {}
    for d in knapp.get("dateien", []):
        endung = Path(d.get("pfad", "")).suffix.lower().lstrip(".")
        if endung:
            endungen[endung] = endungen.get(endung, 0) + 1
    haupt = [e for e, _ in sorted(endungen.items(), key=lambda kv: -kv[1])[:4]]
    return {
        "dateien": _klasse(int(knapp.get("anzahl_dateien") or 0),
                           (10, 50, 200, 1000, 5000)),
        "zeilen": _klasse(int(knapp.get("anzahl_zeilen") or 0),
                          (500, 5000, 50000, 500000)),
        "sprachen": haupt,
        "git": bool((knapp.get("git") or {}).get("commit")),
        "kapitel": _klasse(int(knapp.get("kapitel") or 0), (1, 5, 20, 100)),
    }


_ZEICHENKETTE = re.compile(r"""(['"])(?:\\.|(?!\1).)*\1""")
_PFADARTIG = re.compile(r"(?:[A-Za-z]:[\\/]|~/|\.{1,2}/|/)[\w.\-/\\ ]{2,}")
_ZAHL = re.compile(r"\b\d+\b")
_HEX = re.compile(r"\b[0-9a-fA-F]{6,}\b")


def meldung_entschaerfen(text: str) -> str:
    """Eine Fehlermeldung auf ihr Muster zurueckfuehren.

    Aus "KeyError: 'vorlage/layout.html'" wird "KeyError: <text>". Damit bleibt
    die Fehlerart erkennbar, das Woran verschwindet.
    """
    if not text:
        return ""
    aus = schwaerzen.schwaerzen(text) or ""
    aus = _ZEICHENKETTE.sub("<text>", aus)
    aus = _PFADARTIG.sub("<pfad>", aus)
    aus = _HEX.sub("<id>", aus)
    aus = _ZAHL.sub("<n>", aus)
    return re.sub(r"\s+", " ", aus).strip()[:220]


def _pfade_entfernen(text: str) -> str:
    """Absolute Pfade auf den Dateinamen kuerzen, Heimordner ersetzen."""
    if not text:
        return text
    aus = text.replace(str(konfig.HEIM), "~")
    # alles, was nach einem absoluten Pfad aussieht, auf den Namen kuerzen
    aus = re.sub(r"(?:~|/)[\w.\-/ ]{3,}/([\w.\-]+)", r".../\1", aus)
    return schwaerzen.schwaerzen(aus) or ""


def umgebung() -> dict:
    from . import __version__
    return {
        "fassung": FASSUNG,
        "werkzeug": __version__,
        "os": sys.platform,
        "os_fassung": platform.release(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "ki": _konf().get("ki", "unbekannt"),
    }


def _datei() -> Path:
    ORDNER.mkdir(parents=True, exist_ok=True)
    return ORDNER / (datetime.now().strftime("%Y-%m") + ".jsonl")


def festhalten(befehl: str, flaggen: list[str], code: int, dauer_ms: int,
               ergebnis: dict | None = None, ursache: dict | None = None,
               projekt: str = "") -> None:
    """Einen Aufruf anhaengen. Still - ein Protokollfehler darf nie stoeren."""
    if not aktiv():
        return
    try:
        satz = {
            "t": int(time.time()),
            "tn": teilnehmer(),
            "b": befehl,
            "f": sorted(set(flaggen))[:12],
            "c": code,
            "ms": dauer_ms,
            **umgebung(),
        }
        if projekt:
            # opake Gruppenkennung: erkennt Wiederholung, nennt keinen Namen
            satz["g"] = kurzhash(projekt)
            form = struktur(projekt)
            if form:
                satz["s"] = form
        if ergebnis:
            satz["e"] = {k: v for k, v in ergebnis.items()
                         if isinstance(v, (int, float, bool))}
        if ursache:
            satz["u"] = ursache
        with _datei().open("a", encoding="utf-8") as f:
            f.write(json.dumps(satz, ensure_ascii=False) + "\n")
    except Exception:
        pass


def absturz_festhalten(befehl: str, flaggen: list[str], dauer_ms: int,
                       projekt: str = "") -> None:
    """Ursache strukturiert festhalten: Klasse, eigene Codestelle, Muster.

    Mitgenommen werden nur Rahmen aus dem eigenen Paket - die Stellen also,
    die man reparieren muss. Fremde Rahmen und die Fehlermeldung im Wortlaut
    bleiben draussen.
    """
    art, wert, _ = sys.exc_info()
    klasse = art.__name__ if art else "Fehler"
    eigene: list[str] = []
    for rahmen in traceback.extract_tb(sys.exc_info()[2]):
        datei = Path(rahmen.filename)
        if datei.parent.name == "lk" or datei.name in ("landkarte", "brainbook"):
            eigene.append(f"{datei.name}:{rahmen.lineno} in {rahmen.name}")
    ursache = {
        "klasse": klasse,
        "stelle": eigene[-1] if eigene else "unbekannt",
        "weg": eigene[-4:],
        "muster": meldung_entschaerfen(str(wert) if wert else ""),
    }
    festhalten(befehl, flaggen, 70, dauer_ms, ursache=ursache, projekt=projekt)


# --------------------------------------------------------------- Auswertung


def _lesen(monate: int = 12) -> list[dict]:
    if not ORDNER.exists():
        return []
    dateien = sorted(ORDNER.glob("*.jsonl"))[-monate:]
    aus: list[dict] = []
    for p in dateien:
        try:
            for zeile in p.read_text("utf-8", errors="replace").splitlines():
                if not zeile.strip():
                    continue
                try:
                    aus.append(json.loads(zeile))
                except json.JSONDecodeError:
                    continue
        except OSError:
            continue
    return aus


def _reibung(saetze: list[dict]) -> list[dict]:
    """Wo hakt es: derselbe Befehl zweimal hintereinander, oder ein Fehlschlag,
    auf den sofort ein anderer Versuch folgt. Das ist das Mass fuer Reibung."""
    saetze = sorted(saetze, key=lambda s: s.get("t", 0))
    doppelt: dict[str, int] = {}
    nachgefasst: dict[str, int] = {}
    for a, b in zip(saetze, saetze[1:]):
        if b.get("t", 0) - a.get("t", 0) > 120:
            continue
        if a.get("b") == b.get("b") and a.get("f") == b.get("f"):
            doppelt[a.get("b", "?")] = doppelt.get(a.get("b", "?"), 0) + 1
        elif a.get("c") not in (0, None) or (a.get("e") or {}).get("treffer") == 0:
            schluessel = f"{a.get('b')} → {b.get('b')}"
            nachgefasst[schluessel] = nachgefasst.get(schluessel, 0) + 1
    return [
        {"art": "gleicher Befehl direkt wiederholt", "werte": dict(
            sorted(doppelt.items(), key=lambda kv: -kv[1])[:8])},
        {"art": "nach Fehlschlag oder Nulltreffer anders versucht", "werte": dict(
            sorted(nachgefasst.items(), key=lambda kv: -kv[1])[:8])},
    ]


def bericht(monate: int = 12) -> dict:
    saetze = _lesen(monate)
    if not saetze:
        return {"aufrufe": 0}

    je_befehl: dict[str, dict] = {}
    for s in saetze:
        b = s.get("b", "?")
        e = je_befehl.setdefault(b, {"aufrufe": 0, "fehlschlaege": 0,
                                     "dauern": [], "nulltreffer": 0,
                                     "abstuerze": 0})
        e["aufrufe"] += 1
        if s.get("c") not in (0, None):
            e["fehlschlaege"] += 1
        if s.get("c") == 70:
            e["abstuerze"] += 1
        if isinstance(s.get("ms"), int):
            e["dauern"].append(s["ms"])
        if (s.get("e") or {}).get("treffer") == 0:
            e["nulltreffer"] += 1

    befehle = {}
    for b, e in sorted(je_befehl.items(), key=lambda kv: -kv[1]["aufrufe"]):
        dauern = sorted(e["dauern"])
        befehle[b] = {
            "aufrufe": e["aufrufe"],
            "fehlschlaege": e["fehlschlaege"],
            "abstuerze": e["abstuerze"],
            "nulltreffer": e["nulltreffer"],
            "ms_mittel": int(statistics.median(dauern)) if dauern else None,
            "ms_p95": dauern[int(len(dauern) * 0.95)] if len(dauern) > 4 else (
                dauern[-1] if dauern else None),
        }

    # Ursachen zusammenfassen: Klasse + eigene Codestelle + Muster
    ursachen: dict[tuple, dict] = {}
    for s in saetze:
        u = s.get("u")
        if not u:
            continue
        schluessel = (u.get("klasse"), u.get("stelle"), u.get("muster", ""))
        e = ursachen.setdefault(schluessel, {
            "klasse": u.get("klasse"), "stelle": u.get("stelle"),
            "muster": u.get("muster", ""), "weg": u.get("weg", []),
            "anzahl": 0, "befehle": {}, "strukturen": []})
        e["anzahl"] += 1
        e["befehle"][s.get("b", "?")] = e["befehle"].get(s.get("b", "?"), 0) + 1
        if s.get("s") and s["s"] not in e["strukturen"]:
            e["strukturen"].append(s["s"])

    # Welche ARTEN von Strukturen kommen vor - ohne jede Identitaet.
    formen: dict[str, dict[str, int]] = {"dateien": {}, "zeilen": {},
                                         "sprachen": {}, "git": {}}
    for s in saetze:
        form = s.get("s")
        if not form:
            continue
        for feld in ("dateien", "zeilen"):
            wert = form.get(feld)
            if wert:
                formen[feld][wert] = formen[feld].get(wert, 0) + 1
        for sprache in form.get("sprachen", []):
            formen["sprachen"][sprache] = formen["sprachen"].get(sprache, 0) + 1
        schluessel = "mit git" if form.get("git") else "ohne git"
        formen["git"][schluessel] = formen["git"].get(schluessel, 0) + 1
    formen = {k: dict(sorted(v.items(), key=lambda kv: -kv[1])[:8])
              for k, v in formen.items() if v}

    projekte = len({s["g"] for s in saetze if s.get("g")})
    zeiten = [s.get("t", 0) for s in saetze if s.get("t")]
    letzter = saetze[-1]
    return {
        "fassung": FASSUNG,
        "teilnehmer": letzter.get("tn"),
        "erzeugt": datetime.now().isoformat(timespec="seconds"),
        "zeitraum": {
            "von": datetime.fromtimestamp(min(zeiten)).date().isoformat()
            if zeiten else None,
            "bis": datetime.fromtimestamp(max(zeiten)).date().isoformat()
            if zeiten else None,
            "tage_aktiv": len({datetime.fromtimestamp(t).date() for t in zeiten}),
        },
        "umgebung": {k: letzter.get(k) for k in
                     ("werkzeug", "os", "os_fassung", "python", "ki")},
        "aufrufe": len(saetze),
        "beruehrte_projekte": projekte,
        "befehle": befehle,
        "strukturen": formen,
        "ursachen": sorted(ursachen.values(), key=lambda e: -e["anzahl"]),
        "reibung": _reibung(saetze),
    }


def ausgeben(b: dict) -> str:
    if not b.get("aufrufe"):
        return ("Noch keine Statistik. Sie entsteht beim Benutzen des "
                "Werkzeugs.\nAbschalten mit: landkarte einrichten --statistik-aus")
    z = [f"Statistik — Teilnehmer {b['teilnehmer']}", ""]
    u = b["umgebung"]
    z.append(f"Werkzeug {u.get('werkzeug')} · {u.get('os')} · "
             f"Python {u.get('python')} · KI: {u.get('ki')}")
    zr = b["zeitraum"]
    z.append(f"{b['aufrufe']} Aufrufe vom {zr['von']} bis {zr['bis']} "
             f"an {zr['tage_aktiv']} Tagen · "
             f"{b['beruehrte_projekte']} verschiedene Projekte")
    z.append("")
    z.append(f"{'Befehl':<16}{'Aufrufe':>8}{'Fehler':>8}{'0 Treffer':>11}"
             f"{'Mittel':>9}{'p95':>8}")
    z.append("-" * 60)
    for name, e in b["befehle"].items():
        z.append(f"{name:<16}{e['aufrufe']:>8}{e['fehlschlaege']:>8}"
                 f"{e['nulltreffer']:>11}"
                 f"{(str(e['ms_mittel']) + ' ms') if e['ms_mittel'] is not None else '—':>9}"
                 f"{(str(e['ms_p95'])) if e['ms_p95'] is not None else '—':>8}")
    if b.get("strukturen"):
        z.append("")
        z.append("STRUKTUREN, auf denen gearbeitet wurde (Klassen, keine Namen)")
        for feld, werte in b["strukturen"].items():
            z.append(f"  {feld}: " + ", ".join(f"{k} ({n}x)"
                                               for k, n in werte.items()))
    if b.get("ursachen"):
        z.append("")
        z.append("URSACHEN (Fehlerklasse · eigene Codestelle · Muster)")
        for a in b["ursachen"][:10]:
            z.append(f"  {a['anzahl']}x  {a['klasse']}  bei {a['stelle']}")
            if a.get("muster"):
                z.append(f"        Muster: {a['muster']}")
            if a.get("befehle"):
                z.append(f"        Aufgabe: " + ", ".join(
                    f"{k} ({n}x)" for k, n in a["befehle"].items()))
            for form in a.get("strukturen", [])[:2]:
                z.append(f"        Struktur: {form.get('dateien')} Dateien, "
                         f"{form.get('zeilen')} Zeilen, "
                         f"{'/'.join(form.get('sprachen', []))}, "
                         f"{'mit' if form.get('git') else 'ohne'} git")
    z.append("")
    z.append("REIBUNG")
    for r in b["reibung"]:
        if r["werte"]:
            z.append(f"  {r['art']}:")
            for k, n in r["werte"].items():
                z.append(f"     {n}x  {k}")
    return "\n".join(z)


def exportieren(ziel: Path, monate: int = 12) -> Path:
    b = bericht(monate)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(b, ensure_ascii=False, indent=1), "utf-8")
    return ziel


def rohzeilen(monate: int = 12) -> list[str]:
    return [json.dumps(s, ensure_ascii=False) for s in _lesen(monate)]
