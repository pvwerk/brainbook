"""Zweck: Zugangsdaten aus Protokolltexten entfernen, bevor sie irgendwo landen.

Der Chronist schreibt Befehlszeilen mit. Darin stehen manchmal Passwoerter -
etwa in einer Postgres-URL. Ungeschwaerzt landen sie in der Chronik, im
Werkstattbericht und in der Anfrage an das Modell.

Deshalb wird an drei Stellen geschwaerzt: beim Schreiben im Hook, beim
Nachtragen und noch einmal beim Lesen. Die dritte Stelle ist die wichtigste,
weil sie auch Dateien abdeckt, die vorher schon geschrieben wurden.
"""

from __future__ import annotations

import re

ERSATZ = "***"

_REGELN: tuple[tuple[re.Pattern, str], ...] = (
    # Anmeldedaten in einer URL: postgresql://benutzer:geheim@host
    (re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://)([^\s:/@]+):([^\s@]+)@"),
     r"\1\2:" + ERSATZ + "@"),
    # Schluessel=Wert und Schluessel: Wert
    # Schluessel=Wert und "schluessel": "wert".
    # Kein \b am Anfang: sonst greift SB_PASSWORD nicht, weil zwischen "_"
    # und "P" keine Wortgrenze liegt. Das schliessende Anfuehrungszeichen vor
    # dem Trennzeichen muss erlaubt sein, sonst greift JSON nicht.
    (re.compile(r"(?i)(?<![:{$/])((?:[a-z0-9]+[_-])*"
                r"(?:pass(?:wor[dt])?|pwd|secret|token|api[_-]?key|"
                r"auth[_-]?token|private[_-]?key|access[_-]?key|"
                r"session[_-]?key|credential)s?)"
                r"([\"']?\s*[:=]\s*)([\"']?)([^\s\"'&;|,}]{6,})"),
     lambda t: f"{t.group(1)}{t.group(2)}{t.group(3)}{ERSATZ}"),
    # Kennwortschalter auf der Befehlszeile
    (re.compile(r"(?i)(--?(?:password|pass|pwd|token|secret)[= ])"
                r"([\"']?)([^\s\"'&;|]{6,})"),
     lambda t: f"{t.group(1)}{t.group(2)}{ERSATZ}"),
    # Das verbreitete "echo geheim | sudo -S"
    (re.compile(r"(?i)(echo\s+)([\"']?)([^\"'|\s]{6,})(\2\s*\|\s*sudo\s+-\S*S)"),
     lambda t: f"{t.group(1)}{t.group(2)}{ERSATZ}{t.group(4)}"),
    # Formularfelder in eingetippten Skripten
    (re.compile(r"(?i)(\[name=(?:password|passwort)\][^=]{0,40}=\s*)"
                r"(\\?[\"'])([^\"'\\]{6,})"),
     lambda t: f"{t.group(1)}{t.group(2)}{ERSATZ}"),
    # Bearer-Kopfzeile
    (re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9_\-.+/=]{12,})"),
     r"\1" + ERSATZ),
    # bekannte Schluesselformen
    (re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9\-_]{14,}"), ERSATZ),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), ERSATZ),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}"), ERSATZ),
    (re.compile(r"\bAKIA[0-9A-Z]{12,}"), ERSATZ),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]*"),
     ERSATZ),
    # PGPASSWORD und Konsorten als Umgebungsvariable
    (re.compile(r"(?i)\b(PGPASSWORD|MYSQL_PWD|ANTHROPIC_API_KEY|OPENAI_API_KEY|"
                r"SUPABASE_[A-Z_]*KEY|AWS_SECRET_ACCESS_KEY)(=)(\S+)"),
     r"\1\2" + ERSATZ),
)


def schwaerzen(text: str | None) -> str | None:
    """Alle erkannten Zugangsdaten durch *** ersetzen - beide Linien."""
    if not text:
        return text
    aus = text
    for muster, ersatz in _REGELN:
        aus = muster.sub(ersatz, aus)
    return woertlich_schwaerzen(aus)


def eintrag_schwaerzen(eintrag: dict) -> dict:
    """Die Textfelder eines Chronik-Eintrags schwaerzen."""
    for feld in ("d", "f"):
        if eintrag.get(feld):
            eintrag[feld] = schwaerzen(eintrag[feld])
    return eintrag


# ---------------------------------------------------------------------------
# Zweite, unabhaengige Linie: woertliche Schwaerzung bekannter Geheimnisse.
#
# Mustererkennung laesst immer etwas durch - ein Passwort, das ohne
# Schluesselwort in einer Befehlszeile steht, ist nicht erkennbar. Deshalb
# werden bekannte Geheimnisse dort gelesen, wo sie ohnehin schon liegen, und
# dann woertlich ersetzt. Es entsteht keine neue Kopie.

import json as _json
import os as _os
from pathlib import Path as _Path

_QUELLEN = (
    _Path.home() / ".claude" / "settings.local.json",
    _Path.home() / ".claude" / "settings.json",
    _Path.home() / ".landkarte" / "geheimnisse.txt",
)
_WOERTLICH: list[str] | None = None
_MIN_LAENGE = 8


def _aus_text_ziehen(text: str) -> set[str]:
    """Werte, die unsere eigenen Muster als Geheimnis erkennen."""
    gefunden: set[str] = set()
    for muster, _ in _REGELN:
        for treffer in muster.finditer(text):
            gruppen = [g for g in treffer.groups() if g] or [treffer.group(0)]
            wert = gruppen[-1]
            if len(wert) < _MIN_LAENGE or wert.startswith(("***", "<", "{")):
                continue
            # Ein Geheimnis mischt Ziffern und Buchstaben oder ist lang.
            # Ohne diese Pruefung landet etwa "crypt('T" aus einem SQL-Befehl
            # in der Liste und schwaerzt dann harmlosen Text.
            if not ((any(z.isdigit() for z in wert)
                     and any(z.isalpha() for z in wert))
                    or len(wert) >= 16):
                continue
            gefunden.add(wert)
            # Derselbe Schluessel kommt mit unterschiedlichem Anhang vor:
            # in einer URL als "geheim-!@host", in einer Befehlszeile nur als
            # "geheim". Deshalb auch den Kern ohne Randzeichen aufnehmen.
            kern = re.sub(r"[^A-Za-z0-9]+$", "", wert)
            kern = re.sub(r"^[^A-Za-z0-9]+", "", kern)
            if len(kern) >= _MIN_LAENGE and kern != wert:
                gefunden.add(kern)
    return gefunden


def bekannte_geheimnisse(neu_laden: bool = False) -> list[str]:
    global _WOERTLICH
    if _WOERTLICH is not None and not neu_laden:
        return _WOERTLICH
    werte: set[str] = set()
    for quelle in _QUELLEN:
        if not quelle.exists():
            continue
        try:
            inhalt = quelle.read_text("utf-8", errors="replace")
        except OSError:
            continue
        if quelle.suffix == ".txt":
            for zeile in inhalt.splitlines():
                zeile = zeile.strip()
                if zeile and not zeile.startswith("#") and len(zeile) >= _MIN_LAENGE:
                    werte.add(zeile)
            continue
        werte |= _aus_text_ziehen(inhalt)
    # Was im Tresor liegt, wird ueberall geschwaerzt. Das schliesst den Kreis:
    # die Tresorwache nimmt ein Geheimnis einmal auf, danach erkennt es jede
    # Schwaerzung woertlich wieder - auch dort, wo kein Muster greift.
    try:
        from . import tresor as _tresor
        werte |= {w for w in _tresor.alle_geheimnisse() if len(w) >= _MIN_LAENGE}
    except Exception:
        pass
    # laengste zuerst, damit Teilstuecke nicht halbe Reste stehen lassen
    _WOERTLICH = sorted(werte, key=len, reverse=True)
    return _WOERTLICH


def woertlich_schwaerzen(text: str | None) -> str | None:
    if not text:
        return text
    aus = text
    for geheim in bekannte_geheimnisse():
        if geheim in aus:
            aus = aus.replace(geheim, ERSATZ)
    return aus
