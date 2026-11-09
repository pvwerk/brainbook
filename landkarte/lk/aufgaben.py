"""Zweck: Verzeichnis der offenen Punkte im Brainbook.

Offene Punkte stehen heute ueberall und nirgends: in `docs/OFFEN.md`, als
`- [ ]` in einer Liste, als "OFFENER PUNKT" in einer Notiz, als TODO im Code -
und in Saetzen wie "das kuemmere ich spaeter", die nach der Sitzung niemand
mehr findet. Dieses Verzeichnis sammelt sie an einer Stelle.

Zwei Quellen, bewusst getrennt:

**Geerntet** - alles, was in den Projekten schon geschrieben steht. Wird bei
jedem Aufruf neu gelesen, nie zwischengespeichert. Verschwindet der Punkt in
der Datei (Haken gesetzt, Zeile durchgestrichen), verschwindet er hier.
Dadurch kann das Verzeichnis nicht veralten.

**Eingetragen** - was ausdruecklich mit `landkarte aufgabe "..."` gemeldet
wurde. Liegt in `~/.landkarte/aufgaben.jsonl` und bleibt, bis es erledigt
gemeldet wird. Das ist der Platz fuer die Punkte, die sonst nirgends stehen.

Der Zustand "erledigt" wird nie geraten. Eine geerntete Zeile gilt als
erledigt, sobald sie in der Quelle nicht mehr offen ist; ein eingetragener
Punkt nur, wenn jemand es sagt.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import konfig

EIGENE = konfig.LK_HEIM / "aufgaben.jsonl"

# Dateien, in denen offene Punkte stehen duerfen. Alles andere waere Rauschen:
# ein TODO mitten im Code ist eine Notiz an den naechsten Leser, keine Aufgabe.
QUELLDATEIEN = (
    "OFFEN.md", "TODO.md", "AUFGABEN.md", "OPEN.md",
    "docs/OFFEN.md", "docs/TODO.md", "docs/AUFGABEN.md",
    ".landkarte/notizen.md",
)

# "- [ ] Text" - unerledigter Haken in einer Markdown-Liste
_HAKEN = re.compile(r"^\s*[-*+]\s+\[\s\]\s+(.+?)\s*$")
# Zeilen, die sich selbst als offen bezeichnen. Genommen wird ab dem Fund,
# nicht die ganze Zeile - sonst wandert ein halber Absatz in die Liste.
_OFFEN_WORT = re.compile(
    r"(?i)\b(offener punkt|noch offen|offen:|zu tun:|to ?do:|nicht erledigt|"
    r"fehlt noch|steht noch aus|muss noch|bleibt zu tun)\b")
# Durchgestrichenes gilt als erledigt
_ERLEDIGT = re.compile(r"^\s*[-*+]\s+\[[xX]\]|~~.+~~")
# Eine Tabellenzeile: | 4 | **Punkt** | Warum | Wohin |
_TABELLE = re.compile(r"^\s*\|(.+)\|\s*$")
# Ueberschriften, unter denen nichts Offenes mehr steht
_ERLEDIGT_ABSCHNITT = re.compile(r"(?i)^#{1,6}\s+.*\b(erledigt|abgeschlossen|"
                                 r"entschieden|geschafft|bewusst nicht)\b")
_OFFEN_DATEI = re.compile(r"(?i)^(docs/)?(OFFEN|TODO|AUFGABEN|OPEN)\.md$")


def _entschmuecken(text: str) -> str:
    """Markdown-Auszeichnung entfernen, ohne den Text zu verstuemmeln."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)[*_]{1,2}(?=\S)|(?<=\S)[*_]{1,2}(?!\w)", "", text)
    text = re.sub(r"(?i)^(offener punkt|zu tun|noch offen)\s*[:\-]\s*", "", text.strip())
    return text.strip(" *_|").strip()


@dataclass
class Aufgabe:
    text: str
    projekt: str = ""
    quelle: str = ""
    zeile: int = 0
    art: str = "geerntet"      # geerntet | eingetragen
    dringlich: bool = False
    angelegt: int = 0
    id: str = ""
    erledigt_am: int = 0

    def kurz(self) -> str:
        t = " ".join(self.text.split())
        return t[:160]


# --------------------------------------------------------------- Ernten


def _tabellentext(zeile: str) -> str | None:
    """Aus einer Markdown-Tabellenzeile den Punkt herausziehen.

    In `OFFEN.md` steht der Punkt in der Spalte nach der laufenden Nummer.
    Ist er durchgestrichen, gilt er als erledigt. Trennzeilen (|---|---|) und
    Kopfzeilen werden ausgelassen.
    """
    treffer = _TABELLE.match(zeile)
    if not treffer:
        return None
    zellen = [z.strip() for z in treffer.group(1).split("|")]
    if not zellen or all(set(z) <= set("-: ") for z in zellen):
        return None
    # erste Zelle ist oft nur eine Nummer
    inhalt = [z for z in zellen if z and not re.fullmatch(r"[0-9]+[a-z]?", z)]
    if not inhalt:
        return None
    punkt = inhalt[0]
    if punkt.startswith("~~") or punkt.lower() in ("punkt", "was", "aufgabe", "#"):
        return None
    # Der Rest der Zeile sagt manchmal, dass es doch erledigt ist.
    if re.search(r"(?i)\*\*erledigt\b", " | ".join(inhalt[1:])):
        return None
    return _entschmuecken(punkt)


def _aus_datei(pfad: Path, projekt: str, wurzel: Path) -> list[Aufgabe]:
    try:
        zeilen = pfad.read_text("utf-8", errors="replace").splitlines()
    except OSError:
        return []
    try:
        rel_name = str(pfad.relative_to(wurzel))
    except ValueError:
        rel_name = pfad.name
    ist_offen_datei = bool(_OFFEN_DATEI.match(rel_name))
    aus: list[Aufgabe] = []
    abschnitt_erledigt = False
    for nr, zeile in enumerate(zeilen, 1):
        if zeile.lstrip().startswith("#"):
            abschnitt_erledigt = bool(_ERLEDIGT_ABSCHNITT.match(zeile.strip()))
            continue
        if abschnitt_erledigt or _ERLEDIGT.search(zeile):
            continue
        treffer = _HAKEN.match(zeile)
        if treffer:
            text = _entschmuecken(treffer.group(1))
        elif ist_offen_datei and (tab := _tabellentext(zeile)):
            text = tab
        elif (wort := _OFFEN_WORT.search(zeile)):
            # Nur ab dem Fundwort, und nur wenn danach noch Inhalt kommt.
            rest = zeile[wort.start():].strip().lstrip("#*->| ").strip()
            rest = re.sub(r"(?i)^(offen|zu tun|to ?do)\s*:\s*", "", rest)
            if len(rest) < 12 or rest.endswith((":", "—", "-")):
                continue
            text = _entschmuecken(rest)
        else:
            continue
        if text.strip().startswith(("~~", "<!--")):
            continue
        aus.append(Aufgabe(
            text=text, projekt=projekt, quelle=rel_name, zeile=nr,
            art="geerntet",
            dringlich=bool(re.search(r"(?i)\b(dringend|wichtig|kritisch|sofort)\b", text)),
        ))
    return aus


def ernten(nur_projekt: str | None = None) -> list[Aufgabe]:
    """Offene Punkte aus allen bekannten Projekten einsammeln."""
    aus: list[Aufgabe] = []
    eintraege: list[dict] = []
    if konfig.REGISTER.exists():
        try:
            eintraege = json.loads(konfig.REGISTER.read_text("utf-8")).get("projekte", [])
        except (OSError, json.JSONDecodeError):
            eintraege = []
    for e in sorted(eintraege, key=lambda x: x.get("name", "")):
        name = e.get("name", "")
        if nur_projekt and name != nur_projekt:
            continue
        if not e.get("wurzel"):
            continue
        wurzel = Path(e["wurzel"]).expanduser()
        if not wurzel.is_dir():
            continue
        for rel in QUELLDATEIEN:
            datei = wurzel / rel
            if datei.is_file():
                aus.extend(_aus_datei(datei, name, wurzel))
    return aus


# --------------------------------------------------------------- Eigene


def _lies_eigene() -> list[dict]:
    if not EIGENE.exists():
        return []
    aus = []
    for z in EIGENE.read_text("utf-8", errors="replace").splitlines():
        z = z.strip()
        if not z:
            continue
        try:
            aus.append(json.loads(z))
        except json.JSONDecodeError:
            continue
    # Spaetere Zeile gewinnt: die Datei ist ein Journal, kein Zustand.
    nach_id: dict[str, dict] = {}
    for e in aus:
        nach_id[e.get("id", "")] = e
    return list(nach_id.values())


def _schreib_eigene(alle: list[dict]) -> None:
    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    with EIGENE.open("w", encoding="utf-8") as f:
        for e in alle:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def eintragen(text: str, projekt: str = "", dringlich: bool = False) -> Aufgabe:
    alle = _lies_eigene()
    kennung = f"a{int(time.time()*1000):x}"
    neu = Aufgabe(text=text, projekt=projekt, art="eingetragen",
                  dringlich=dringlich, angelegt=int(time.time()), id=kennung)
    alle.append(asdict(neu))
    _schreib_eigene(alle)
    return neu


def erledigen(kennung: str) -> bool:
    alle = _lies_eigene()
    for e in alle:
        if e.get("id") == kennung and not e.get("erledigt_am"):
            e["erledigt_am"] = int(time.time())
            _schreib_eigene(alle)
            return True
    return False


def eigene(auch_erledigte: bool = False) -> list[Aufgabe]:
    aus = []
    for e in _lies_eigene():
        if not auch_erledigte and e.get("erledigt_am"):
            continue
        aus.append(Aufgabe(**{k: v for k, v in e.items()
                              if k in Aufgabe.__dataclass_fields__}))
    return aus


# --------------------------------------------------------------- Zusammen


def alle(nur_projekt: str | None = None) -> list[Aufgabe]:
    zusammen = eigene() + ernten(nur_projekt)
    if nur_projekt:
        zusammen = [a for a in zusammen if a.projekt == nur_projekt or not a.projekt]
    # Dringliches zuerst, dann Eingetragenes vor Geerntetem, dann nach Projekt.
    zusammen.sort(key=lambda a: (not a.dringlich, a.art != "eingetragen",
                                 a.projekt, a.kurz().lower()))
    return zusammen


def bericht(nur_projekt: str | None = None, grenze: int = 0) -> str:
    liste = alle(nur_projekt)
    if not liste:
        return "Keine offenen Punkte gefunden."
    zeilen = [f"OFFENE PUNKTE — {len(liste)} Stück", ""]
    letztes = None
    gezeigt = 0
    for a in liste:
        if grenze and gezeigt >= grenze:
            zeilen.append(f"  … {len(liste) - gezeigt} weitere")
            break
        kopf = a.projekt or "(ohne Projekt)"
        if kopf != letztes:
            zeilen.append(f"[{kopf}]")
            letztes = kopf
        marke = "!" if a.dringlich else " "
        herkunft = (f"{a.quelle}:{a.zeile}" if a.art == "geerntet"
                    else f"eingetragen {a.id}")
        zeilen.append(f"  {marke} {a.kurz()}")
        zeilen.append(f"      {herkunft}")
        gezeigt += 1
    return "\n".join(zeilen)


def als_markdown(nur_projekt: str | None = None) -> str:
    """Fuer das Brainbook: eine Liste, die man auch von Hand lesen kann."""
    liste = alle(nur_projekt)
    zeilen = ["# Offene Punkte", "",
              f"_Von `landkarte aufgaben` gesammelt, Stand "
              f"{time.strftime('%d.%m.%Y %H:%M')}. Geerntete Punkte stammen aus den "
              f"Dateien der Projekte und verschwinden hier, sobald sie dort "
              f"erledigt sind._", ""]
    if not liste:
        zeilen.append("Nichts offen.")
        return "\n".join(zeilen) + "\n"
    letztes = None
    for a in liste:
        kopf = a.projekt or "(ohne Projekt)"
        if kopf != letztes:
            zeilen += ["", f"## {kopf}", ""]
            letztes = kopf
        marke = "**!** " if a.dringlich else ""
        herkunft = (f"`{a.quelle}:{a.zeile}`" if a.art == "geerntet"
                    else f"eingetragen, `{a.id}`")
        zeilen.append(f"- [ ] {marke}{a.kurz()}  \n      {herkunft}")
    return "\n".join(zeilen) + "\n"
