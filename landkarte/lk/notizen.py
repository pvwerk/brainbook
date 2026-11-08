"""Zweck: Handgepflegte Notizen eines Projekts - werden nie überschrieben."""

from __future__ import annotations

from datetime import date
from pathlib import Path

VORLAGE = """# Notizen: {name}

Diese Datei gehört dem Menschen (und Claude per `landkarte notiz`).
`landkarte` liest sie und baut sie in die KARTE.md ein, überschreibt sie aber
nie. Alles Handgeschriebene gehört hierher, nicht in die KARTE.md.

**Keine Passwörter, Token oder Schlüssel hier hinein.** Nur Zeiger darauf.

## Fallen

Wo schon Zeit verloren ging. Form: **kurze Benennung** — was passiert und warum.

## Regeln

Was man beim nächsten Mal von Anfang an richtig machen muss.

## Zugaenge

Wo die Zugangsdaten liegen — nicht die Daten selbst.

## Offen

Was noch zu tun ist.
"""

ABSCHNITTE = ("Fallen", "Regeln", "Zugaenge", "Offen")


def pfad(wurzel: Path) -> Path:
    return wurzel / ".landkarte" / "notizen.md"


def anlegen_wenn_fehlt(wurzel: Path) -> Path:
    p = pfad(wurzel)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(VORLAGE.format(name=wurzel.name), "utf-8")
    return p


def laden(wurzel: Path) -> dict[str, list[str]]:
    p = pfad(wurzel)
    if not p.exists():
        return {}
    try:
        text = p.read_text("utf-8")
    except OSError:
        return {}
    aus: dict[str, list[str]] = {}
    aktuell = ""
    for zeile in text.splitlines():
        if zeile.startswith("## "):
            aktuell = zeile[3:].strip()
            aus.setdefault(aktuell, [])
            continue
        s = zeile.strip()
        if aktuell and s.startswith(("- ", "* ")):
            rein = s[2:].strip()
            if rein:
                aus[aktuell].append(rein)
    return {k: v for k, v in aus.items() if v}


def anhaengen(wurzel: Path, abschnitt: str, text: str) -> Path:
    """Einen Punkt in einen Abschnitt schreiben, Abschnitt notfalls anlegen."""
    abschnitt = abschnitt.strip().capitalize()
    if abschnitt == "Zugänge":
        abschnitt = "Zugaenge"
    p = anlegen_wenn_fehlt(wurzel)
    zeilen = p.read_text("utf-8").splitlines()
    eintrag = f"- [{date.today().isoformat()}] {text.strip()}"

    ziel = None
    for i, zeile in enumerate(zeilen):
        if zeile.strip() == f"## {abschnitt}":
            ziel = i
            break
    if ziel is None:
        zeilen += ["", f"## {abschnitt}", "", eintrag, ""]
    else:
        # hinter den letzten Punkt dieses Abschnitts setzen
        einfuegen = len(zeilen)
        for j in range(ziel + 1, len(zeilen)):
            if zeilen[j].startswith("## "):
                einfuegen = j
                break
        letzter_punkt = ziel
        for j in range(ziel + 1, einfuegen):
            if zeilen[j].strip().startswith(("- ", "* ")):
                letzter_punkt = j
        if letzter_punkt == ziel:
            zeilen.insert(einfuegen, eintrag)
            zeilen.insert(einfuegen, "")
        else:
            zeilen.insert(letzter_punkt + 1, eintrag)
    p.write_text("\n".join(zeilen) + "\n", "utf-8")
    return p
