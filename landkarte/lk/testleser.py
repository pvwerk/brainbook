"""Zweck: Der Testleser - liest stichprobenartig ein Kapitel und prueft, ob
das Verzeichnis darauf schliessen laesst, was drin steht.

Der entscheidende Griff: das Modell wird NICHT gefragt, ob das Verzeichnis gut
ist - das waere eine Meinung. Es sagt nur, wonach jemand suchen wuerde, um
dieses Kapitel zu finden. Dann schlaegt das Verzeichnis wirklich nach. Findet
es nichts, ist das ein Beweis. Nach der Korrektur wird dieselbe Suche
wiederholt; findet sie jetzt, ist die Korrektur belegt.

Korrigiert wird nach Risiko getrennt:
  - fehlende Schlagworte und Regal-Etiketten: selbst, ergaenzend, rueckbaubar
  - Buch im falschen Regal: nur bei eindeutigem Befund, sonst Vorschlag
  - der Kapiteltext selbst: nie. Er ist Beweismittel des Schiedsrichters.
"""

from __future__ import annotations

import json
import math
import random
import re
import time
from datetime import date, datetime
from pathlib import Path

from . import buch, karte, konfig, regalwart, suche

LESUNGEN = konfig.LK_HEIM / "lesungen.jsonl"
SCHLAGWORT_DATEI = "schlagworte.md"
MAX_NEUE_SCHLAGWORTE = 8
EINDEUTIG_AB = 0.8          # Anteil der Dateien, der fuer einen Umzug reicht

ANWEISUNG = """Du bist Testleser einer Wissensablage. Unten steht ein Kapitel \
eines Arbeitsbuchs. Du beurteilst NICHT, ob es gut ist. Du beantwortest nur \
zwei Fragen, damit die Ablage danach maschinell geprueft werden kann.

1. WONACH WUERDE JEMAND SUCHEN, um genau dieses Kapitel wiederzufinden?
   Nenne 5 bis 8 Suchbegriffe. Jeder Begriff muss:
   - ein bis drei Woerter lang sein
   - aus dem Kapitel hervorgehen, nicht erfunden sein
   - etwas sein, was man Monate spaeter tatsaechlich eintippt: ein Fehlertext,
     ein Werkzeugname, ein Dateiname, ein Fachbegriff, ein Symptom
   Keine Allerweltsbegriffe wie "Fehler", "Datei", "Projekt", "Code".

2. ZU WELCHEM PROJEKT gehoert das Kapitel, nur nach seinem Inhalt geurteilt?
   Nenne den Projektnamen, wie er im Kapitel oder in den Dateipfaden auftaucht.
   Wenn der Inhalt das nicht hergibt: "unklar".

Antworte NUR in diesem Format, ohne Vorrede:

BEGRIFFE:
- <begriff>
- <begriff>

PROJEKT: <name oder unklar>
BEGRUENDUNG: <ein Satz, woran du das Projekt erkennst>
"""


def _antwort_lesen(text: str) -> dict:
    begriffe: list[str] = []
    projekt = ""
    begruendung = ""
    abschnitt = ""
    for zeile in (text or "").splitlines():
        s = zeile.strip()
        if re.match(r"^BEGRIFFE\s*:", s, re.I):
            abschnitt = "begriffe"
            continue
        treffer = re.match(r"^PROJEKT\s*:\s*(.+)$", s, re.I)
        if treffer:
            projekt = treffer.group(1).strip().strip("`\"'")
            abschnitt = ""
            continue
        treffer = re.match(r"^BEGR(?:UE|Ü)NDUNG\s*:\s*(.+)$", s, re.I)
        if treffer:
            begruendung = treffer.group(1).strip()
            abschnitt = ""
            continue
        if abschnitt == "begriffe" and s.startswith(("-", "*")):
            begriff = s[1:].strip().strip("`\"'")
            if 2 <= len(begriff) <= 60:
                begriffe.append(begriff)
    return {"begriffe": begriffe[:10], "projekt": projekt,
            "begruendung": begruendung}


# ------------------------------------------------------------- Auswahl


def kapitel_zaehlen() -> int:
    """Wie viele Kapitel die Bibliothek ueberhaupt hat."""
    anzahl = 0
    for wurzel in regalwart.laden().get("regale", {}):
        pfad = Path(wurzel)
        if not pfad.is_dir():
            continue
        try:
            anzahl += len(buch.kapitel_sammeln(pfad))
        except OSError:
            continue
    return anzahl


def anzahl_aus_anteil(anteil: float) -> int:
    """20 Prozent der Bibliothek - mindestens eins, wenn es etwas gibt."""
    gesamt = kapitel_zaehlen()
    if gesamt <= 0:
        return 0
    return max(1, math.ceil(gesamt * anteil / 100.0))


def kapitel_auswaehlen(anzahl: int = 1) -> list[dict]:
    """Kapitel aussuchen: lange nicht geprueft und inhaltsreich zuerst."""
    gelesen: dict[str, dict] = {}
    if LESUNGEN.exists():
        try:
            for zeile in LESUNGEN.read_text("utf-8").splitlines():
                if not zeile.strip():
                    continue
                try:
                    e = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                gelesen[e.get("kapitel", "")] = e
        except OSError:
            pass

    kandidaten: list[dict] = []
    for wurzel in regalwart.laden().get("regale", {}):
        pfad = Path(wurzel)
        if not pfad.is_dir():
            continue
        for k in buch.kapitel_sammeln(pfad):
            letzte = gelesen.get(k["pfad"])
            punkte = 100.0
            if letzte:
                tage = (time.time() - (letzte.get("zeit") or 0)) / 86400
                punkte = min(tage * 2, 90)
            punkte += min(len(k.get("fallen", [])) * 3, 20)
            punkte += min(len(k.get("regeln", [])) * 2, 10)
            kandidaten.append({"kapitel": k, "projekt": str(pfad),
                               "punkte": punkte + random.random() * 10,
                               "zuletzt": letzte})
    kandidaten.sort(key=lambda x: -x["punkte"])
    return kandidaten[:anzahl]


# ------------------------------------------------------------- Pruefung


def _suchprobe(begriff: str, kapitelpfad: str, projektwurzel: str) -> dict:
    """Findet das Verzeichnis dieses Kapitel oder sein Projekt?"""
    treffer = suche.finden(begriff, grenze=60)
    kapitel_getroffen = any(t["ort"] == kapitelpfad for t in treffer)
    projekt_getroffen = any(t["ort"].startswith(projektwurzel) for t in treffer)
    return {"begriff": begriff, "treffer": len(treffer),
            "kapitel_gefunden": kapitel_getroffen,
            "projekt_gefunden": projekt_getroffen}


def schlagwortdatei(wurzel: Path) -> Path:
    return wurzel / ".landkarte" / SCHLAGWORT_DATEI


def schlagworte_laden(wurzel: Path) -> dict[str, list[str]]:
    """{kapitel-datei: [begriffe]} aus der maschinell gepflegten Datei."""
    p = schlagwortdatei(wurzel)
    if not p.exists():
        return {}
    aus: dict[str, list[str]] = {}
    aktuell = ""
    try:
        for zeile in p.read_text("utf-8").splitlines():
            treffer = re.match(r"^##\s+(.+)$", zeile)
            if treffer:
                aktuell = treffer.group(1).strip()
                aus.setdefault(aktuell, [])
                continue
            s = zeile.strip()
            if aktuell and s.startswith("- "):
                aus[aktuell].append(s[2:].strip())
    except OSError:
        return {}
    return aus


def schlagworte_ergaenzen(wurzel: Path, kapiteldatei: str,
                          neue: list[str]) -> Path:
    """Begriffe anhaengen. Eigene Datei, damit notizen.md dem Menschen bleibt."""
    p = schlagwortdatei(wurzel)
    vorhanden = schlagworte_laden(wurzel)
    schon = {b.lower() for b in vorhanden.get(kapiteldatei, [])}
    zu_ergaenzen = [b for b in neue if b.lower() not in schon]
    if not zu_ergaenzen:
        return p

    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(
            f"# Schlagworte: {wurzel.name}\n\n"
            "Vom Testleser gepflegt, nicht von Hand. Hier stehen Begriffe, "
            "unter denen ein Kapitel gefunden werden soll, aber ohne sie nicht "
            "gefunden wurde. Handschriftliches gehoert in `notizen.md`.\n\n"
            "Jede Zeile ist belegt: der Begriff wurde vor dem Eintrag gesucht "
            "und nicht gefunden, nach dem Eintrag gefunden.\n", "utf-8")

    zeilen = p.read_text("utf-8").splitlines()
    kopf = f"## {kapiteldatei}"
    if kopf in zeilen:
        stelle = zeilen.index(kopf)
        einfuegen = len(zeilen)
        for j in range(stelle + 1, len(zeilen)):
            if zeilen[j].startswith("## "):
                einfuegen = j
                break
        letzter = stelle
        for j in range(stelle + 1, einfuegen):
            if zeilen[j].strip().startswith("- "):
                letzter = j
        for b in reversed(zu_ergaenzen):
            zeilen.insert(letzter + 1, f"- {b}")
    else:
        zeilen += ["", kopf, ""] + [f"- {b}" for b in zu_ergaenzen]
    p.write_text("\n".join(zeilen) + "\n", "utf-8")
    return p


# -------------------------------------------------- Regal und Beschriftung


def _regal_pruefen(kapitel: dict, projektwurzel: str,
                   vermutet: str) -> list[dict]:
    """Steht das Buch im richtigen Regal, ist das Regal richtig beschriftet."""
    befunde: list[dict] = []
    regale = regalwart.laden().get("regale", {})
    eigenes = regale.get(projektwurzel) or {}

    # 1. Zeigen die Dateien des Kapitels woandershin?
    dateien = kapitel["kopf"].get("dateien") or []
    if dateien:
        zuordnung: dict[str, int] = {}
        for d in dateien:
            pfad = d if d.startswith("/") else f"{projektwurzel}/{d}"
            beste = ""
            for wurzel in regale:
                if pfad.startswith(wurzel + "/") and len(wurzel) > len(beste):
                    beste = wurzel
            if beste:
                zuordnung[beste] = zuordnung.get(beste, 0) + 1
        if zuordnung:
            gesamt = sum(zuordnung.values())
            fuehrend, anzahl = max(zuordnung.items(), key=lambda kv: kv[1])
            if fuehrend != projektwurzel and anzahl / gesamt >= EINDEUTIG_AB:
                befunde.append({
                    "art": "regal_falsch", "schwere": "schwer",
                    "befund": f"{anzahl} von {gesamt} Dateien des Kapitels "
                              f"liegen in {Path(fuehrend).name}, nicht in "
                              f"{Path(projektwurzel).name}",
                    "ziel": fuehrend, "eindeutig": True})
            elif fuehrend != projektwurzel:
                befunde.append({
                    "art": "regal_zweifelhaft", "schwere": "leicht",
                    "befund": f"nur {anzahl} von {gesamt} Dateien zeigen nach "
                              f"{Path(fuehrend).name} — nicht eindeutig, "
                              f"deshalb nur gemeldet",
                    "ziel": fuehrend, "eindeutig": False})

    # 2. Ist der vom Inhalt her vermutete Name als Alias bekannt?
    if vermutet and vermutet.lower() not in ("unklar", "unbekannt", ""):
        normal = regalwart._normal(vermutet)
        aliase = {regalwart._normal(a) for a in eigenes.get("aliase", [])}
        if normal and normal not in aliase:
            # Gehoert der Name schon einem anderen Regal? Dann kein Alias.
            fremd = ""
            for wurzel, e in regale.items():
                if wurzel == projektwurzel:
                    continue
                if normal in {regalwart._normal(a) for a in e.get("aliase", [])}:
                    fremd = e.get("name", Path(wurzel).name)
                    break
            if fremd:
                befunde.append({
                    "art": "alias_belegt", "schwere": "leicht",
                    "befund": f"Der Inhalt deutet auf „{vermutet}\", aber dieser "
                              f"Name gehoert schon zu {fremd}. Nicht uebernommen.",
                    "ziel": "", "eindeutig": False})
            else:
                befunde.append({
                    "art": "alias_fehlt", "schwere": "leicht",
                    "befund": f"„{vermutet}\" war kein Alias von "
                              f"{eigenes.get('name', Path(projektwurzel).name)}",
                    "ziel": vermutet, "eindeutig": True})

    # 3. Steht das Regal ordentlich im Verzeichnis?
    if not eigenes:
        befunde.append({"art": "regal_fehlt", "schwere": "schwer",
                        "befund": "Das Projekt steht nicht im Regalverzeichnis",
                        "ziel": projektwurzel, "eindeutig": False})
    elif not (Path(projektwurzel) / "KARTE.md").exists():
        befunde.append({"art": "karte_fehlt", "schwere": "schwer",
                        "befund": "Das Regal hat kein Inhaltsverzeichnis "
                                  "(KARTE.md fehlt)",
                        "ziel": projektwurzel, "eindeutig": True})
    return befunde


def _alias_eintragen(projektwurzel: str, alias: str) -> bool:
    konf = konfig.laden()
    aliase = dict(konf.get("aliase") or {})
    liste = list(aliase.get(projektwurzel, []))
    if alias in liste:
        return False
    liste.append(alias)
    aliase[projektwurzel] = liste
    konf["aliase"] = aliase
    konfig.schreiben(konf)
    return True


# ------------------------------------------------------------------ Lesung


def lesung(kapitel: dict, projektwurzel: str, modell: str | None = None,
           trocken: bool = False) -> dict:
    """Ein Kapitel lesen, das Verzeichnis daran pruefen, Belegbares korrigieren."""
    konf = konfig.laden()
    modell = modell or konf.get("testleser_modell",
                                konf.get("schreiber_modell", "sonnet"))
    try:
        volltext = Path(kapitel["pfad"]).read_text("utf-8")
    except OSError as fehler:
        return {"ok": False, "grund": f"Kapitel nicht lesbar: {fehler}"}

    anfrage = ANWEISUNG + "\n\n=== KAPITEL ===\n" + volltext
    if trocken:
        return {"ok": True, "trocken": True, "zeichen": len(anfrage)}

    erfolg, antwort = buch._claude_rufen(anfrage, modell)
    if not erfolg:
        return {"ok": False, "grund": f"Testleser fehlgeschlagen: {antwort}"}
    gelesen = _antwort_lesen(antwort)
    if not gelesen["begriffe"]:
        return {"ok": False, "grund": "keine Suchbegriffe erkannt"}

    wurzel = Path(projektwurzel)
    # --- erste Messung: findet das Verzeichnis das Kapitel? ---
    vorher = [_suchprobe(b, kapitel["pfad"], projektwurzel)
              for b in gelesen["begriffe"]]
    blind = [p["begriff"] for p in vorher
             if not p["kapitel_gefunden"] and not p["projekt_gefunden"]]

    korrekturen: list[dict] = []
    nachher: list[dict] = []
    if blind and not trocken:
        schlagworte_ergaenzen(wurzel, kapitel["datei"],
                              blind[:MAX_NEUE_SCHLAGWORTE])
        karte.bauen(wurzel)
        nachher = [_suchprobe(b, kapitel["pfad"], projektwurzel) for b in blind]
        geheilt = [p["begriff"] for p in nachher
                   if p["kapitel_gefunden"] or p["projekt_gefunden"]]
        korrekturen.append({
            "art": "schlagworte",
            "getan": f"{len(blind)} Begriffe ergaenzt, {len(geheilt)} davon "
                     f"nachweislich jetzt auffindbar",
            "begriffe": blind[:MAX_NEUE_SCHLAGWORTE],
            "belegt": geheilt})

    # --- Regal, Beschriftung, Verzeichnis ---
    befunde = _regal_pruefen(kapitel, projektwurzel, gelesen["projekt"])
    vorschlaege: list[dict] = []
    for b in befunde:
        if b["art"] == "alias_fehlt" and not trocken:
            if _alias_eintragen(projektwurzel, b["ziel"]):
                korrekturen.append({"art": "alias",
                                    "getan": f"Alias „{b['ziel']}\" ergaenzt"})
        elif b["art"] == "karte_fehlt" and not trocken:
            karte.bauen(wurzel)
            korrekturen.append({"art": "karte",
                                "getan": "Inhaltsverzeichnis neu gesetzt"})
        else:
            vorschlaege.append(b)

    satz = {
        "zeit": int(time.time()),
        "gelesen": datetime.now().isoformat(timespec="seconds"),
        "kapitel": kapitel["pfad"],
        "kapiteldatei": kapitel["datei"],
        "projekt": projektwurzel,
        "modell": modell,
        "begriffe": gelesen["begriffe"],
        "vermutetes_projekt": gelesen["projekt"],
        "begruendung": gelesen["begruendung"],
        "blind_vorher": blind,
        "messung_vorher": vorher,
        "messung_nachher": nachher,
        "korrekturen": korrekturen,
        "vorschlaege": vorschlaege,
    }
    LESUNGEN.parent.mkdir(parents=True, exist_ok=True)
    with LESUNGEN.open("a", encoding="utf-8") as f:
        f.write(json.dumps(satz, ensure_ascii=False) + "\n")

    if vorschlaege:
        _journal(wurzel, kapitel, vorschlaege)
    return {"ok": True, **satz}


def _journal(wurzel: Path, kapitel: dict, vorschlaege: list[dict]) -> None:
    kopf = "" if regalwart.JOURNAL.exists() else (
        "# Regal-Journal\n\nWas der Regalwart veraendert hat. Nur angehaengt.\n")
    with regalwart.JOURNAL.open("a", encoding="utf-8") as f:
        if kopf:
            f.write(kopf)
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} "
                f"— Testleser zu `{kapitel['datei']}`\n\n")
        for v in vorschlaege:
            f.write(f"- **{v['art']}** ({v['schwere']}): {v['befund']}\n")


def runde(anzahl: int = 1, modell: str | None = None,
          trocken: bool = False, anteil: float | None = None) -> list[dict]:
    if anteil:
        anzahl = anzahl_aus_anteil(anteil)
    aus = []
    for kandidat in kapitel_auswaehlen(anzahl):
        aus.append(lesung(kandidat["kapitel"], kandidat["projekt"],
                          modell=modell, trocken=trocken))
    return aus


def bilanz(zurueck_tage: int = 120) -> dict:
    """Wie gut ist das Verzeichnis - gemessen, nicht geschaetzt."""
    if not LESUNGEN.exists():
        return {"lesungen": 0}
    grenze = time.time() - zurueck_tage * 86400
    lesungen = 0
    begriffe = 0
    blind = 0
    geheilt = 0
    offene: list[dict] = []
    try:
        for zeile in LESUNGEN.read_text("utf-8").splitlines():
            if not zeile.strip():
                continue
            try:
                e = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if (e.get("zeit") or 0) < grenze:
                continue
            lesungen += 1
            begriffe += len(e.get("begriffe", []))
            blind += len(e.get("blind_vorher", []))
            for k in e.get("korrekturen", []):
                geheilt += len(k.get("belegt", []))
            for v in e.get("vorschlaege", []):
                offene.append({**v, "kapitel": e.get("kapiteldatei")})
    except OSError:
        return {"lesungen": 0}
    return {"lesungen": lesungen, "begriffe": begriffe, "blind": blind,
            "geheilt": geheilt,
            "trefferquote": round(1 - blind / begriffe, 3) if begriffe else None,
            "offene_vorschlaege": offene[:20]}
