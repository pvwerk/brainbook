"""Zweck: Das Brainbook - Uebersetzung von Jans Worten in die Ablage.

Es steht in keinem Regal, in keiner Liste und in keinem Verzeichnis. Es wird
nicht gescannt, nicht sortiert, nicht vom Testleser geprueft und erscheint
nicht im Regal. Es liegt beim Bibliothekar am Tresen.

Darin stehen nur Verweise: Jans Stichwort, Vorsilbe, Kosename oder Synonym auf
der einen Seite - Projekt, Kategorien, Pfade und Kurznotiz auf der anderen.
Sagt er "ETM CRM", muss daraus `~/Projekte/etm-gutachten` werden, ohne dass
er den Ordnernamen kennen muss.

Es ist absichtlich eine einzige, von Hand lesbare Datei: das Verzeichnis dazu
hat Jan selbst im Kopf.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from . import konfig, regalwart

# Liegt oben in der Ablage, nicht in einem Regal: der Platz am Tresen.
BUCH = konfig.LK_HEIM / "brainbook.md"
EINTRAGUNGEN = konfig.LK_HEIM / "brainbook-eintragungen.jsonl"

TRENNER = "·"
FELDER = ("auch", "was", "regal", "kategorien", "verweise", "notiz")

KOPFTEXT = """# Brainbook

Jans eigenes Buch. Es steht in **keinem Regal und in keiner Liste** - es liegt
beim Bibliothekar am Tresen. Hier stehen nur Verweise: links ein Wort, wie Jan
es sagt, rechts der Ort in der Ablage.

Es wird nicht gescannt, nicht sortiert, nicht vom Testleser geprueft und
erscheint nicht im Regal.

Von Hand aenderbar. Aufbau je Eintrag:

```
## <Stichwort, wie Jan es sagt>
auch: <Synonym> · <Synonym>
was: <ein Satz: was ist das>
regal: <Projektname> — <Pfad>
kategorien: <Thema> · <Thema>
verweise: <Pfad oder Verweis> · <Pfad oder Verweis>
notiz: <Kurznotiz>            (mehrfach erlaubt)
```

Angelegt und ergaenzt wird mit `landkarte merke "<Stichwort>" --ist <projekt>`.
Nachgeschlagen wird damit von selbst: `landkarte wo "<Stichwort>"` sieht hier
zuerst nach.
"""


def _normal(text: str) -> str:
    return regalwart._normal(text or "")


# ------------------------------------------------------------------- Lesen


def laden() -> dict[str, dict]:
    """{stichwort: eintrag} in der Reihenfolge der Datei."""
    if not BUCH.exists():
        return {}
    try:
        text = BUCH.read_text("utf-8")
    except OSError:
        return {}

    eintraege: dict[str, dict] = {}
    aktuell: str | None = None
    in_beispiel = False
    for zeile in text.splitlines():
        if zeile.strip().startswith("```"):
            in_beispiel = not in_beispiel
            continue
        if in_beispiel:
            continue
        kopf = re.match(r"^##\s+(.+?)\s*$", zeile)
        if kopf:
            aktuell = kopf.group(1).strip()
            eintraege[aktuell] = {"stichwort": aktuell, "auch": [], "was": "",
                                  "regal": [], "kategorien": [],
                                  "verweise": [], "notiz": []}
            continue
        if not aktuell:
            continue
        treffer = re.match(r"^\s*(\w+)\s*:\s*(.+?)\s*$", zeile)
        if not treffer:
            continue
        feld, wert = treffer.group(1).lower(), treffer.group(2).strip()
        if feld not in FELDER:
            continue
        if feld == "was":
            eintraege[aktuell]["was"] = wert
        elif feld == "notiz":
            eintraege[aktuell]["notiz"].append(wert)
        elif feld == "regal":
            eintraege[aktuell]["regal"].append(_regal_lesen(wert))
        else:
            teile = [t.strip() for t in re.split(r"\s*[·|]\s*|\s*,\s*", wert)
                     if t.strip()]
            eintraege[aktuell][feld].extend(teile)
    return eintraege


def _regal_lesen(wert: str) -> dict:
    treffer = re.match(r"^(.*?)\s+[—-]{1,2}\s+(\S.*)$", wert)
    if treffer:
        return {"name": treffer.group(1).strip(), "pfad": treffer.group(2).strip()}
    return {"name": wert.strip(), "pfad": ""}


def nachschlagen(begriff: str) -> list[dict]:
    """Jans Wort in Ablagenorte uebersetzen. Genauer Treffer zuerst."""
    gesucht = _normal(begriff)
    if not gesucht:
        return []
    aus: list[dict] = []
    for eintrag in laden().values():
        namen = [eintrag["stichwort"]] + eintrag["auch"]
        punkte = 0
        wie = ""
        for name in namen:
            n = _normal(name)
            if not n:
                continue
            if n == gesucht:
                punkte = max(punkte, 130)
                wie = f"dein Stichwort „{name}\""
            elif gesucht in n or n in gesucht:
                punkte = max(punkte, 110)
                wie = wie or f"dein Stichwort „{name}\""
        for kategorie in eintrag["kategorien"]:
            if _normal(kategorie) == gesucht:
                punkte = max(punkte, 100)
                wie = wie or f"deine Kategorie „{kategorie}\""
        if punkte:
            aus.append({**eintrag, "punkte": punkte, "wie": wie})
    aus.sort(key=lambda e: -e["punkte"])
    return aus


def stichworte() -> list[str]:
    """Nur die Schluesselwoerter - fuer den Auszug beim Sitzungsstart."""
    aus = []
    for eintrag in laden().values():
        aus.append(eintrag["stichwort"])
    return aus


# ----------------------------------------------------------------- Schreiben


def _regal_aufloesen(angabe: str) -> dict | None:
    """Projektangabe auf ein bekanntes Regal abbilden."""
    regale = regalwart.laden().get("regale", {})
    pfad_kandidat = Path(angabe).expanduser()
    if str(pfad_kandidat) in regale:
        e = regale[str(pfad_kandidat)]
        return {"name": e.get("name", pfad_kandidat.name),
                "pfad": str(pfad_kandidat), "eintrag": e}
    gesucht = _normal(angabe)
    beste = None
    for pfad, e in regale.items():
        if e.get("verschwunden"):
            continue
        namen = [e.get("name", "")] + list(e.get("aliase", []))
        for name in namen:
            n = _normal(name)
            if not n:
                continue
            if n == gesucht:
                return {"name": e.get("name"), "pfad": pfad, "eintrag": e}
            if gesucht and (gesucht in n or n in gesucht) and beste is None:
                beste = {"name": e.get("name"), "pfad": pfad, "eintrag": e}
    return beste


def merken(stichwort: str, ist: list[str] | None = None,
           auch: list[str] | None = None, was: str = "",
           kategorien: list[str] | None = None,
           verweise: list[str] | None = None,
           notiz: list[str] | None = None) -> dict:
    """Eintrag anlegen oder ergaenzen. Es werden nur Verweise gespeichert."""
    BUCH.parent.mkdir(parents=True, exist_ok=True)
    eintraege = laden()

    # bestehenden Eintrag finden, auch ueber Synonyme
    schluessel = None
    for name, eintrag in eintraege.items():
        if _normal(name) == _normal(stichwort) or any(
                _normal(a) == _normal(stichwort) for a in eintrag["auch"]):
            schluessel = name
            break
    if schluessel is None:
        schluessel = stichwort.strip()
        eintraege[schluessel] = {"stichwort": schluessel, "auch": [], "was": "",
                                 "regal": [], "kategorien": [], "verweise": [],
                                 "notiz": []}
    eintrag = eintraege[schluessel]
    neu = {"regal": [], "auch": [], "kategorien": [], "verweise": [],
           "notiz": [], "was": ""}

    for angabe in (ist or []):
        aufgeloest = _regal_aufloesen(angabe)
        if not aufgeloest:
            neu.setdefault("unbekannt", []).append(angabe)
            continue
        if not any(r["pfad"] == aufgeloest["pfad"] for r in eintrag["regal"]):
            eintrag["regal"].append({"name": aufgeloest["name"],
                                     "pfad": aufgeloest["pfad"]})
            neu["regal"].append(aufgeloest["name"])
        e = aufgeloest["eintrag"]
        # Nur die Gruppe uebernehmen. Ordnernamen wie app/ oder tests/ sind
        # keine Themen von Jan - die stehen schon in Liste 2 der Karte.
        kategorie = e.get("gruppe", "")
        if kategorie and kategorie not in eintrag["kategorien"]:
            eintrag["kategorien"].append(kategorie)
            neu["kategorien"].append(kategorie)
        for verweis in (f"{aufgeloest['pfad']}/KARTE.md",
                        f"{aufgeloest['pfad']}/.landkarte/buch/"):
            if Path(verweis.rstrip("/")).exists() and verweis not in eintrag["verweise"]:
                eintrag["verweise"].append(verweis)
                neu["verweise"].append(verweis)
        if not eintrag["was"] and e.get("zweck"):
            eintrag["was"] = e["zweck"]
            neu["was"] = e["zweck"]

    for name in (auch or []):
        if name and name not in eintrag["auch"]:
            eintrag["auch"].append(name)
            neu["auch"].append(name)
    for kategorie in (kategorien or []):
        if kategorie and kategorie not in eintrag["kategorien"]:
            eintrag["kategorien"].append(kategorie)
            neu["kategorien"].append(kategorie)
    for verweis in (verweise or []):
        if verweis and verweis not in eintrag["verweise"]:
            eintrag["verweise"].append(verweis)
            neu["verweise"].append(verweis)
    for text in (notiz or []):
        if text and text not in eintrag["notiz"]:
            eintrag["notiz"].append(text)
            neu["notiz"].append(text)
    if was:
        eintrag["was"] = was
        neu["was"] = was

    _schreiben(eintraege)
    with EINTRAGUNGEN.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "zeit": int(time.time()),
            "gesetzt": datetime.now().isoformat(timespec="seconds"),
            "stichwort": schluessel, "neu": neu,
        }, ensure_ascii=False) + "\n")
    return {"stichwort": schluessel, "eintrag": eintrag, "neu": neu}


def _schreiben(eintraege: dict[str, dict]) -> None:
    z = [KOPFTEXT.rstrip(), ""]
    for eintrag in eintraege.values():
        z.append(f"## {eintrag['stichwort']}")
        if eintrag["auch"]:
            z.append(f"auch: {f' {TRENNER} '.join(eintrag['auch'])}")
        if eintrag["was"]:
            z.append(f"was: {eintrag['was']}")
        for regal in eintrag["regal"]:
            if regal.get("pfad"):
                z.append(f"regal: {regal['name']} — {regal['pfad']}")
            else:
                z.append(f"regal: {regal['name']}")
        if eintrag["kategorien"]:
            z.append(f"kategorien: {f' {TRENNER} '.join(eintrag['kategorien'])}")
        if eintrag["verweise"]:
            z.append(f"verweise: {f' {TRENNER} '.join(eintrag['verweise'])}")
        for text in eintrag["notiz"]:
            z.append(f"notiz: {text}")
        z.append("")
    BUCH.write_text("\n".join(z) + "\n", "utf-8")


def ausgeben(eintrag: dict) -> list[str]:
    """Einen Eintrag als Textblock."""
    z = [f"{eintrag['stichwort']}"]
    if eintrag.get("wie"):
        z[0] += f"   ({eintrag['wie']})"
    if eintrag.get("auch"):
        z.append(f"   auch: {', '.join(eintrag['auch'])}")
    if eintrag.get("was"):
        z.append(f"   was: {eintrag['was']}")
    for regal in eintrag.get("regal", []):
        pfad = regal.get("pfad", "").replace(str(konfig.HEIM), "~")
        z.append(f"   Regal: {regal['name']}" + (f"  {pfad}" if pfad else ""))
    if eintrag.get("kategorien"):
        z.append(f"   Kategorien: {', '.join(eintrag['kategorien'])}")
    for verweis in eintrag.get("verweise", []):
        z.append(f"   → {verweis.replace(str(konfig.HEIM), '~')}")
    for text in eintrag.get("notiz", []):
        z.append(f"   Notiz: {text}")
    return z
