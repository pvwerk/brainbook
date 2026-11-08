"""Zweck: Die Absicherung - Gegenprobe, Zwillinge, Schiedsspruch, Zusicherungen.

Grundsatz: Redundanz hilft nur gegen *unabhängige* Fehler.

- Chronist: kein Zwilling, sondern eine Gegenprobe gegen das Sitzungsprotokoll,
  das Claude Code selbst schreibt - anderer Code, anderer Weg, echte Unabhängig-
  keit. Verglichen wird über die tool_use_id, also Aufruf für Aufruf.
- Schreiber und Aufseher: echte Zwillinge, zwei getrennte Prozesse, die sich
  nicht sehen. Nur hier sind die Fehler wirklich unabhängig.
- Setzer und Bibliothekar: keine Zwillinge, sondern Zusicherungen. Zwei Läufe
  desselben Skripts über dieselbe Eingabe liefern denselben Fehler; ein
  Vergleich davon kann nie anschlagen.

Bei zwei Stimmen ist nicht abstimmbar. Widersprechen sie sich, entscheidet der
Schiedsrichter am Rohprotokoll - das deshalb von keiner Rolle verändert wird.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import buch, chronik, karte, konfig, korrektur, notizen

PRUEFORDNER = konfig.LK_HEIM / "pruefung"
ABWEICHUNGEN = konfig.LK_HEIM / "abweichungen.jsonl"
# Durchgehendes Protokoll des Schiedsrichters: unabhaengig von der Bibliothek
# abgelegt, nur angehaengt, nie ueberschrieben. Es ist die Beweislage dafuer,
# welche Formataenderung welche Fehlerklasse beseitigt hat.
SPRUCHBUCH = PRUEFORDNER / "protokoll.jsonl"
MAX_FASSUNG = 9000


def protokoll_fingerabdruck(protokoll: str) -> str:
    """Kennung des Protokoll-FORMATS, nicht des Inhalts.

    Nur die Abschnittsueberschriften gehen ein. So bekommen alle Laeufe mit
    demselben Aufbau dieselbe Kennung, und man kann Abweichungen nach
    Protokollfassung gruppieren.
    """
    kopfzeilen = [z.strip() for z in protokoll.splitlines()
                  if z.strip() and z.strip() == z.strip().upper()
                  and len(z.strip()) > 8]
    roh = "|".join(kopfzeilen)
    return "f" + hashlib.sha256(roh.encode("utf-8")).hexdigest()[:10]


def spruch_festhalten(satz: dict) -> None:
    """Einen Schiedsspruch anhaengen. Niemals ueberschreiben."""
    SPRUCHBUCH.parent.mkdir(parents=True, exist_ok=True)
    with SPRUCHBUCH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(satz, ensure_ascii=False) + "\n")
# Verdacht auf Zugangsdaten in der Ablage. Der Wert muss nach Geheimnis
# aussehen, nicht nach Wort: ein Routen-Platzhalter wie "/d/:token: Label"
# darf nicht anschlagen, sonst wird der Waechter ignoriert.
_SCHLUESSELWORT = re.compile(
    r"(?<![:{$/])(pass(?:wor[dt])?|pwd|secret|token|api[_-]?key|"
    r"authorization|client[_-]?secret|private[_-]?key)"
    r"\s*[:=]\s*(?:bearer\s+)?[\"\']?([A-Za-z0-9_\-.+/=]{12,})",
    re.I,
)
_BEKANNTE_PREFIXE = re.compile(
    r"\b(sk-[A-Za-z0-9][A-Za-z0-9\-]{14,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"eyJ[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{8,}|"
    r"AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})"
)
# "Bearer <wert>" steht oft ohne Doppelpunkt
_BEARER = re.compile(r"\bbearer\s+([A-Za-z0-9_\-.+/=]{16,})", re.I)
_PLATZHALTER = {
    "label", "string", "beispiel", "example", "changeme", "yourtoken",
    "your_token", "deintoken", "none", "null", "true", "false", "undefined",
    "optional", "erforderlich", "required", "placeholder", "xxxxxxxxxxxx",
    "geheim", "secret", "token", "password", "passwort",
}


def geheimnisverdacht(zeile: str) -> str | None:
    """Gibt den verdaechtigen Ausschnitt zurueck, sonst None."""
    treffer = _BEKANNTE_PREFIXE.search(zeile)
    if treffer:
        return treffer.group(1)[:24]
    treffer = _BEARER.search(zeile)
    if treffer and treffer.group(1).lower() not in _PLATZHALTER:
        return "bearer=\u2026" + treffer.group(1)[-6:]
    for name, wert in _SCHLUESSELWORT.findall(zeile):
        rein = wert.strip("\"'.,;:)")
        if len(rein) < 12:
            continue
        if rein.lower() in _PLATZHALTER:
            continue
        if rein.startswith(("<", "{", "$", "x" * 6)):
            continue
        # Ein Geheimnis mischt Ziffern und Buchstaben; ein deutsches oder
        # englisches Wort tut das nicht.
        hat_ziffer = any(z.isdigit() for z in rein)
        hat_buchstabe = any(z.isalpha() for z in rein)
        if not (hat_ziffer and hat_buchstabe):
            continue
        # Dateinamen und Pfade sind keine Geheimnisse
        if "/" in rein or rein.endswith((".js", ".py", ".php", ".json", ".md")):
            continue
        return f"{name}=…{rein[-6:]}"
    return None


# ------------------------------------------------- Gegenprobe des Chronisten


def transkript_pfad(sitzung: str) -> Path | None:
    wurzel = konfig.HEIM / ".claude" / "projects"
    if not wurzel.is_dir():
        return None
    for ordner, _unter, dateien in os.walk(wurzel):
        if f"{sitzung}.jsonl" in dateien:
            return Path(ordner) / f"{sitzung}.jsonl"
    return None


def transkript_aufrufe(sitzung: str) -> dict:
    """Werkzeugaufrufe aus dem Sitzungsprotokoll von Claude Code.

    Wird zeilenweise gestreamt; diese Dateien werden Gigabyte gross.
    """
    pfad = transkript_pfad(sitzung)
    if not pfad:
        return {"gefunden": False, "aufrufe": {}, "fehler": {}}
    aufrufe: dict[str, dict] = {}
    fehler: dict[str, bool] = {}
    try:
        with pfad.open("r", encoding="utf-8", errors="replace") as f:
            for zeile in f:
                if '"tool_use"' not in zeile and '"tool_result"' not in zeile:
                    continue
                try:
                    e = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                inhalt = (e.get("message") or {}).get("content")
                if not isinstance(inhalt, list):
                    continue
                for block in inhalt:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        aufrufe[block.get("id", "")] = {
                            "werkzeug": block.get("name", ""),
                            "zeit": e.get("timestamp", ""),
                            "ordner": e.get("cwd", ""),
                            "nebenlauf": bool(e.get("isSidechain")),
                        }
                    elif block.get("type") == "tool_result":
                        if block.get("is_error"):
                            fehler[block.get("tool_use_id", "")] = True
    except OSError:
        return {"gefunden": False, "aufrufe": {}, "fehler": {}}
    aufrufe.pop("", None)
    return {"gefunden": True, "pfad": str(pfad), "aufrufe": aufrufe,
            "fehler": fehler}


def chronik_gegenpruefen(sitzung: str) -> dict:
    """Hook-Chronik gegen das Sitzungsprotokoll stellen, Aufruf für Aufruf."""
    transkript = transkript_aufrufe(sitzung)
    alle_eigenen = list(chronik.eintraege(zurueck=60, sitzung=sitzung))
    eigene = {e.get("i"): e for e in alle_eigenen if e.get("i")}
    ohne_kennung = len([e for e in alle_eigenen if not e.get("i")])
    nachgetragen = len([e for e in alle_eigenen if e.get("q") == "transkript"])

    if not transkript["gefunden"]:
        return {"ok": None, "grund": "Sitzungsprotokoll nicht gefunden",
                "chronik": len(eigene) + ohne_kennung}

    # Eine Sitzung, deren Chronik vollstaendig nachgetragen ist, sagt nichts
    # ueber den Hook: die Eintraege stammen aus derselben Quelle, gegen die
    # geprueft wird. Das als Datenverlust zu melden waere falsch.
    if alle_eigenen and nachgetragen == len(alle_eigenen):
        gekappt = nachgetragen >= 20000
        return {"ok": None,
                "grund": ("nur nachgetragen, der Hook lief in dieser Sitzung "
                          "noch nicht" + (" (Nachtrag bei 20000 gekappt)"
                                          if gekappt else "")),
                "nachgetragen": nachgetragen, "gekappt": gekappt,
                "transkript": len([k for k, v in transkript["aufrufe"].items()
                                   if not v["nebenlauf"]]),
                "chronik": len(eigene)}

    # Nebenläufe (Unteragenten) feuern keine PostToolUse-Hooks der Hauptsitzung
    haupt = {k: v for k, v in transkript["aufrufe"].items() if not v["nebenlauf"]}
    fehlen = sorted(set(haupt) - set(eigene))
    ueberzaehlig = sorted(set(eigene) - set(transkript["aufrufe"]))

    fehler_transkript = {k for k in transkript["fehler"] if k in haupt}
    fehler_chronik = {k for k, v in eigene.items() if v.get("f")}
    fehler_verpasst = sorted(fehler_transkript - fehler_chronik)

    return {
        "ok": not fehlen and not ueberzaehlig and not fehler_verpasst,
        "transkript": len(haupt),
        "chronik": len(eigene),
        "ohne_kennung": ohne_kennung,
        "nachgetragen": nachgetragen,
        "fehlen": fehlen[:40],
        "anzahl_fehlen": len(fehlen),
        "ueberzaehlig": ueberzaehlig[:20],
        "fehler_transkript": len(fehler_transkript),
        "fehler_chronik": len(fehler_chronik),
        "fehler_verpasst": fehler_verpasst[:20],
        "fehlende_werkzeuge": _zaehlen([haupt[k]["werkzeug"] for k in fehlen]),
    }


def _zaehlen(liste: list[str]) -> dict:
    aus: dict[str, int] = {}
    for x in liste:
        aus[x] = aus.get(x, 0) + 1
    return dict(sorted(aus.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------- Zwillinge und Schiedsspruch

SCHIEDS_ANWEISUNG = """Zwei Schreiber haben unabhängig voneinander dasselbe \
Maschinenprotokoll zu einem Kapitel verarbeitet. Sie haben sich nicht gesehen, \
und du weisst nicht, welcher welcher ist. Du bist der Schiedsrichter.

Deine Aufgabe:
1. Vergleiche beide Fassungen inhaltlich, nicht sprachlich. Dieselbe Sache \
anders formuliert ist kein Unterschied.
2. Wo sie sich widersprechen oder wo einer etwas hat, das der andere nicht hat: \
entscheide am MASCHINENPROTOKOLL. Nicht nach Mehrheit, nicht nach besserem Stil, \
nicht nach Reihenfolge. Das Protokoll ist die einzige Wahrheit.
3. Lässt sich eine Stelle am Protokoll nicht entscheiden, erfinde keine \
Entscheidung: nimm sie als offene Frage ins Kapitel auf und kennzeichne sie \
unten als strittig.
4. Was in keiner Fassung durch das Protokoll gedeckt ist, fliegt raus.
5. Baue daraus eine Endfassung mit allem Gedeckten aus beiden.

Harte Regeln:
- Nichts erfinden, auch nicht beim Zusammenführen.
- Keine Passwörter, Token oder Schlüssel übernehmen.
- Deutsch, knapp.

Antworte in genau diesem Aufbau:

TITEL: <eine Zeile, max 60 Zeichen>

## Ziel
## Vorgehen
## Fallen
## Regeln daraus
## Offen

ABWEICHUNGEN:
<Je Abweichung GENAU EINE Zeile in diesem Format, mit senkrechten Strichen:
ART | WER | Beschreibung mit Belegstelle aus dem Protokoll

ART ist eines von:
  erfindung    - eine Fassung behauptet etwas, das das Protokoll nicht deckt
  auslassung   - eine Fassung übergeht etwas, das klar im Protokoll steht
  fehldeutung  - beide sehen die Stelle, lesen sie aber verschieden
  formulierung - nur sprachlich verschieden, inhaltlich gleich
  strittig     - am Protokoll nicht entscheidbar

WER ist ERSTE, ZWEITE oder KEINE (bei strittig und formulierung immer KEINE).
Es bezeichnet die Fassung, die RECHT hatte.

Wenn die Fassungen inhaltlich gleich waren, schreibe eine einzige Zeile:
formulierung | KEINE | inhaltlich gleich>
"""


ARTEN = ("erfindung", "auslassung", "fehldeutung", "formulierung", "strittig")


def abweichungen_lesen(text: str) -> list[dict]:
    """Die Zeilen des Schiedsspruchs in Daten verwandeln."""
    aus: list[dict] = []
    for zeile in (text or "").splitlines():
        s = zeile.strip().lstrip("-*0123456789. ").strip()
        if not s or "|" not in s:
            continue
        teile = [x.strip() for x in s.split("|", 2)]
        if len(teile) < 2:
            continue
        art = teile[0].lower()
        if art not in ARTEN:
            continue
        wer = teile[1].upper()
        if wer not in ("ERSTE", "ZWEITE", "KEINE"):
            wer = "KEINE"
        aus.append({"art": art, "wer": wer,
                    "beschreibung": (teile[2] if len(teile) > 2 else "")[:400]})
    return aus


def _abweichungen_trennen(text: str) -> tuple[str, str]:
    treffer = re.search(r"^ABWEICHUNGEN\s*:\s*$", text, re.M)
    if not treffer:
        treffer = re.search(r"^ABWEICHUNGEN\s*:", text, re.M)
    if not treffer:
        return text, ""
    return text[: treffer.start()].rstrip(), text[treffer.end():].strip()


def _aehnlichkeit(a: str, b: str) -> float:
    reinigen = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()
    return difflib.SequenceMatcher(None, reinigen(a), reinigen(b)).ratio()


def kapitel_doppelt(sitzung: str, modell: str | None = None) -> dict:
    """Zwei unabhängige Schreiber, dann Schiedsspruch. Ergebnis wird abgelegt."""
    bericht = chronik.sitzung_verdichten(sitzung)
    if not bericht:
        return {"ok": False, "grund": "keine Chronik zu dieser Sitzung"}
    projekt = bericht.get("projekt") or ""
    wurzel = Path(projekt)
    if not projekt or not wurzel.is_dir():
        return {"ok": False, "grund": f"Projektordner nicht auffindbar: {projekt}"}

    konf = konfig.laden()
    modell = modell or konf.get("schreiber_modell", buch.STANDARD_MODELL)
    protokoll = buch.bericht_text(bericht)
    fingerabdruck = protokoll_fingerabdruck(protokoll)
    strittig: list[dict] = []
    anfrage = buch.ANWEISUNG + "\n\n=== MASCHINENPROTOKOLL ===\n" + protokoll

    # zwei getrennte Prozesse, gleichzeitig, ohne gemeinsamen Zustand
    with ThreadPoolExecutor(max_workers=2) as pool:
        laeufe = [pool.submit(buch._claude_rufen, anfrage, modell) for _ in range(2)]
        ergebnisse = [f.result() for f in laeufe]

    fassungen = [antwort for erfolg, antwort in ergebnisse if erfolg]
    if not fassungen:
        return {"ok": False, "grund": "beide Schreiber fehlgeschlagen: "
                + "; ".join(a for _, a in ergebnisse)[:300]}
    if len(fassungen) == 1:
        # ein Schreiber ausgefallen: Kapitel schreiben, Ausfall vermerken
        titel, koerper = buch._titel_trennen(fassungen[0])
        abweichungen = ("- Nur ein Schreiber hat geantwortet, die Gegenprobe "
                        "fehlt für dieses Kapitel.")
        einstimmig = None
        aehnlich = None
        strittig = []
    else:
        aehnlich = _aehnlichkeit(*fassungen)
        # Reihenfolge mischen: sonst bevorzugt der Schiedsrichter messbar die
        # erste Position, und das sähe über die Zeit wie Wahrheit aus.
        reihenfolge = [0, 1]
        random.shuffle(reihenfolge)
        erste, zweite = fassungen[reihenfolge[0]], fassungen[reihenfolge[1]]
        schieds = (SCHIEDS_ANWEISUNG
                   + "\n\n=== MASCHINENPROTOKOLL ===\n" + protokoll
                   + "\n\n=== ERSTE FASSUNG ===\n" + erste
                   + "\n\n=== ZWEITE FASSUNG ===\n" + zweite)
        erfolg, spruch = buch._claude_rufen(schieds, modell)
        if not erfolg:
            titel, koerper = buch._titel_trennen(fassungen[0])
            abweichungen = f"- Schiedsrichter nicht erreichbar: {spruch[:200]}"
            einstimmig = None
        else:
            kapiteltext, abweichungen = _abweichungen_trennen(spruch)
            titel, koerper = buch._titel_trennen(kapiteltext)
            geparst = abweichungen_lesen(abweichungen)
            inhaltlich = [a for a in geparst if a["art"] != "formulierung"]
            einstimmig = not inhaltlich
            strittig = [a for a in geparst if a["art"] == "strittig"]
            _abweichungen_merken(sitzung, str(wurzel), modell, geparst,
                                 reihenfolge, aehnlich, fingerabdruck)

    # Der Schiedsspruch wird festgehalten, BEVOR das Kapitel geschrieben wird.
    # Sonst haengt die Beweislage davon ab, dass der nachfolgende Schritt
    # gelingt - und ein abgebrochener Lauf hinterliesse nichts.
    spruch_festhalten({
        "zeit": int(time.time()),
        "lauf": datetime.now().isoformat(timespec="seconds"),
        "sitzung": sitzung,
        "projekt": str(wurzel),
        "modell": modell,
        "protokollfassung": fingerabdruck,
        "protokoll_zeichen": len(protokoll),
        "schreiber_geantwortet": len(fassungen),
        "uebereinstimmung": round(aehnlich, 3) if aehnlich is not None else None,
        "einstimmig": einstimmig,
        "abweichungen": [
            {"art": a["art"], "position": a["wer"],
             "beschreibung": a["beschreibung"]}
            for a in (abweichungen_lesen(abweichungen) if abweichungen else [])
        ],
        "schiedsspruch_text": (abweichungen or "")[:MAX_FASSUNG],
        "fassungen": [f[:MAX_FASSUNG] for f in fassungen],
    })

    if not titel:
        titel = (f"Sitzung "
                 f"{datetime.fromtimestamp(bericht['beginn']).strftime('%d.%m. %H:%M')}")
    datum = datetime.fromtimestamp(bericht.get("beginn") or time.time()).strftime("%Y-%m-%d")

    gegenprobe = chronik_gegenpruefen(sitzung)
    kopf = {
        "sitzung": sitzung, "datum": datum, "projekt": wurzel.name, "titel": titel,
        "aufrufe": bericht.get("aufrufe"),
        "dauer": buch._dauer((bericht.get("ende") or 0) - (bericht.get("beginn") or 0)),
        "fehlschlaege": len(bericht.get("fehlschlaege") or []),
        "dateien": list((bericht.get("dateien") or {}).keys())[:15],
        "modell": modell, "schreiber": len(fassungen),
        "einstimmig": einstimmig,
        "strittig": len(strittig),
        "uebereinstimmung": round(aehnlich, 3) if aehnlich is not None else None,
        "chronik_vollstaendig": gegenprobe.get("ok"),
    }
    ordner = buch.buchordner(wurzel)
    ordner.mkdir(parents=True, exist_ok=True)
    ziel = ordner / buch._dateiname(datum, titel, sitzung)

    zeilen = ["---"]
    for schluessel, wert in kopf.items():
        if isinstance(wert, list):
            zeilen.append(f"{schluessel}: [{', '.join(json.dumps(x, ensure_ascii=False) for x in wert)}]")
        elif isinstance(wert, str):
            zeilen.append(f"{schluessel}: {json.dumps(wert, ensure_ascii=False)}")
        else:
            zeilen.append(f"{schluessel}: {wert}")
    zeilen += ["---", "", f"# {titel}", "", koerper, ""]
    ziel.write_text("\n".join(zeilen), "utf-8")

    # Prüfbericht getrennt ablegen - Rohstoff für den Aufseher
    ordner_pruefung = PRUEFORDNER / sitzung
    ordner_pruefung.mkdir(parents=True, exist_ok=True)
    laufkennung = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    berichtdatei = ordner_pruefung / f"{laufkennung}.md"
    pruefbericht = [
        f"# Prüfung Sitzung {sitzung}", "",
        f"Lauf {laufkennung} · Protokollfassung `{fingerabdruck}`", "",
        f"Projekt: {wurzel.name} · {datum} · Modell {modell}",
        f"Schreiber geantwortet: {len(fassungen)} von 2",
        f"Textübereinstimmung der Fassungen: "
        f"{round(aehnlich*100,1) if aehnlich is not None else '—'} %",
        f"Inhaltlich einstimmig: {einstimmig}", "",
        "## Abweichungen und Schiedsspruch", "", abweichungen or "keine", "",
        "## Gegenprobe der Chronik", "",
        "```", json.dumps(gegenprobe, ensure_ascii=False, indent=1), "```", "",
    ]
    for i, fassung in enumerate(fassungen):
        pruefbericht += [f"## Fassung {chr(65+i)} (unverändert)", "", fassung, ""]
    berichtdatei.write_text("\n".join(pruefbericht), "utf-8")

    chronik.abgeschlossen_merken(sitzung, {
        "kapitel": str(ziel), "titel": titel, "projekt": str(wurzel),
        "geschrieben": int(time.time()), "modell": modell,
        "schreiber": len(fassungen), "einstimmig": einstimmig,
        "uebereinstimmung": aehnlich, "pruefbericht": str(berichtdatei),
        "protokollfassung": fingerabdruck,
        "chronik_vollstaendig": gegenprobe.get("ok"),
    })
    return {"ok": True, "kapitel": str(ziel), "titel": titel,
            "projekt": str(wurzel), "schreiber": len(fassungen),
            "einstimmig": einstimmig, "uebereinstimmung": aehnlich,
            "strittig": len(strittig), "gegenprobe": gegenprobe,
            "pruefbericht": str(berichtdatei),
            "protokollfassung": fingerabdruck}


def _abweichungen_merken(sitzung: str, projekt: str, modell: str,
                         geparst: list[dict], reihenfolge: list[int],
                         aehnlichkeit: float | None,
                         fingerabdruck: str = "") -> None:
    """Strichliste der Abweichungen - Rohstoff für den Aufseher.

    Festgehalten wird auch, welche *Position* der Schiedsrichter bevorzugt hat.
    Wählt er über die Zeit fast immer die erste, ist das Positionsvorliebe und
    nicht Wahrheit.
    """
    ABWEICHUNGEN.parent.mkdir(parents=True, exist_ok=True)
    with ABWEICHUNGEN.open("a", encoding="utf-8") as f:
        for a in geparst:
            f.write(json.dumps({
                "zeit": int(time.time()), "sitzung": sitzung,
                "projekt": projekt, "modell": modell,
                "art": a["art"], "position": a["wer"],
                "beschreibung": a["beschreibung"],
                "protokollfassung": fingerabdruck,
                "aehnlichkeit": round(aehnlichkeit, 3) if aehnlichkeit else None,
            }, ensure_ascii=False) + "\n")


def abweichungen_auswerten(zurueck_tage: int = 120) -> dict:
    """Welche Abweichungsart häuft sich, und bevorzugt der Schiedsrichter eine Position."""
    if not ABWEICHUNGEN.exists():
        return {"gesamt": 0, "arten": {}, "positionen": {}, "hinweise": []}
    grenze = time.time() - zurueck_tage * 86400
    arten: dict[str, int] = {}
    positionen: dict[str, int] = {}
    beispiele: dict[str, list[str]] = {}
    gesamt = 0
    try:
        for zeile in ABWEICHUNGEN.read_text("utf-8").splitlines():
            if not zeile.strip():
                continue
            try:
                e = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if (e.get("zeit") or 0) < grenze:
                continue
            gesamt += 1
            arten[e["art"]] = arten.get(e["art"], 0) + 1
            if e.get("position") in ("ERSTE", "ZWEITE"):
                positionen[e["position"]] = positionen.get(e["position"], 0) + 1
            if e["art"] != "formulierung" and e.get("beschreibung"):
                beispiele.setdefault(e["art"], []).append(e["beschreibung"][:160])
    except OSError:
        return {"gesamt": 0, "arten": {}, "positionen": {}, "hinweise": []}

    # Was konkret korrigiert werden muss, ergibt sich aus der Art
    ZIEL = {
        "erfindung": ("Anweisung des Schreibers", "lk/buch.py: ANWEISUNG - "
                      "Verbot des Erfindens schärfen oder Protokoll anreichern"),
        "auslassung": ("Verdichtung des Protokolls", "lk/chronik.py: "
                       "sitzung_verdichten / lk/buch.py: bericht_text - "
                       "übergangene Stelle deutlicher darstellen"),
        "fehldeutung": ("Felder des Chronisten", "hooks/chronist.sh - "
                        "fehlendes Feld nachrüsten, damit die Stelle eindeutig wird"),
        "strittig": ("Datenlage", "Protokoll deckt die Frage nicht ab - "
                     "entweder zusätzliches Feld erfassen oder offen lassen"),
    }
    hinweise = []
    for art, anzahl in sorted(arten.items(), key=lambda kv: -kv[1]):
        if art == "formulierung" or anzahl < 3:
            continue
        stelle, was = ZIEL.get(art, ("", ""))
        hinweise.append({"art": art, "anzahl": anzahl, "stelle": stelle,
                         "massnahme": was,
                         "beispiele": beispiele.get(art, [])[:3]})

    erste = positionen.get("ERSTE", 0)
    zweite = positionen.get("ZWEITE", 0)
    entschieden = erste + zweite
    schieflage = None
    if entschieden >= 10:
        anteil = erste / entschieden
        if anteil > 0.7 or anteil < 0.3:
            schieflage = {
                "anteil_erste": round(anteil, 3), "entschieden": entschieden,
                "befund": "Der Schiedsrichter bevorzugt eine Position. Die "
                          "Reihenfolge wird zufällig vertauscht, also kann das "
                          "keine Wahrheit sein, sondern Positionsvorliebe."}
    return {"gesamt": gesamt, "arten": arten, "positionen": positionen,
            "hinweise": hinweise, "schieflage": schieflage,
            "nach_fassung": _nach_fassung(zurueck_tage)}


def _nach_fassung(zurueck_tage: int) -> list[dict]:
    """Abweichungen nach Protokollfassung - zeigt, ob eine Aenderung half."""
    if not SPRUCHBUCH.exists():
        return []
    grenze = time.time() - zurueck_tage * 86400
    je_fassung: dict[str, dict] = {}
    try:
        for zeile in SPRUCHBUCH.read_text("utf-8").splitlines():
            if not zeile.strip():
                continue
            try:
                e = json.loads(zeile)
            except json.JSONDecodeError:
                continue
            if (e.get("zeit") or 0) < grenze:
                continue
            f = e.get("protokollfassung") or "?"
            eintrag = je_fassung.setdefault(f, {
                "fassung": f, "laeufe": 0, "arten": {}, "zuerst": e.get("lauf"),
                "zuletzt": e.get("lauf"), "uebereinstimmung": []})
            eintrag["laeufe"] += 1
            eintrag["zuletzt"] = e.get("lauf")
            if e.get("uebereinstimmung") is not None:
                eintrag["uebereinstimmung"].append(e["uebereinstimmung"])
            for a in e.get("abweichungen", []):
                eintrag["arten"][a["art"]] = eintrag["arten"].get(a["art"], 0) + 1
    except OSError:
        return []
    aus = []
    for e in je_fassung.values():
        werte = e.pop("uebereinstimmung")
        e["uebereinstimmung_mittel"] = (round(sum(werte) / len(werte), 3)
                                        if werte else None)
        inhaltlich = sum(n for art, n in e["arten"].items()
                         if art != "formulierung")
        e["inhaltliche_abweichungen_je_lauf"] = round(inhaltlich / e["laeufe"], 2)
        aus.append(e)
    aus.sort(key=lambda e: e["zuerst"] or "")
    return aus


# ------------------------------------------------------------- Zusicherungen


def karte_zusicherungen(wurzel: Path) -> list[dict]:
    """Prüfen, dass der Setzer nichts verloren oder durchgelassen hat."""
    wurzel = wurzel.resolve()
    maengel: list[dict] = []
    karte_md = wurzel / "KARTE.md"
    if not karte_md.exists():
        return [{"schwere": "schwer", "befund": "keine KARTE.md",
                 "ort": str(wurzel)}]
    text = karte_md.read_text("utf-8")

    # 1. jede Falle und jede Regel aus jedem Kapitel muss in der Karte stehen
    for k in buch.kapitel_sammeln(wurzel):
        for art, schluessel in (("Falle", "fallen"), ("Regel", "regeln")):
            for eintrag in k.get(schluessel, []):
                kern = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", eintrag)).strip()
                probe = kern[:60]
                if probe and probe not in re.sub(r"\s+", " ", re.sub(r"[*_`]", "", text)):
                    maengel.append({
                        "schwere": "schwer",
                        "befund": f"{art} aus {k['datei']} fehlt in der KARTE.md",
                        "ort": kern[:110]})

    # 2. jede handgeschriebene Notiz muss in der Karte stehen
    for abschnitt, punkte in notizen.laden(wurzel).items():
        for eintrag in punkte:
            kern = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", eintrag)).strip()[:60]
            if kern and kern not in re.sub(r"\s+", " ", re.sub(r"[*_`]", "", text)):
                maengel.append({
                    "schwere": "schwer",
                    "befund": f"Notiz ({abschnitt}) fehlt in der KARTE.md",
                    "ort": kern[:110]})

    # 3. nichts Geheimes in der Karte, im Buch oder in den Notizen
    zu_pruefen = [karte_md] + list(buch.buchordner(wurzel).glob("*.md"))
    if notizen.pfad(wurzel).exists():
        zu_pruefen.append(notizen.pfad(wurzel))
    for p in zu_pruefen:
        try:
            inhalt = p.read_text("utf-8")
        except OSError:
            continue
        for nummer, zeile in enumerate(inhalt.splitlines(), 1):
            verdacht = geheimnisverdacht(zeile)
            if verdacht:
                maengel.append({
                    "schwere": "schwer",
                    "befund": f"sieht aus wie ein Zugangsdatum in der Ablage "
                              f"({verdacht})",
                    "ort": f"{p.name}:{nummer}"})

    # 4. Karte darf nicht älter sein als die Dateien, die sie beschreibt
    try:
        karte_zeit = karte_md.stat().st_mtime
    except OSError:
        karte_zeit = 0
    neuste = 0.0
    konf = konfig.laden()
    ignorieren = set(konf.get("ignorieren", []))
    for ordner, unter, dateien in os.walk(wurzel):
        unter[:] = [u for u in unter if u not in ignorieren and u != ".landkarte"]
        for name in dateien:
            if name in ("KARTE.md", ".DS_Store"):
                continue
            try:
                neuste = max(neuste, os.stat(os.path.join(ordner, name)).st_mtime)
            except OSError:
                continue
    if neuste > karte_zeit + 3600:
        maengel.append({
            "schwere": "leicht",
            "befund": f"Karte ist {int((neuste-karte_zeit)/3600)} Stunden älter "
                      f"als die jüngste Änderung",
            "ort": "KARTE.md"})
    return maengel


def brainbook_zusicherungen() -> list[dict]:
    """Das Brainbook enthaelt nur Verweise - keine Geheimnisse, keine toten Pfade."""
    from . import brainbook
    maengel: list[dict] = []
    if not brainbook.BUCH.exists():
        return maengel
    try:
        inhalt = brainbook.BUCH.read_text("utf-8")
    except OSError:
        return maengel
    for nummer, zeile in enumerate(inhalt.splitlines(), 1):
        verdacht = geheimnisverdacht(zeile)
        if verdacht:
            maengel.append({"schwere": "schwer",
                            "befund": f"sieht aus wie ein Zugangsdatum "
                                      f"({verdacht})",
                            "ort": f"brainbook.md:{nummer}"})
    for stichwort, eintrag in brainbook.laden().items():
        for regal in eintrag.get("regal", []):
            pfad = regal.get("pfad")
            if pfad and not Path(pfad).is_dir():
                maengel.append({"schwere": "leicht",
                                "befund": f"„{stichwort}\" zeigt auf ein Regal, "
                                          f"das es nicht mehr gibt",
                                "ort": pfad})
        for verweis in eintrag.get("verweise", []):
            ziel = Path(verweis.rstrip("/"))
            if not ziel.exists():
                maengel.append({"schwere": "leicht",
                                "befund": f"Verweis von „{stichwort}\" ist tot",
                                "ort": verweis})
    return maengel


def regal_zusicherungen() -> list[dict]:
    maengel: list[dict] = []
    if not konfig.REGISTER.exists():
        return [{"schwere": "schwer", "befund": "kein Regal gebaut", "ort": "—"}]
    reg = json.loads(konfig.REGISTER.read_text("utf-8"))
    for p in reg.get("projekte", []):
        if not (Path(p["wurzel"]) / "KARTE.md").exists():
            maengel.append({"schwere": "schwer",
                            "befund": "im Regal, aber ohne Karte",
                            "ort": p["name"]})
    for f in reg.get("scanfehler", []):
        maengel.append({"schwere": "schwer", "befund": f["fehler"],
                        "ort": f["projekt"]})
    return maengel


def vollpruefung(projekte: list[Path] | None = None) -> dict:
    """Alle Zusicherungen über alle Projekte, plus Chronik-Gegenprobe."""
    from . import register as reg_modul
    projekte = projekte if projekte is not None else reg_modul.projekte_finden()
    befunde: list[dict] = []
    for wurzel in projekte:
        if not (wurzel / "KARTE.md").exists():
            continue
        for m in karte_zusicherungen(wurzel):
            befunde.append({**m, "projekt": wurzel.name})
    for m in regal_zusicherungen():
        befunde.append({**m, "projekt": "(Regal)"})
    for m in brainbook_zusicherungen():
        befunde.append({**m, "projekt": "(Brainbook)"})

    gegenproben = []
    for sitzung in list(chronik.sitzungen_mit_aktivitaet(7))[:25]:
        ergebnis = chronik_gegenpruefen(sitzung)
        if ergebnis.get("ok") is False:
            gegenproben.append({"sitzung": sitzung, **ergebnis})
    return {"befunde": befunde, "gegenproben": gegenproben,
            "geprueft": int(time.time())}
