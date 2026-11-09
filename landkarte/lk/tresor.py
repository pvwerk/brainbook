"""Zweck: verschluesselter Tresor fuer Zugangsdaten im Brainbook.

Warum ueberhaupt: Passwoerter landen im Gespraech. Von dort wandern sie in das
Sitzungsprotokoll, in die Chronik und in jede Auswertung, die darauf aufsetzt.
Schwaerzen allein genuegt nicht - danach ist das Geheimnis zwar unsichtbar,
aber auch weg, und beim naechsten Mal wird es erneut getippt. Der Tresor nimmt
es auf, bevor es geschwaerzt wird: einmal gesagt, dauerhaft verfuegbar, nie
wieder im Klartext in einer Datei.

Aufbau:

    ~/.landkarte/tresor.enc        die verschluesselte Ablage
    Hauptschluessel                im Schluesselbund (macOS) oder als
                                   Datei mit Rechten 600

Verschluesselt wird mit `openssl enc -aes-256-cbc -pbkdf2 -iter 600000`.
Die Python-Standardbibliothek bringt kein AES mit, und eine
Fremdbibliothek waere eine neue Abhaengigkeit fuer ein Werkzeug, das
bewusst ohne auskommt. `openssl` liegt auf macOS und jedem Linux bereit und
verschluesselt bereits die naechtlichen Sicherungen des Gutachten-Tools -
dasselbe Verfahren, dieselbe Pruefbarkeit.

Zusaetzlich wird nach dem Verschluesseln ein HMAC ueber den Geheimtext
gebildet (encrypt-then-MAC). Ohne ihn liesse sich der Geheimtext unbemerkt
veraendern; CBC allein erkennt das nicht.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from . import konfig

TRESOR = konfig.LK_HEIM / "tresor.enc"
SCHLUESSEL_DATEI = konfig.LK_HEIM / "tresor.schluessel"
SCHLUESSELBUND_DIENST = "landkarte-tresor"
ITERATIONEN = 600_000
FASSUNG = 1


class TresorFehler(RuntimeError):
    """Etwas stimmt mit dem Tresor nicht - nie mit Geheimnis im Text."""


# --------------------------------------------------------------- Hauptschluessel


def _openssl() -> str:
    weg = shutil.which("openssl")
    if not weg:
        raise TresorFehler(
            "openssl wurde nicht gefunden. Ohne openssl kann der Tresor nicht "
            "verschluesseln. Auf macOS ist es vorhanden, unter Debian/Ubuntu: "
            "apt install openssl"
        )
    return weg


# Nur fuer den Pruefbetrieb: haelt den echten Schluesselbund aus dem Spiel.
# Ohne diesen Schalter wuerde eine Pruefung den Schluessel des Nutzers lesen
# oder ueberschreiben - eine Pruefung darf nichts anfassen, was ihr nicht
# gehoert.
_SCHLUESSEL_NUR_DATEI = False


def _schluesselbund_lesen() -> str | None:
    if _SCHLUESSEL_NUR_DATEI or platform.system() != "Darwin":
        return None
    try:
        e = subprocess.run(
            ["security", "find-generic-password", "-s", SCHLUESSELBUND_DIENST, "-w"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return None
    wert = e.stdout.strip()
    return wert if e.returncode == 0 and wert else None


def _schluesselbund_schreiben(wert: str) -> bool:
    if _SCHLUESSEL_NUR_DATEI or platform.system() != "Darwin":
        return False
    try:
        e = subprocess.run(
            ["security", "add-generic-password", "-s", SCHLUESSELBUND_DIENST,
             "-a", os.environ.get("USER", "landkarte"), "-w", wert, "-U"],
            capture_output=True, text=True, timeout=15,
        )
        return e.returncode == 0
    except Exception:
        return False


def hauptschluessel(anlegen: bool = True) -> str:
    """Den Hauptschluessel holen, bei Bedarf einen neuen erzeugen.

    Reihenfolge: Schluesselbund zuerst, Datei als Rueckfallebene. Auf dem Mac
    liegt der Schluessel damit dort, wo das Betriebssystem ihn schuetzt, und
    nicht neben dem Tresor - wer nur die Datei kopiert, hat nichts.
    """
    wert = _schluesselbund_lesen()
    if wert:
        return wert
    if SCHLUESSEL_DATEI.exists():
        wert = SCHLUESSEL_DATEI.read_text("utf-8").strip()
        if wert:
            return wert
    if not anlegen:
        raise TresorFehler("Es gibt noch keinen Hauptschluessel.")
    neu = secrets.token_hex(32)
    if not _schluesselbund_schreiben(neu):
        konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
        SCHLUESSEL_DATEI.write_text(neu + "\n", encoding="utf-8")
        os.chmod(SCHLUESSEL_DATEI, 0o600)
    return neu


def schluessel_ort() -> str:
    if _schluesselbund_lesen():
        return "Schluesselbund (macOS)"
    if SCHLUESSEL_DATEI.exists():
        return f"Datei {SCHLUESSEL_DATEI} (Rechte 600)"
    return "noch keiner"


def _mac_schluessel(haupt: str) -> bytes:
    """Eigener Schluessel fuer den HMAC - nie derselbe wie zum Verschluesseln."""
    return hashlib.sha256(("mac:" + haupt).encode()).digest()


# --------------------------------------------------------------- Ver-/Entschluesseln


def _verschluesseln(klartext: bytes, haupt: str) -> dict:
    e = subprocess.run(
        [_openssl(), "enc", "-aes-256-cbc", "-pbkdf2", "-iter", str(ITERATIONEN),
         "-salt", "-pass", "stdin"],
        input=haupt.encode() + b"\n" + klartext,
        capture_output=True, timeout=120,
    )
    # openssl liest die Passphrase als erste Zeile von stdin, danach die Daten.
    if e.returncode != 0:
        raise TresorFehler("Verschluesseln fehlgeschlagen.")
    geheim = e.stdout
    marke = hmac.new(_mac_schluessel(haupt), geheim, hashlib.sha256).hexdigest()
    return {
        "fassung": FASSUNG,
        "verfahren": f"aes-256-cbc/pbkdf2-{ITERATIONEN}",
        "hmac": marke,
        "inhalt": base64.b64encode(geheim).decode(),
    }


def _entschluesseln(huelle: dict, haupt: str) -> bytes:
    geheim = base64.b64decode(huelle["inhalt"])
    erwartet = hmac.new(_mac_schluessel(haupt), geheim, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(erwartet, huelle.get("hmac", "")):
        raise TresorFehler(
            "Der Tresor wurde veraendert oder der Hauptschluessel passt nicht. "
            "Es wird nichts entschluesselt."
        )
    e = subprocess.run(
        [_openssl(), "enc", "-d", "-aes-256-cbc", "-pbkdf2",
         "-iter", str(ITERATIONEN), "-pass", "stdin"],
        input=haupt.encode() + b"\n" + geheim,
        capture_output=True, timeout=120,
    )
    if e.returncode != 0:
        raise TresorFehler("Entschluesseln fehlgeschlagen.")
    return e.stdout


# --------------------------------------------------------------- Ablage


def _leer() -> dict:
    return {"fassung": FASSUNG, "eintraege": {}}


# Entschluesseln kostet 600.000 PBKDF2-Runden, also rund eine halbe Sekunde.
# Beim Rundgang durch Dutzende Protokolldateien waere das die ganze Laufzeit.
# Deshalb wird der entschluesselte Stand im Prozess gehalten, zusammen mit der
# Veraenderungszeit der Datei: schreibt ein anderer Prozess dazwischen, wird
# neu gelesen.
_SPEICHER: tuple[float, dict] | None = None


def _stempel() -> float:
    try:
        return TRESOR.stat().st_mtime_ns / 1e9
    except OSError:
        return 0.0


def speicher_leeren() -> None:
    global _SPEICHER
    _SPEICHER = None


def laden() -> dict:
    global _SPEICHER
    if not TRESOR.exists():
        return _leer()
    jetzt = _stempel()
    if _SPEICHER is not None and _SPEICHER[0] == jetzt:
        return _SPEICHER[1]
    try:
        huelle = json.loads(TRESOR.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as fehler:
        raise TresorFehler(f"Tresor nicht lesbar: {type(fehler).__name__}") from None
    roh = _entschluesseln(huelle, hauptschluessel(anlegen=False))
    try:
        daten = json.loads(roh.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TresorFehler("Tresorinhalt beschaedigt.") from None
    _SPEICHER = (jetzt, daten)
    return daten


def sichern(daten: dict) -> None:
    global _SPEICHER
    haupt = hauptschluessel()
    huelle = _verschluesseln(json.dumps(daten, ensure_ascii=False).encode(), haupt)
    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    vorlaeufig = TRESOR.with_suffix(".enc.neu")
    vorlaeufig.write_text(json.dumps(huelle), encoding="utf-8")
    os.chmod(vorlaeufig, 0o600)
    vorlaeufig.replace(TRESOR)
    _SPEICHER = (_stempel(), daten)


# --------------------------------------------------------------- Oeffentlich


def _name_frei(daten: dict, wunsch: str) -> str:
    name = wunsch
    n = 2
    while name in daten["eintraege"]:
        name = f"{wunsch}-{n}"
        n += 1
    return name


def einlegen(name: str, geheimnis: str, herkunft: str = "",
             notiz: str = "") -> tuple[str, bool]:
    """Ein Geheimnis ablegen. Gibt (Name, war_neu) zurueck.

    Ist dasselbe Geheimnis schon drin, wird kein zweiter Eintrag angelegt -
    sonst waechst der Tresor bei jedem Erwaehnen desselben Passworts.
    """
    if not geheimnis:
        raise TresorFehler("Leeres Geheimnis wird nicht abgelegt.")
    daten = laden()
    for vorhanden, e in daten["eintraege"].items():
        if e.get("geheimnis") == geheimnis:
            e["zuletzt_gesehen"] = int(time.time())
            if herkunft and herkunft not in e.get("herkunft", []):
                e.setdefault("herkunft", []).append(herkunft)
            sichern(daten)
            return vorhanden, False
    name = _name_frei(daten, name or "ohne-namen")
    daten["eintraege"][name] = {
        "geheimnis": geheimnis,
        "notiz": notiz,
        "herkunft": [herkunft] if herkunft else [],
        "angelegt": int(time.time()),
        "zuletzt_gesehen": int(time.time()),
    }
    sichern(daten)
    return name, True


def holen(name: str) -> str | None:
    e = laden()["eintraege"].get(name)
    return e.get("geheimnis") if e else None


def entfernen(name: str) -> bool:
    daten = laden()
    if name not in daten["eintraege"]:
        return False
    del daten["eintraege"][name]
    sichern(daten)
    return True


def umbenennen(alt: str, neu: str) -> bool:
    daten = laden()
    if alt not in daten["eintraege"] or neu in daten["eintraege"]:
        return False
    daten["eintraege"][neu] = daten["eintraege"].pop(alt)
    sichern(daten)
    return True


def liste() -> list[dict]:
    """Alle Eintraege OHNE die Geheimnisse - zum Anzeigen gedacht."""
    daten = laden()
    aus = []
    for name, e in sorted(daten["eintraege"].items()):
        aus.append({
            "name": name,
            "notiz": e.get("notiz", ""),
            "herkunft": e.get("herkunft", []),
            "angelegt": e.get("angelegt"),
            "zuletzt_gesehen": e.get("zuletzt_gesehen"),
            "laenge": len(e.get("geheimnis", "")),
        })
    return aus


def alle_geheimnisse() -> list[str]:
    """Nur fuer die Schwaerzung: die Werte, nach denen gesucht wird."""
    try:
        daten = laden()
    except TresorFehler:
        return []
    return [e["geheimnis"] for e in daten["eintraege"].values() if e.get("geheimnis")]


def steht_bereit() -> bool:
    return TRESOR.exists()
