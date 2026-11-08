"""Zweck: Der Aufseher - erkennt Muster, findet wo die Kette hakt, schlägt vor.

Er ändert nichts. Er misst, benennt und schreibt Vorschläge in WERKSTATT.md.
Begründung steht dort im Kopf: ein Bauteil, das sich selbst umschreibt,
beschädigt im Fehlerfall genau das Protokoll, das den Fehler belegen müsste.

Das Messen ist reine Rechnung. Das Modell wird nur gebraucht, um aus den
Zahlen benannte Schwachstellen und konkrete Vorschläge zu machen.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import buch, chronik, konfig, pruefer

WERKSTATT = konfig.LK_HEIM / "WERKSTATT.md"
BEFUND_JSON = konfig.LK_HEIM / "befund.json"

_PFAD = re.compile(r"(/[\w.\-]+){2,}")
_ZAHL = re.compile(r"\b\d+\b")
_HEX = re.compile(r"\b[0-9a-f]{8,}\b", re.I)


def fehlersignatur(text: str) -> str:
    s = (text or "").strip().lower()
    s = _PFAD.sub("<pfad>", s)
    s = _HEX.sub("<id>", s)
    s = _ZAHL.sub("<n>", s)
    s = re.sub(r"\s+", " ", s)
    return s[:140]


def _claude_sitzungen_vorhanden(zurueck_tage: int = 7) -> int:
    """Wie viele Claude-Sitzungsdateien gab es zuletzt - Gegenprobe zur Chronik."""
    wurzel = konfig.HEIM / ".claude" / "projects"
    if not wurzel.is_dir():
        return -1
    grenze = time.time() - zurueck_tage * 86400
    anzahl = 0
    for ordner, _unter, dateien in os.walk(wurzel):
        for name in dateien:
            if not name.endswith(".jsonl"):
                continue
            try:
                if os.stat(os.path.join(ordner, name)).st_mtime >= grenze:
                    anzahl += 1
            except OSError:
                continue
    return anzahl


def befund(zurueck: int = 30) -> dict:
    """Alle Messwerte. Reine Rechnung, kein Modell."""
    alle = list(chronik.eintraege(zurueck))
    jetzt = time.time()

    # 1. wiederkehrende Fehler
    signaturen: Counter = Counter()
    beispiel: dict[str, dict] = {}
    for e in alle:
        if not e.get("f"):
            continue
        sig = fehlersignatur(e["f"])
        if not sig:
            continue
        signaturen[sig] += 1
        beispiel.setdefault(sig, {"werkzeug": e.get("w"), "projekt": e.get("p"),
                                  "text": (e.get("f") or "")[:220],
                                  "ziel": e.get("d", "")})
    wiederkehrend = [{"signatur": s, "anzahl": n, **beispiel[s]}
                     for s, n in signaturen.most_common(15) if n >= 2]

    # 2. zaehe Dateien: viele Aenderungen in einer Sitzung = nicht verstanden
    je_sitzung: dict[tuple, int] = {}
    for e in alle:
        if e.get("w") not in ("Edit", "Write", "MultiEdit"):
            continue
        ziel = chronik._dateiziel(e)
        if not ziel:
            continue
        je_sitzung[(e.get("s"), e.get("p"), ziel)] = \
            je_sitzung.get((e.get("s"), e.get("p"), ziel), 0) + 1
    zaeh = sorted(
        ({"datei": ziel, "projekt": projekt, "aenderungen": n, "sitzung": s}
         for (s, projekt, ziel), n in je_sitzung.items() if n >= 8),
        key=lambda x: -x["aenderungen"])[:15]

    # 3. Kette pruefen
    sitzungen_chronik = len({e.get("s") for e in alle if e.get("s")})
    sitzungen_echt = _claude_sitzungen_vorhanden(7)
    chronik_7 = len({e.get("s") for e in chronik.eintraege(7) if e.get("s")})
    faellig = chronik.kapitel_faellig(zurueck=14)
    alt_faellig = [f for f in faellig if jetzt - f["ende"] > 2 * 86400]

    register = {}
    if konfig.REGISTER.exists():
        try:
            register = json.loads(konfig.REGISTER.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            register = {}
    veraltete_karten = []
    for p in register.get("projekte", []):
        wurzel = Path(p["wurzel"])
        karte = wurzel / "KARTE.md"
        if not karte.exists():
            veraltete_karten.append({"projekt": p["name"], "grund": "keine KARTE.md"})
            continue
        try:
            karte_alter = karte.stat().st_mtime
        except OSError:
            continue
        zuletzt_benutzt = p.get("rang", {}).get("zuletzt") or 0
        if zuletzt_benutzt and zuletzt_benutzt - karte_alter > 7 * 86400:
            veraltete_karten.append({
                "projekt": p["name"],
                "grund": f"Karte {int((zuletzt_benutzt - karte_alter)/86400)} Tage "
                         f"älter als die letzte Arbeit daran"})

    # 4. wird die Bibliothek benutzt?
    karte_gelesen = 0
    landkarte_aufrufe = 0
    for e in alle:
        ziel = (e.get("d") or "")
        if e.get("w") == "Read" and ("KARTE.md" in ziel or ".landkarte/" in ziel):
            karte_gelesen += 1
        if e.get("w") == "Bash" and "landkarte" in ziel:
            landkarte_aufrufe += 1

    # 5. Regeln, die mehrfach auftauchen = nicht angekommen
    regel_zaehler: Counter = Counter()
    regel_orte: dict[str, list[str]] = {}
    for p in register.get("projekte", []):
        wurzel = Path(p["wurzel"])
        if not wurzel.is_dir():
            continue
        for k in buch.kapitel_sammeln(wurzel):
            for r in k.get("regeln", []):
                sig = fehlersignatur(r)[:90]
                if len(sig) < 15:
                    continue
                regel_zaehler[sig] += 1
                regel_orte.setdefault(sig, []).append(
                    f"{p['name']}/{k['datei']}")
    hochziehen = [{"regel": beispiel_text(regel_orte[s]), "signatur": s,
                   "anzahl": n, "orte": regel_orte[s][:5]}
                  for s, n in regel_zaehler.most_common(12) if n >= 2]

    # 6. Zusicherungen und Gegenproben (vom Pruefer, deterministisch)
    try:
        pruefung = pruefer.vollpruefung()
    except Exception as fehler:
        pruefung = {"befunde": [{"schwere": "schwer",
                                 "befund": f"Prüfung fehlgeschlagen: {fehler}",
                                 "ort": "-", "projekt": "-"}],
                    "gegenproben": []}

    # 7. Streit zwischen den Schreibern: wie oft waren die Zwillinge uneinig
    uneinig, einstimmig, einzeln = 0, 0, 0
    for datei in sorted(chronik.SITZUNGEN.glob("*.json")):
        try:
            eintrag = json.loads(datei.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if eintrag.get("schreiber") == 1:
            einzeln += 1
        elif eintrag.get("einstimmig") is True:
            einstimmig += 1
        elif eintrag.get("einstimmig") is False:
            uneinig += 1

    return {
        "gemessen": int(jetzt),
        "zeitraum_tage": zurueck,
        "aufrufe": len(alle),
        "sitzungen": sitzungen_chronik,
        "wiederkehrende_fehler": wiederkehrend,
        "zaehe_dateien": zaeh,
        "kette": {
            "chronist": {
                "sitzungen_7_tage_chronik": chronik_7,
                "sitzungsdateien_7_tage": sitzungen_echt,
                "verdacht": (sitzungen_echt > 0 and chronik_7 == 0),
            },
            "schreiber": {
                "faellig": len(faellig),
                "ueberfaellig": len(alt_faellig),
                "liste": [f["sitzung"][:8] for f in alt_faellig[:8]],
            },
            "setzer": {"veraltete_karten": veraltete_karten},
            "nutzung": {
                "karte_gelesen": karte_gelesen,
                "landkarte_aufrufe": landkarte_aufrufe,
                "verdacht": (len(alle) > 300 and karte_gelesen == 0
                             and landkarte_aufrufe == 0),
            },
            "scanfehler": register.get("scanfehler", []),
        },
        "regeln_hochziehen": hochziehen,
        "zusicherungen": pruefung["befunde"],
        "gegenproben": pruefung["gegenproben"],
        "schreiberstreit": {"einstimmig": einstimmig, "uneinig": uneinig,
                            "nur_einer": einzeln},
        "abweichungen": pruefer.abweichungen_auswerten(),
    }


def beispiel_text(orte: list[str]) -> str:
    return orte[0] if orte else ""


ANWEISUNG = """Du bist der Aufseher einer Wissensablage. Unten stehen Messwerte \
über ihren Betrieb der letzten Wochen: wiederkehrende Fehler, Dateien die \
auffällig oft nachgebessert wurden, und ob die Verarbeitungskette läuft.

Deine Aufgabe: aus den Zahlen benannte Schwachstellen und konkrete Vorschläge \
machen. Du änderst nichts, du schlägst vor.

Beachte besonders den Abschnitt ABWEICHUNGEN: dort steht, wo die beiden \
unabhängigen Schreiber auseinandergingen. Eine Häufung ist keine Schuld eines \
Schreibers - beide sind derselbe Prompt in zwei Prozessen. Eine Häufung zeigt \
einen Mangel an der Anweisung oder am Protokoll, und die Zeile "Massnahme" \
nennt die Stelle. Eine Positionsvorliebe des Schiedsrichters ist ein schwerer \
Befund, weil die Reihenfolge zufällig vertauscht wird.

Harte Regeln:
- Nur was in den Messwerten steht. Nichts hinzuerfinden.
- Jeder Vorschlag muss ausführbar sein: welche Datei, welche Änderung, warum.
- Keine allgemeinen Ratschläge ("besser testen"). Konkret oder weglassen.
- Wenn die Messwerte in Ordnung sind, sage das in einem Satz und schlage nichts vor.
- Deutsch, knapp, keine Einleitung.

Antworte NUR in diesem Aufbau:

## Schwachstellen
<Je Befund ein Stichpunkt: **Benennung** -- was die Zahlen zeigen und was das \
bedeutet. Nach Schwere sortiert. Wenn keine: "keine erkennbar">

## Vorschläge
<Je Vorschlag ein Stichpunkt: was zu ändern ist, in welcher Datei oder welchem \
Bauteil, und welchen Befund es behebt. Wenn keine: "keine">

## Nach oben ziehen
<Regeln, die laut Messwerten mehrfach nötig waren und deshalb in die \
Dauer-Anweisungen (CLAUDE.md oder Gedächtnis) gehören. Wenn keine: "keine">
"""


SCHIEDS_ANWEISUNG = """Zwei Aufseher haben unabhängig voneinander dieselben \
Messwerte beurteilt. Du bist der Schiedsrichter.

Vergleiche beide Beurteilungen inhaltlich. Wo sie sich widersprechen oder wo \
einer etwas hat, das der andere nicht hat: entscheide an den MESSWERTEN, nicht \
nach Mehrheit. Was die Messwerte nicht belegen, fliegt raus. Baue eine \
Endfassung mit allem Belegten aus beiden.

Antworte im Aufbau der Beurteilungen (## Schwachstellen, ## Vorschläge, \
## Nach oben ziehen) und hänge am Ende an:

ABWEICHUNGEN:
<was unterschiedlich war und welche Fassung recht hatte; wenn gleich: "keine">
"""


def bericht(mit_modell: bool = True, zurueck: int = 30,
            doppelt: bool | None = None) -> dict:
    daten = befund(zurueck)
    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    BEFUND_JSON.write_text(json.dumps(daten, ensure_ascii=False, indent=1), "utf-8")

    zahlen = messwerte_text(daten)
    urteil = ""
    abweichungen = ""
    konf = konfig.laden()
    if doppelt is None:
        doppelt = konf.get("aufseher_doppelt", True)
    if mit_modell:
        modell = konf.get("aufseher_modell", konf.get("schreiber_modell", "sonnet"))
        anfrage = ANWEISUNG + "\n\n=== MESSWERTE ===\n" + zahlen
        if doppelt:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as pool:
                laeufe = [pool.submit(buch._claude_rufen, anfrage, modell)
                          for _ in range(2)]
                ergebnisse = [f.result() for f in laeufe]
            fassungen = [a for ok, a in ergebnisse if ok]
            if len(fassungen) == 2:
                erfolg, spruch = buch._claude_rufen(
                    SCHIEDS_ANWEISUNG + "\n\n=== MESSWERTE ===\n" + zahlen
                    + "\n\n=== BEURTEILUNG A ===\n" + fassungen[0]
                    + "\n\n=== BEURTEILUNG B ===\n" + fassungen[1], modell)
                if erfolg:
                    from .pruefer import _abweichungen_trennen
                    urteil, abweichungen = _abweichungen_trennen(spruch)
                else:
                    urteil = fassungen[0]
                    abweichungen = f"Schiedsrichter nicht erreichbar: {spruch[:200]}"
            elif fassungen:
                urteil = fassungen[0]
                abweichungen = "Nur ein Aufseher hat geantwortet, Gegenprobe fehlt."
            else:
                urteil = ("_Aufseher-Modell nicht erreichbar: "
                          + "; ".join(a for _, a in ergebnisse)[:300] + "_")
        else:
            erfolg, antwort = buch._claude_rufen(anfrage, modell)
            urteil = antwort if erfolg else f"_Aufseher-Modell nicht erreichbar: {antwort}_"

    z = ["# Werkstatt — Zustand der Bibliothek", "",
         f"Stand {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
         f"Zeitraum {zurueck} Tage · {daten['aufrufe']} Werkzeugaufrufe in "
         f"{daten['sitzungen']} Sitzungen.", "",
         "> Der Aufseher misst und schlägt vor, er ändert nichts. Ein Bauteil, "
         "das sich selbst umschreibt, beschädigt im Fehlerfall genau das "
         "Protokoll, das den Fehler belegen müsste. Eingebaut wird von Hand.", ""]
    if urteil:
        z.append(urteil)
        z.append("")
    if abweichungen:
        z.append("## Abweichungen zwischen den beiden Aufsehern")
        z.append("")
        z.append(abweichungen)
        z.append("")
    z.append("---")
    z.append("")
    z.append("## Messwerte")
    z.append("")
    z.append("```")
    z.append(zahlen)
    z.append("```")
    WERKSTATT.write_text("\n".join(z) + "\n", "utf-8")
    return {"werkstatt": str(WERKSTATT), "befund": str(BEFUND_JSON),
            "mit_modell": mit_modell, "doppelt": bool(doppelt), "daten": daten}


def messwerte_text(d: dict) -> str:
    z: list[str] = []
    z.append(f"Zeitraum: {d['zeitraum_tage']} Tage, {d['aufrufe']} Aufrufe, "
             f"{d['sitzungen']} Sitzungen")
    z.append("")
    z.append("WIEDERKEHRENDE FEHLER (gleiche Ursache mehrfach):")
    if d["wiederkehrende_fehler"]:
        for f in d["wiederkehrende_fehler"]:
            z.append(f"  {f['anzahl']}x  [{f.get('werkzeug')}] "
                     f"{(f.get('projekt') or '').split('/')[-1]} "
                     f"{f.get('ziel','')}: {f['text']}")
    else:
        z.append("  keine")
    z.append("")
    z.append("ZAEHE DATEIEN (viele Nachbesserungen in einer Sitzung):")
    if d["zaehe_dateien"]:
        for f in d["zaehe_dateien"]:
            z.append(f"  {f['aenderungen']}x  {(f.get('projekt') or '').split('/')[-1]}"
                     f"/{f['datei']}")
    else:
        z.append("  keine")
    z.append("")
    k = d["kette"]
    z.append("KETTE:")
    c = k["chronist"]
    z.append(f"  Chronist: {c['sitzungen_7_tage_chronik']} Sitzungen in der Chronik "
             f"(7 Tage), {c['sitzungsdateien_7_tage']} Sitzungsdateien vorhanden"
             + ("  >>> VERDACHT: Hook schreibt nicht" if c["verdacht"] else ""))
    s = k["schreiber"]
    z.append(f"  Schreiber: {s['faellig']} Kapitel fällig, {s['ueberfaellig']} "
             f"davon über 2 Tage alt" + (f" ({', '.join(s['liste'])})" if s["liste"] else ""))
    v = k["setzer"]["veraltete_karten"]
    z.append(f"  Setzer: {len(v)} veraltete oder fehlende Karten")
    for e in v[:10]:
        z.append(f"    - {e['projekt']}: {e['grund']}")
    n = k["nutzung"]
    z.append(f"  Nutzung: Karte {n['karte_gelesen']}x gelesen, "
             f"landkarte {n['landkarte_aufrufe']}x aufgerufen"
             + ("  >>> VERDACHT: Bibliothek wird nicht benutzt" if n["verdacht"] else ""))
    if k["scanfehler"]:
        z.append(f"  Scanfehler: {len(k['scanfehler'])}")
        for e in k["scanfehler"][:6]:
            z.append(f"    - {e['projekt']}: {e['fehler']}")
    z.append("")
    z.append("ZUSICHERUNGEN (Setzer und Bibliothekar):")
    schwer = [b for b in d.get("zusicherungen", []) if b["schwere"] == "schwer"]
    leicht = [b for b in d.get("zusicherungen", []) if b["schwere"] != "schwer"]
    if schwer or leicht:
        z.append(f"  {len(schwer)} schwere, {len(leicht)} leichte Befunde")
        for b in (schwer + leicht)[:18]:
            z.append(f"    - [{b['schwere']}] {b.get('projekt','?')}: "
                     f"{b['befund']} ({b['ort']})")
    else:
        z.append("  alle erfüllt")
    z.append("")
    z.append("GEGENPROBE CHRONIK gegen Sitzungsprotokoll:")
    if d.get("gegenproben"):
        for g in d["gegenproben"][:10]:
            z.append(f"  {g['sitzung'][:8]}: {g.get('anzahl_fehlen')} von "
                     f"{g.get('transkript')} Aufrufen fehlen in der Chronik, "
                     f"Werkzeuge: {g.get('fehlende_werkzeuge')}")
    else:
        z.append("  keine Lücke gefunden")
    z.append("")
    st = d.get("schreiberstreit") or {}
    z.append(f"SCHREIBER-ZWILLINGE: {st.get('einstimmig',0)} einstimmig, "
             f"{st.get('uneinig',0)} mit bereinigten Abweichungen, "
             f"{st.get('nur_einer',0)} ohne Gegenprobe")
    z.append("")
    ab = d.get("abweichungen") or {}
    z.append(f"ABWEICHUNGEN ZWISCHEN DEN SCHREIBERN ({ab.get('gesamt',0)} erfasst):")
    if ab.get("arten"):
        for art, anzahl in sorted(ab["arten"].items(), key=lambda kv: -kv[1]):
            z.append(f"  {anzahl:>4}x {art}")
    else:
        z.append("  keine erfasst")
    if ab.get("hinweise"):
        z.append("  HAEUFUNGEN - hier muss korrigiert werden:")
        for h in ab["hinweise"]:
            z.append(f"    {h['anzahl']}x {h['art']} -> {h['stelle']}")
            z.append(f"       Massnahme: {h['massnahme']}")
            for b in h.get("beispiele", []):
                z.append(f"       Beispiel: {b}")
    if ab.get("schieflage"):
        s = ab["schieflage"]
        z.append(f"  >>> POSITIONSVORLIEBE: {round(s['anteil_erste']*100)} % der "
                 f"{s['entschieden']} Entscheidungen gingen an die erste Fassung. "
                 f"{s['befund']}")
    z.append("")
    z.append("REGELN, DIE MEHRFACH NOETIG WAREN:")
    if d["regeln_hochziehen"]:
        for r in d["regeln_hochziehen"]:
            z.append(f"  {r['anzahl']}x: {r['signatur']}")
            z.append(f"       in {', '.join(r['orte'])}")
    else:
        z.append("  keine")
    return "\n".join(z)
