"""Zweck: Die Brainbooks der anderen mitlesen - beim Nachschlagen, nicht nur beim Abgleich.

`landkarte abgleich` holt die Staende der anderen und legt sie lesbar in
`~/.landkarte/geteilt/` ab. Bis hierher war das eine Sackgasse: die Dateien
lagen da, aber `landkarte bb` und `landkarte wo` haben nur im eigenen Stand
gesucht. Wer also eine Falle gefunden hatte, die jemand anders laengst kannte,
hat sie trotzdem noch einmal gefunden - und genau das soll die gemeinsame
Bibliothek verhindern.

Dieses Modul liest die zusammengefuehrten Dateien und gibt die Treffer mit
dem Namen desjenigen zurueck, von dem sie stammen. Die Herkunft bleibt immer
sichtbar: fremdes Wissen wird nie als eigenes ausgegeben, denn es kann aus
einem anderen Projekt, einem anderen Rechner oder einem anderen Stand kommen.

Gelesen wird nur - geschrieben wird hier nie. Die Dateien in `geteilt/` baut
`abgleich.zusammenfuehren()` bei jedem Lauf neu.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import konfig

GETEILT = konfig.LK_HEIM / "geteilt"

# "## Von <name>" trennt die Beitraege der Teilnehmer. Die Ueberschrift kommt
# von abgleich.zusammenfuehren() und steht auf derselben Ebene wie die
# Abschnitte INNERHALB eines fremden Standes ("## Fallen"). Deshalb wird
# zuerst auf "Von " geprueft und erst danach auf eine gewoehnliche Ueberschrift.
_VON = re.compile(r"^##\s+Von\s+(.+?)\s*$")
_UEBERSCHRIFT = re.compile(r"^#{2,4}\s+(.+?)\s*$")
_PUNKT = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
# Erklaertext der Sammeldatei, keine Notiz
_RAUSCHEN = ("_", "#", "```", "|")


def _lesen(datei: Path) -> list[tuple[str, str, str]]:
    """Je Eintrag (Teilnehmer, Abschnitt, Text)."""
    if not datei.exists():
        return []
    teilnehmer = ""
    abschnitt = ""
    aus: list[tuple[str, str, str]] = []
    for zeile in datei.read_text("utf-8", errors="replace").splitlines():
        m = _VON.match(zeile)
        if m:
            teilnehmer = m.group(1).strip()
            abschnitt = ""
            continue
        if not teilnehmer:
            continue                      # Kopf der Sammeldatei
        m = _UEBERSCHRIFT.match(zeile)
        if m:
            abschnitt = m.group(1).strip()
            # Im Brainbook ist die Ueberschrift selbst der Eintrag - das
            # Stichwort, unter dem der andere die Sache ablegt.
            aus.append((teilnehmer, "Stichwort", abschnitt))
            continue
        m = _PUNKT.match(zeile)
        if m:
            aus.append((teilnehmer, abschnitt or "Notiz", m.group(1).strip()))
            continue
        t = zeile.strip()
        if t and not t.startswith(_RAUSCHEN):
            aus.append((teilnehmer, abschnitt or "Notiz", t))
    return aus


def nachschlagen(begriff: str, grenze: int = 12) -> list[dict]:
    """Treffer in den Staenden der anderen, Herkunft immer dabei."""
    if not begriff.strip():
        return []
    muster = re.compile(re.escape(begriff), re.I)
    roh: list[dict] = []
    for datei, quelle in ((GETEILT / "notizen.md", "Notiz"),
                          (GETEILT / "brainbook.md", "Brainbook")):
        for wer, abschnitt, text in _lesen(datei):
            if muster.search(text):
                roh.append({"teilnehmer": wer, "quelle": quelle,
                            "abschnitt": abschnitt, "text": text,
                            "ort": str(datei)})

    gesehen: set[tuple[str, str]] = set()
    aus: list[dict] = []
    for e in roh:
        schluessel = (e["teilnehmer"], e["text"][:80])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        aus.append(e)
    return aus[:grenze]


def teilnehmer() -> list[str]:
    """Von wem liegt ueberhaupt ein Stand vor?"""
    namen: list[str] = []
    for datei in (GETEILT / "notizen.md", GETEILT / "brainbook.md"):
        for wer, _, _ in _lesen(datei):
            if wer not in namen:
                namen.append(wer)
    return namen
