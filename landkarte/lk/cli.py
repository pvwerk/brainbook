"""Zweck: Befehlszeile der Landkarte."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from . import aufseher, brainbook, buch, chronik, digest, karte, konfig
from . import freigabe as _freigabe
from . import platzanweiser
from . import mindmap, notizen
from . import korrektur, nachtrag, pruefer, regalwart, register, scan
from . import schwaerzen as _schw
from . import statistik
from . import suche, testleser, vorstellung


_MESSUNG: dict = {}


def messen(**werte) -> None:
    """Zaehlwerte fuer das Selbstprotokoll hinterlegen - niemals Inhalte."""
    _MESSUNG.update(werte)


def projektwurzel(pfad: str | None = None) -> Path:
    """Projektordner bestimmen: Angabe, sonst von hier aufwaerts suchen."""
    start = Path(pfad).expanduser().resolve() if pfad else Path.cwd()
    if start.is_file():
        start = start.parent
    aktuell = start
    while True:
        if aktuell.resolve() not in konfig.NIEMALS_PROJEKT:
            for marker in ("KARTE.md", ".landkarte", ".git", "pyproject.toml",
                           "package.json"):
                if (aktuell / marker).exists():
                    return aktuell
        if aktuell.parent == aktuell or aktuell == konfig.HEIM:
            return start
        aktuell = aktuell.parent


def _kurz(p: Path | str) -> str:
    return str(p).replace(str(konfig.HEIM), "~")


# --------------------------------------------------------------- Einzelbefehle


def befehl_scan(args) -> int:
    wurzel = projektwurzel(args.pfad)
    if not wurzel.is_dir():
        print(f"{_kurz(wurzel)} gibt es nicht.", file=sys.stderr)
        return 2
    beginn = time.time()
    try:
        ergebnis = karte.bauen(wurzel)
    except ValueError as fehler:
        print(str(fehler), file=sys.stderr)
        return 2
    if args.mindmap:
        modell = json.loads((wurzel / ".landkarte" / "karte.json").read_text("utf-8"))
        mindmap.bauen(modell, wurzel / ".landkarte" / "mindmap.html")
    messen(projekt=str(wurzel), dateien=ergebnis["dateien"],
           kapitel=ergebnis["kapitel"], fallen=ergebnis["fallen"])
    print(f"{_kurz(ergebnis['karte'])} — {ergebnis['dateien']} Dateien, "
          f"{ergebnis['kapitel']} Kapitel, {ergebnis['fallen']} Fallen, "
          f"{int((time.time()-beginn)*1000)} ms")
    return 0


def befehl_regal(args) -> int:
    beginn = time.time()
    ergebnis = register.regal_bauen(neu_scannen=not args.ohne_scan)
    messen(projekte=ergebnis["projekte"],
           scanfehler=len(ergebnis["scanfehler"]),
           regalereignisse=len(ergebnis.get("regalereignisse", [])))
    print(f"{ergebnis['projekte']} Projekte · {_kurz(ergebnis['regal'])} · "
          f"{int(time.time()-beginn)} s")
    for e in ergebnis.get("regalereignisse", []):
        print("  " + e.replace("**", ""))
    for f in ergebnis["scanfehler"]:
        print(f"  FEHLER {_kurz(f['projekt'])}: {f['fehler']}", file=sys.stderr)
    return 0


def befehl_digest(args) -> int:
    wurzel = projektwurzel(args.pfad)
    # Beim ersten Mal die Vorstellung voranstellen und das merken.
    voran = ""
    if args.mit_vorstellung and not vorstellung.schon_vorgestellt():
        voran = vorstellung.ANWEISUNG + "\n"
        vorstellung.merken()
    text = digest.bauen(wurzel, grenze=digest.GRENZE - len(voran))
    if not text and not voran:
        return 1
    print(voran + text)
    return 0


def befehl_vorstellen(args) -> int:
    """Erklären, was die Bibliothek kann und wie man eingreift."""
    if args.erneut:
        vorstellung.zuruecksetzen()
        print("Merker gelöscht — beim nächsten Sitzungsstart erklärt es die KI "
              "noch einmal.")
        return 0
    print(vorstellung.ANWEISUNG if args.fuer_ki else vorstellung.TEXT)
    return 0


def _bb_zeile(treffer: int) -> str:
    """Die Signalzeile, die Jan in jeder Antwort sehen will.

    Wortlaut von ihm vorgegeben (09.11.2026): nichts gefunden -> `bb false`,
    sonst `bb true <N> Eintraege`. Die Zahl ist gezaehlt, nicht geschaetzt.
    """
    if treffer <= 0:
        return "bb false"
    return f"bb true {treffer} Einträge"


def befehl_bb(args) -> int:
    """Nachschlagen und das Ergebnis als Signalzeile melden.

    Ein Aufruf statt zwei: die Zeile fuer die Antwort und die Fundstellen.
    """
    if args.bilanz:
        b = platzanweiser.bilanz()
        print(f"bb {b['uses']} uses")
        print(f"   {b['abfragen']} Abfragen, davon {b['ergiebig']} ergiebig "
              f"({b['treffer']} Fundstellen)")
        print(f"   {b['nachgereicht']} Verzeichniseinträge nachgereicht, "
              f"{b['angehalten']} mal angehalten")
        return 0
    if not args.begriff:
        print("Entweder einen Begriff nennen oder --bilanz.", file=sys.stderr)
        return 2
    args.bb = True
    args.grenze = getattr(args, "grenze", 5)
    args.projekt = None
    return befehl_wo(args)


def befehl_finde(args) -> int:
    treffer = suche.finden(args.begriff, projekt=args.projekt)
    platzanweiser.nachgeschlagen_merken("*", treffer=len(treffer))
    messen(treffer=len(treffer), laenge=len(args.begriff))
    if getattr(args, "bb", False):
        print(_bb_zeile(len(treffer)))
        print()
    print(suche.ausgeben(treffer, args.begriff))
    return 0 if treffer else 1


def befehl_notiz(args) -> int:
    wurzel = projektwurzel(args.projekt)
    art = {"falle": "Fallen", "fallen": "Fallen", "regel": "Regeln",
           "regeln": "Regeln", "zugang": "Zugaenge", "zugaenge": "Zugaenge",
           "offen": "Offen"}.get(args.art.lower(), "Fallen")
    ziel = notizen.anhaengen(wurzel, art, args.text)
    print(f"{art} ← {_kurz(ziel)}")
    if (wurzel / "KARTE.md").exists():
        karte.bauen(wurzel)
        print("KARTE.md neu gesetzt")
    return 0


def _kapitel_machen(sitzung: str, args):
    """Einfach oder doppelt, je nach Einstellung."""
    doppelt = (not args.einfach) and konfig.laden().get("schreiber_doppelt", True)
    if doppelt and not args.trocken:
        return pruefer.kapitel_doppelt(sitzung, args.modell)
    return buch.kapitel_schreiben(sitzung, args.modell, trocken=args.trocken)


def _kapitel_melden(ergebnis: dict) -> None:
    zusatz = ""
    if ergebnis.get("schreiber") == 2:
        uebereinstimmung = ergebnis.get("uebereinstimmung")
        if ergebnis.get("einstimmig") is True:
            zusatz = "  [2 Schreiber, einstimmig]"
        elif ergebnis.get("einstimmig") is False:
            zusatz = (f"  [2 Schreiber, Abweichungen bereinigt, "
                      f"{round((uebereinstimmung or 0)*100)} % Textgleichheit]")
        else:
            zusatz = "  [2 Schreiber]"
    elif ergebnis.get("schreiber") == 1:
        zusatz = "  [nur 1 Schreiber - Gegenprobe fehlt]"
    gegen = ergebnis.get("gegenprobe") or {}
    if gegen.get("ok") is False:
        zusatz += (f"  [Chronik unvollständig: {gegen.get('anzahl_fehlen')} "
                   f"Aufrufe fehlen]")
    print(f"  ✓ {ergebnis['titel']} → {_kurz(ergebnis['kapitel'])}{zusatz}")


def befehl_kapitel(args) -> int:
    if args.faellig:
        offen = chronik.kapitel_faellig(min_aufrufe=args.min_aufrufe)
        if not offen:
            print("Kein Kapitel fällig.")
            return 0
        print(f"{len(offen)} Kapitel fällig.")
        for eintrag in offen[: args.grenze]:
            ergebnis = _kapitel_machen(eintrag["sitzung"], args)
            if ergebnis.get("ok") and not args.trocken:
                _kapitel_melden(ergebnis)
                karte.bauen(Path(ergebnis["projekt"]))
            elif args.trocken:
                print(f"  (trocken) {eintrag['sitzung'][:8]} — "
                      f"{ergebnis.get('zeichen')} Zeichen Anfrage")
            else:
                print(f"  ✗ {eintrag['sitzung'][:8]}: {ergebnis.get('grund')}",
                      file=sys.stderr)
        return 0
    if not args.sitzung:
        print("Entweder --sitzung <id> oder --faellig.", file=sys.stderr)
        return 2
    ergebnis = _kapitel_machen(args.sitzung, args)
    if args.trocken:
        print(ergebnis.get("anfrage", ergebnis.get("grund", "")))
        return 0 if ergebnis.get("ok") else 1
    if not ergebnis.get("ok"):
        print(ergebnis.get("grund"), file=sys.stderr)
        return 1
    _kapitel_melden(ergebnis)
    karte.bauen(Path(ergebnis["projekt"]))
    return 0


def befehl_merke(args) -> int:
    """Ein Stichwort von Jan in das Brainbook eintragen."""
    ergebnis = brainbook.merken(
        args.stichwort, ist=args.ist, auch=args.auch, was=args.was or "",
        kategorien=args.kategorie, verweise=args.verweis, notiz=args.notiz)
    neu = ergebnis["neu"]
    print(f"Brainbook: „{ergebnis['stichwort']}“")
    for zeile in brainbook.ausgeben(ergebnis["eintrag"]):
        print(zeile)
    if neu.get("unbekannt"):
        print(f"\n  NICHT gefunden: {', '.join(neu['unbekannt'])}", file=sys.stderr)
        print("  Steht das Regal schon? → landkarte regale", file=sys.stderr)
        return 1
    print(f"\n  {_kurz(brainbook.BUCH)}")
    return 0


def befehl_brainbook(args) -> int:
    if args.begriff:
        treffer = brainbook.nachschlagen(args.begriff)
        platzanweiser.nachgeschlagen_merken("*", treffer=len(treffer))
        if not treffer:
            print(f"„{args.begriff}“ steht nicht im Brainbook.")
            print('Eintragen mit:  landkarte merke "<stichwort>" --ist <projekt>')
            return 1
        for eintrag in treffer:
            for zeile in brainbook.ausgeben(eintrag):
                print(zeile)
            print()
        return 0
    eintraege = brainbook.laden()
    if not eintraege:
        print("Brainbook ist leer.")
        print('Eintragen mit:  landkarte merke "ETM CRM" --ist etm-gutachten')
        return 1
    print(f"Brainbook — {len(eintraege)} Stichworte  "
          f"({_kurz(brainbook.BUCH)})")
    print("steht in keinem Regal und in keiner Liste")
    print()
    for eintrag in eintraege.values():
        for zeile in brainbook.ausgeben(eintrag):
            print(zeile)
        print()
    return 0


def befehl_wo(args) -> int:
    """Dreistufig nachschlagen: Regal, Fach, Inhalt.

    Liste 1 entsteht aus zwei Quellen: dem Namen des Regals und seinem Inhalt.
    Nur ueber den Namen zu gehen wuerde bedeuten, dass man nur findet, wessen
    Regal man schon kennt.
    """
    hier = projektwurzel(None)
    hier_pfad = str(hier.resolve())
    # Dem Platzanweiser sagen, dass nachgeschlagen wurde. `wo` geht ueber alle
    # Regale, darum gilt es fuer alles, was danach kommt.
    # Zuerst das Brainbook: Jans Wort zaehlt mehr als jeder Ordnername.
    aus_brainbook = brainbook.nachschlagen(args.begriff)
    if aus_brainbook:
        print("AUS DEINEM BRAINBOOK")
        for eintrag in aus_brainbook[:3]:
            for zeile in brainbook.ausgeben(eintrag):
                print("  " + zeile)
        print()

    nach_name = regalwart.regal_finden(args.begriff, hier=hier)
    alle_treffer = suche.finden(args.begriff, grenze=400)

    regale = regalwart.laden().get("regale", {})
    regale_vorab = regale
    name_zu_pfad = {e["name"]: pf for pf, e in regale.items()}

    # Inhaltstreffer je Regal zusammenzaehlen
    inhalt: dict[str, list[dict]] = {}
    for tr in alle_treffer:
        pfad = name_zu_pfad.get(tr["projekt"])
        if pfad:
            inhalt.setdefault(pfad, []).append(tr)

    kandidaten: dict[str, dict] = {}
    for r in nach_name:
        kandidaten[r["pfad"]] = {**r, "inhaltstreffer": 0}
    for eintrag in aus_brainbook:
        for regal in eintrag.get("regal", []):
            pfad = regal.get("pfad")
            if not pfad:
                continue
            e = regale_vorab.get(pfad, {})
            vorhanden = kandidaten.get(pfad)
            punkte = eintrag["punkte"]
            if vorhanden:
                vorhanden["punkte"] += punkte
                vorhanden["grund"] = (f"Brainbook: {eintrag['wie']}; "
                                      + vorhanden["grund"])
            else:
                kandidaten[pfad] = {
                    "pfad": pfad, "name": e.get("name", regal.get("name")),
                    "gruppe": e.get("gruppe", ""), "zweck": e.get("zweck", ""),
                    "punkte": punkte, "inhaltstreffer": 0,
                    "grund": f"Brainbook: {eintrag['wie']}",
                    "verwechselbar_mit": [Path(x).name for x in
                                          e.get("verwechselbar_mit", [])],
                    "faecher": e.get("faecher", [])}
    for pfad, treffer in inhalt.items():
        eintrag = regale.get(pfad, {})
        vorhanden = kandidaten.get(pfad)
        beste = max(t["punkte"] for t in treffer)
        punkte = min(beste, 95) + min(len(treffer), 12) * 1.5
        if pfad == hier_pfad or hier_pfad.startswith(pfad + "/"):
            punkte += 25
        if vorhanden:
            vorhanden["punkte"] += punkte / 2
            vorhanden["inhaltstreffer"] = len(treffer)
        else:
            kandidaten[pfad] = {
                "pfad": pfad, "name": eintrag.get("name", Path(pfad).name),
                "gruppe": eintrag.get("gruppe", ""),
                "zweck": eintrag.get("zweck", ""),
                "punkte": punkte, "inhaltstreffer": len(treffer),
                "grund": f"{len(treffer)} Stellen im Inhalt",
                "verwechselbar_mit": [Path(x).name for x in
                                      eintrag.get("verwechselbar_mit", [])],
                "faecher": eintrag.get("faecher", []),
            }

    gereiht = sorted(kandidaten.values(), key=lambda r: -r["punkte"])
    # Dem Platzanweiser sagen, dass nachgeschlagen wurde, mit der Zahl der
    # Fundstellen - daraus entsteht `bb N uses`. `wo` geht ueber alle Regale,
    # darum gilt es fuer alles, was danach kommt.
    platzanweiser.nachgeschlagen_merken("*", treffer=len(alle_treffer))
    if getattr(args, "bb", False):
        print(_bb_zeile(len(alle_treffer)))
        print()
    messen(treffer=len(gereiht), inhaltstreffer=len(alle_treffer),
           aus_brainbook=len(aus_brainbook), laenge=len(args.begriff),
           projekt=hier_pfad)
    print(f'Gesucht: "{args.begriff}"')
    print()
    print("LISTE 1 \u2014 Regal (welches Projekt)")
    if not gereiht:
        print("   kein Regal passt. Steht das Regal schon? \u2192 landkarte regal")
        return 1
    for r in gereiht[: args.grenze]:
        marke = "   \u2190 du arbeitest hier" if r["pfad"] == hier_pfad else ""
        print(f"   [{r['gruppe'] or '?'}] {r['name']}{marke}")
        hinweis = r["grund"]
        if r.get("inhaltstreffer") and "Inhalt" not in hinweis:
            hinweis += f", {r['inhaltstreffer']} Stellen im Inhalt"
        print(f"       {_kurz(r['pfad'])}  ({hinweis})")
        if r["verwechselbar_mit"]:
            print(f"       nicht verwechseln mit: "
                  f"{', '.join(r['verwechselbar_mit'])}")

    ziel = gereiht[0]
    print()
    print(f"LISTE 2 \u2014 Fach in {ziel['name']} (welcher Teil)")
    # Faecher nach Inhaltstreffern ordnen, sonst nach Namen
    fach_treffer: dict[str, int] = {}
    for tr in inhalt.get(ziel["pfad"], []):
        rest = tr["ort"].replace(ziel["pfad"] + "/", "")
        fach = rest.split("/")[0] if "/" in rest else "(Wurzel)"
        fach_treffer[fach] = fach_treffer.get(fach, 0) + 1
    faecher = regalwart.fach_finden(ziel["pfad"], args.begriff)
    faecher.sort(key=lambda f: (-fach_treffer.get(f["name"], 0),
                                -f.get("punkte", 0), -f.get("symbole", 0)))
    if not faecher:
        print("   keine F\u00e4cher verzeichnet")
    for f in faecher[:8]:
        anzahl = fach_treffer.get(f["name"], 0)
        marke = f"  \u2190 {anzahl} Treffer" if anzahl else ""
        beschreibung = f" \u2014 {f['zweck']}" if f.get("zweck") else ""
        print(f"   {f['name']}/  ({f['dateien']} Dateien, "
              f"{f.get('symbole',0)} Symbole){beschreibung}{marke}")

    print()
    print("LISTE 3 \u2014 Inhalt (die genaue Stelle)")
    treffer = inhalt.get(ziel["pfad"]) or alle_treffer
    if not treffer:
        print("   keine Stelle gefunden. Vielleicht Begriff k\u00fcrzer fassen.")
    for tr in treffer[:20]:
        ort = tr["ort"].replace(str(konfig.HEIM), "~")
        print(f"   {tr['art']:<12} {ort}")
        if tr["text"] and tr["text"] not in ort:
            print(f"   {'':<12} {tr['text'][:110]}")
    if len(treffer) > 20:
        print(f"   \u2026 {len(treffer) - 20} weitere")
    return 0


def befehl_regale(args) -> int:
    zustand = regalwart.laden()
    regale = [e for e in zustand.get("regale", {}).values()
              if not e.get("verschwunden")]
    if not regale:
        print("Keine Regale beschriftet. → landkarte regal")
        return 1
    gruppen: dict[str, list[dict]] = {}
    for e in regale:
        gruppen.setdefault(e.get("gruppe") or "Sonstiges", []).append(e)
    for gruppe in sorted(gruppen):
        print(f"{gruppe}")
        for e in sorted(gruppen[gruppe], key=lambda x: x["name"]):
            print(f"   {e['name']:<28} {_kurz(e['pfad'])}")
            if e.get("aliase"):
                print(f"   {'':<28} auch: {', '.join(e['aliase'][:6])}")
            if e.get("verwechselbar_mit"):
                print(f"   {'':<28} ACHTUNG ähnlich: "
                      f"{', '.join(Path(x).name for x in e['verwechselbar_mit'])}")
            if args.faecher:
                for f in e.get("faecher", [])[:10]:
                    print(f"   {'':<28}   {f['name']}/ ({f['dateien']})")
        print()
    if regalwart.JOURNAL.exists() and args.journal:
        print("--- Journal ---")
        print(regalwart.JOURNAL.read_text("utf-8")[-3000:])
    return 0


def befehl_korrigieren(args) -> int:
    wurzel = projektwurzel(args.projekt)
    ziel = korrektur.anlegen(wurzel, args.falsch, args.richtig, args.grund or "")
    print(f"Berichtigung vermerkt → {_kurz(ziel)}")
    if (wurzel / "KARTE.md").exists():
        karte.bauen(wurzel)
        print("KARTE.md neu gesetzt — der falsche Satz ist jetzt durchgestrichen")
    return 0


def befehl_lesung(args) -> int:
    """Testleser: Kapitel lesen, Verzeichnis daran messen, Belegbares richten."""
    if args.bilanz:
        b = testleser.bilanz(args.tage)
        if not b.get("lesungen"):
            print("Noch keine Lesung. → landkarte lesung")
            return 1
        print(f"{b['lesungen']} Lesungen, {b['begriffe']} Suchbegriffe geprüft")
        print(f"  {b['blind']} Begriffe fanden das Kapitel nicht "
              f"({b['geheilt']} davon nachweislich geheilt)")
        if b.get("trefferquote") is not None:
            print(f"  Trefferquote des Verzeichnisses: "
                  f"{round(b['trefferquote']*100)} %")
        if b.get("offene_vorschlaege"):
            print("\n  Offene Vorschläge (nicht selbst ausgeführt):")
            for v in b["offene_vorschlaege"]:
                print(f"    [{v['schwere']}] {v['kapitel']}: {v['befund']}")
        return 0

    anteil = getattr(args, "anteil", None)
    if anteil:
        gesamt = testleser.kapitel_zaehlen()
        wieviel = testleser.anzahl_aus_anteil(anteil)
        print(f"Bibliothek: {gesamt} Kapitel, {round(anteil)} % davon "
              f"= {wieviel} werden rückwärts gelesen.")
        print("")
    ergebnisse = testleser.runde(args.anzahl, args.modell, args.trocken,
                                 anteil=anteil)
    if not ergebnisse:
        print("Keine Kapitel vorhanden. → landkarte kapitel --faellig")
        return 1
    for e in ergebnisse:
        if not e.get("ok"):
            print(f"  ✗ {e.get('grund')}", file=sys.stderr)
            continue
        if e.get("trocken"):
            print(f"  (trocken) Anfrage {e['zeichen']} Zeichen")
            continue
        print(f"gelesen: {Path(e['kapitel']).name}  "
              f"[{Path(e['projekt']).name}]")
        print(f"  Suchbegriffe: {', '.join(e['begriffe'])}")
        gefunden = len(e["begriffe"]) - len(e["blind_vorher"])
        print(f"  Verzeichnis fand {gefunden} von {len(e['begriffe'])}")
        for k in e.get("korrekturen", []):
            print(f"  korrigiert: {k['getan']}")
        for v in e.get("vorschlaege", []):
            print(f"  VORSCHLAG [{v['schwere']}]: {v['befund']}")
        if e.get("vermutetes_projekt"):
            print(f"  Inhalt deutet auf: {e['vermutetes_projekt']} "
                  f"({e.get('begruendung','')})")
    return 0


def befehl_protokoll(args) -> int:
    """Das Spruchbuch des Schiedsrichters lesen."""
    if not pruefer.SPRUCHBUCH.exists():
        print("Noch kein Schiedsspruch protokolliert.")
        return 1
    saetze = []
    for zeile in pruefer.SPRUCHBUCH.read_text("utf-8").splitlines():
        if not zeile.strip():
            continue
        try:
            saetze.append(json.loads(zeile))
        except json.JSONDecodeError:
            continue
    if args.sitzung:
        saetze = [s for s in saetze if s.get("sitzung", "").startswith(args.sitzung)]
    print(f"{len(saetze)} Schiedssprüche in "
          f"{_kurz(pruefer.SPRUCHBUCH)} (nur angehängt, nie überschrieben)")
    print()
    for s in saetze[-args.grenze:]:
        arten = {}
        for a in s.get("abweichungen", []):
            arten[a["art"]] = arten.get(a["art"], 0) + 1
        inhaltlich = sum(n for k, n in arten.items() if k != "formulierung")
        print(f"{s.get('lauf')}  {Path(s.get('projekt','')).name}  "
              f"{s.get('sitzung','')[:8]}")
        print(f"   Protokollfassung {s.get('protokollfassung')} "
              f"({s.get('protokoll_zeichen')} Zeichen) · "
              f"{s.get('schreiber_geantwortet')} Schreiber · "
              f"Textgleichheit {s.get('uebereinstimmung')}")
        print(f"   {inhaltlich} inhaltliche Abweichungen "
              f"{dict(arten) if arten else ''}")
        if args.ausfuehrlich:
            for a in s.get("abweichungen", []):
                print(f"      {a['art']:<12} {a['position']:<6} "
                      f"{a['beschreibung'][:120]}")
        print()

    nach = pruefer._nach_fassung(args.tage)
    if nach:
        print("Entwicklung nach Protokollfassung "
              "(weniger inhaltliche Abweichungen = besseres Protokoll):")
        for f in nach:
            print(f"   {f['fassung']}  {f['laeufe']:>3} Läufe  "
                  f"{f['inhaltliche_abweichungen_je_lauf']:>5} Abw./Lauf  "
                  f"Textgleichheit {f['uebereinstimmung_mittel']}  "
                  f"ab {f['zuerst']}")
    return 0


def befehl_abweichungen(args) -> int:
    ergebnis = pruefer.abweichungen_auswerten(args.tage)
    print(f"{ergebnis['gesamt']} Abweichungen in {args.tage} Tagen")
    for art, anzahl in sorted((ergebnis.get("arten") or {}).items(),
                              key=lambda kv: -kv[1]):
        print(f"  {anzahl:>4}x {art}")
    if ergebnis.get("hinweise"):
        print("\nHäufungen — hier muss korrigiert werden:")
        for h in ergebnis["hinweise"]:
            print(f"  {h['anzahl']}x {h['art']} → {h['stelle']}")
            print(f"     {h['massnahme']}")
    if ergebnis.get("schieflage"):
        s = ergebnis["schieflage"]
        print(f"\n  ACHTUNG Positionsvorliebe: "
              f"{round(s['anteil_erste']*100)} % an die erste Fassung "
              f"({s['entschieden']} Entscheidungen)")
    return 0


def befehl_pruefen(args) -> int:
    if args.sitzung:
        ergebnis = pruefer.chronik_gegenpruefen(args.sitzung)
        print(json.dumps(ergebnis, ensure_ascii=False, indent=1))
        return 0 if ergebnis.get("ok") is not False else 1
    if args.pfad:
        maengel = pruefer.karte_zusicherungen(projektwurzel(args.pfad))
        if not maengel:
            print("Zusicherungen erfüllt.")
            return 0
        for m in maengel:
            print(f"  {m['schwere']:<7} {m['befund']} — {m['ort']}")
        return 1
    ergebnis = pruefer.vollpruefung()
    schwer = [b for b in ergebnis["befunde"] if b["schwere"] == "schwer"]
    leicht = [b for b in ergebnis["befunde"] if b["schwere"] != "schwer"]
    print(f"{len(schwer)} schwere, {len(leicht)} leichte Befunde, "
          f"{len(ergebnis['gegenproben'])} Sitzungen mit lückenhafter Chronik")
    for b in schwer + leicht:
        print(f"  {b['schwere']:<7} [{b['projekt']}] {b['befund']} — {b['ort']}")
    for g in ergebnis["gegenproben"]:
        print(f"  chronik [{g['sitzung'][:8]}] {g['anzahl_fehlen']} von "
              f"{g['transkript']} Aufrufen fehlen — {g.get('fehlende_werkzeuge')}")
    return 1 if (schwer or ergebnis["gegenproben"]) else 0


def befehl_aufsicht(args) -> int:
    ergebnis = aufseher.bericht(mit_modell=not args.ohne_modell, zurueck=args.tage,
                                doppelt=not args.einfach)
    print(f"{_kurz(ergebnis['werkstatt'])} geschrieben")
    if args.zeigen:
        print()
        print(Path(ergebnis["werkstatt"]).read_text("utf-8"))
    return 0


def befehl_mindmap(args) -> int:
    wurzel = projektwurzel(args.pfad)
    if not wurzel.is_dir():
        print(f"{_kurz(wurzel)} gibt es nicht.", file=sys.stderr)
        return 2
    karte_json = wurzel / ".landkarte" / "karte.json"
    if not karte_json.exists():
        karte.bauen(wurzel)
    modell = json.loads(karte_json.read_text("utf-8"))
    ziel = mindmap.bauen(modell, wurzel / ".landkarte" / "mindmap.html")
    print(_kurz(ziel))
    if args.oeffnen:
        subprocess.run(["open", str(ziel)], check=False)
    return 0


def befehl_mermaid(args) -> int:
    wurzel = projektwurzel(args.pfad)
    if not wurzel.is_dir():
        print(f"{_kurz(wurzel)} gibt es nicht.", file=sys.stderr)
        return 2
    karte_json = wurzel / ".landkarte" / "karte.json"
    if not karte_json.exists():
        karte.bauen(wurzel)
    print(mindmap.mermaid(json.loads(karte_json.read_text("utf-8"))))
    return 0


def befehl_symbole(args) -> int:
    ziel = Path(args.datei).expanduser()
    wurzel = projektwurzel(str(ziel.parent))
    if not wurzel.is_dir():
        print(f"{_kurz(wurzel)} gibt es nicht.", file=sys.stderr)
        return 2
    karte_json = wurzel / ".landkarte" / "karte.json"
    if not karte_json.exists():
        try:
            karte.bauen(wurzel)
        except (OSError, ValueError) as fehler:
            print(f"Karte für {_kurz(wurzel)} nicht baubar: {fehler}",
                  file=sys.stderr)
            return 2
    modell = json.loads(karte_json.read_text("utf-8"))
    rel = str(ziel.resolve()).replace(str(wurzel) + "/", "") if ziel.exists() \
        else args.datei
    gefunden = False
    for d in modell["dateien"]:
        if d["pfad"] == rel or d["pfad"].endswith("/" + rel) or rel in d["pfad"]:
            gefunden = True
            print(f"{d['pfad']}  ({d['zeilen']} Zeilen)")
            if d.get("zweck"):
                print(f"  {d['zweck']}")
            for s in d.get("symbole", []):
                print(f"  {s['zeile']:>5}  {s['art']} {s['name']}")
            print()
    return 0 if gefunden else 1


def befehl_zeig(args) -> int:
    wurzel = projektwurzel(args.pfad)
    platzanweiser.nachgeschlagen_merken(str(wurzel.resolve()))
    p = wurzel / "KARTE.md"
    if not p.exists():
        print(f"Keine Karte in {_kurz(wurzel)}. → landkarte scan", file=sys.stderr)
        return 1
    print(p.read_text("utf-8"))
    return 0


def befehl_chronik_eintrag(args) -> int:
    """Rückfall, wenn jq fehlt: Hook-JSON von stdin in die Chronik schreiben."""
    if os.environ.get("LANDKARTE_SCHREIBER"):
        return 0
    try:
        roh = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    eingabe = roh.get("tool_input") or {}
    ziel = (eingabe.get("file_path") or eingabe.get("path")
            or eingabe.get("command") or eingabe.get("pattern") or "")
    eintrag = {
        "t": int(time.time()),
        "s": roh.get("session_id", ""),
        "i": roh.get("tool_use_id", ""),
        "p": roh.get("cwd", ""),
        "w": roh.get("tool_name", ""),
        "d": str(ziel)[:300],
        "ms": roh.get("duration_ms"),
    }
    if roh.get("error"):
        eintrag["f"] = str(roh["error"])[:600]
    chronik.CHRONIK.mkdir(parents=True, exist_ok=True)
    datei = chronik.CHRONIK / (datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    with datei.open("a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    return 0


def befehl_nachtragen(args) -> int:
    ergebnis = nachtrag.nachtragen(args.tage, args.grenze)
    print(f"{ergebnis['protokolle']} Protokolle gelesen, "
          f"{ergebnis['sitzungen']} mit Werkzeugaufrufen")
    print(f"{ergebnis['neu']} Einträge nachgetragen über {ergebnis['tage']} Tage, "
          f"{ergebnis['schon_vorhanden']} waren schon da")
    if ergebnis["neu"]:
        print("Diese Einträge sind mit q=transkript gekennzeichnet und "
              "bestätigen die Gegenprobe des Chronisten nicht.")
    return 0


def befehl_schwaerzen(args) -> int:
    """Zugangsdaten aus bereits geschriebenen Chronikdateien entfernen.

    Die Chronik wird sonst nur angehängt. Hier wird sie ausnahmsweise
    umgeschrieben, weil ein Passwort im Klartext schwerer wiegt als die
    Unveränderlichkeit - die Urfassung geht in den Papierkorb, nicht weg.
    """
    dateien = sorted(chronik.CHRONIK.glob("*.jsonl"))
    if not dateien:
        print("Keine Chronikdateien.")
        return 1
    papierkorb = (konfig.HEIM / ".Papierkorb-Claude" /
                  f"landkarte-chronik-vor-schwaerzung-{date.today().isoformat()}")
    geaendert = 0
    betroffen: list[str] = []
    for datei in dateien:
        zeilen = datei.read_text("utf-8", errors="replace").splitlines()
        neu: list[str] = []
        treffer = 0
        for zeile in zeilen:
            if not zeile.strip():
                continue
            try:
                e = json.loads(zeile)
            except json.JSONDecodeError:
                neu.append(zeile)
                continue
            vorher = (e.get("d") or "") + "\x00" + (e.get("f") or "")
            _schw.eintrag_schwaerzen(e)
            nachher = (e.get("d") or "") + "\x00" + (e.get("f") or "")
            if vorher != nachher:
                treffer += 1
            neu.append(json.dumps(e, ensure_ascii=False))
        if not treffer:
            continue
        betroffen.append(f"{datei.name}: {treffer} Zeilen")
        geaendert += treffer
        if not args.probe:
            papierkorb.mkdir(parents=True, exist_ok=True)
            (papierkorb / datei.name).write_text("\n".join(zeilen) + "\n", "utf-8")
            datei.write_text("\n".join(neu) + "\n", "utf-8")
    if not geaendert:
        print("Keine Zugangsdaten in der Chronik gefunden.")
        return 0
    for b in betroffen:
        print("  " + b)
    if args.probe:
        print(f"{geaendert} Zeilen würden geschwärzt. Ohne --probe ausführen.")
    else:
        print(f"{geaendert} Zeilen geschwärzt. Urfassung in {_kurz(papierkorb)}")
    return 0


def befehl_stats(args) -> int:
    """Selbstprotokoll zeigen oder ausfuehren - zum Verbessern des Werkzeugs."""
    if args.roh:
        zeilen = statistik.rohzeilen(args.monate)
        print(f"# {len(zeilen)} Zeilen Rohprotokoll — jede einzeln pruefbar")
        for z in zeilen:
            print(z)
        return 0
    b = statistik.bericht(args.monate)
    if args.export:
        ziel = Path(args.export).expanduser()
        if ziel.is_dir():
            ziel = ziel / f"brainbook-stats-{statistik.teilnehmer()}-{date.today()}.json"
        statistik.exportieren(ziel, args.monate)
        print(statistik.ausgeben(b))
        print()
        print(f"Ausgeführt nach: {ziel}")
        print("Darin steht: Befehle, Dauern, Fehlschläge, Abstürze, Umgebung.")
        print("Darin steht NICHT: Projektnamen, Pfade, Inhalte, Suchbegriffe.")
        print("Vorher selbst nachsehen:  brainbook stats --roh")
        return 0
    print(statistik.ausgeben(b))
    if b.get("aufrufe"):
        print()
        print("Ausführen:  brainbook stats --export ~/Desktop")
        print("Rohdaten:   brainbook stats --roh")
    return 0


def befehl_status(args) -> int:
    konf = konfig.laden()
    from . import __version__
    print(f"LANDKARTE {__version__}")
    print(f"  Ablage:   {_kurz(konfig.LK_HEIM)}")
    tage = chronik.tage(30)
    zeilen = 0
    for p in tage:
        try:
            zeilen += sum(1 for _ in p.open("r", encoding="utf-8", errors="replace"))
        except OSError:
            pass
    print(f"  Chronik:  {len(tage)} Tage, {zeilen} Einträge (30 Tage)")
    faellig = chronik.kapitel_faellig()
    print(f"  Kapitel:  {len(faellig)} fällig")
    if konfig.REGISTER.exists():
        reg = json.loads(konfig.REGISTER.read_text("utf-8"))
        print(f"  Regal:    {reg['anzahl']} Projekte, gebaut "
              f"{datetime.fromtimestamp(reg['gebaut']).strftime('%Y-%m-%d %H:%M')}")
        veraltet = []
        for p in reg["projekte"]:
            k = Path(p["wurzel"]) / "KARTE.md"
            if not k.exists():
                veraltet.append(p["name"] + " (fehlt)")
        if veraltet:
            print("  fehlend:  " + ", ".join(veraltet[:8]))
    else:
        print("  Regal:    noch nicht gebaut → landkarte regal")
    if aufseher.WERKSTATT.exists():
        print(f"  Werkstatt: {_kurz(aufseher.WERKSTATT)} "
              f"({datetime.fromtimestamp(aufseher.WERKSTATT.stat().st_mtime).strftime('%Y-%m-%d')})")
    hier = projektwurzel(None)
    print(f"\n  hier:     {_kurz(hier)}")
    print(f"  Karte:    {'ja' if (hier/'KARTE.md').exists() else 'nein'}")
    return 0


def befehl_dienst(args) -> int:
    """Nächtlichen Bibliothekar und wöchentlichen Aufseher als launchd-Dienst.

    ~/Library wird nur auf ausdrückliche Anweisung angefasst - deshalb ist das
    ein eigener Befehl und kein Teil von `einrichten`.
    """
    eigen = Path(__file__).resolve().parent.parent
    quelle = eigen / "dienste"
    ziel_ordner = konfig.HEIM / "Library" / "LaunchAgents"

    plists = sorted(quelle.glob("*.plist"))
    if not plists:
        print("Keine Dienstdateien gefunden.", file=sys.stderr)
        return 1

    if args.zeigen:
        for p in plists:
            print(f"--- {p.name}")
            print(p.read_text("utf-8").replace("LANDKARTE", str(eigen))
                  .replace("HEIM", str(konfig.HEIM)))
        print(f"Ziel: {_kurz(ziel_ordner)}")
        print("Einbauen mit:  landkarte dienst --einbauen")
        return 0

    if not args.einbauen and not args.ausbauen:
        print("Was die Dienste tun:")
        print("  de.jan.landkarte.regal     täglich 03:15 — Chronik nachtragen, "
              "alle Projekte scannen, Regal neu sortieren")
        print("  de.jan.landkarte.aufsicht  montags 07:30 — Werkstattbericht "
              "(nutzt ein Sprachmodell, zwei Aufseher plus Schiedsrichter)")
        print()
        print(f"Sie würden nach {_kurz(ziel_ordner)} geschrieben.")
        print("Anzeigen:  landkarte dienst --zeigen")
        print("Einbauen:  landkarte dienst --einbauen")
        return 0

    if not ziel_ordner.is_dir():
        print(f"{ziel_ordner} fehlt.", file=sys.stderr)
        return 1

    for p in plists:
        ziel = ziel_ordner / p.name
        kennung = p.stem
        if args.ausbauen:
            subprocess.run(["launchctl", "unload", str(ziel)], check=False,
                           capture_output=True)
            if ziel.exists():
                papierkorb = konfig.HEIM / ".Papierkorb-Claude" / "landkarte-dienste"
                papierkorb.mkdir(parents=True, exist_ok=True)
                ziel.rename(papierkorb / p.name)
                print(f"ausgebaut: {kennung} (Datei in {_kurz(papierkorb)})")
            continue
        inhalt = (p.read_text("utf-8")
                  .replace("LANDKARTE", str(eigen))
                  .replace("HEIM", str(konfig.HEIM)))
        ziel.write_text(inhalt, "utf-8")
        subprocess.run(["launchctl", "unload", str(ziel)], check=False,
                       capture_output=True)
        ergebnis = subprocess.run(["launchctl", "load", str(ziel)],
                                  capture_output=True, text=True)
        if ergebnis.returncode == 0:
            print(f"eingebaut und geladen: {kennung}")
        else:
            print(f"eingebaut, Laden fehlgeschlagen: {kennung} — "
                  f"{(ergebnis.stderr or '').strip()}", file=sys.stderr)
    return 0


def befehl_einrichten(args) -> int:
    konf = konfig.laden()
    geaendert = False
    if args.teilnehmer:
        konf["teilnehmer"] = args.teilnehmer
        geaendert = True
    if args.ki:
        konf["ki"] = args.ki
        geaendert = True
    if args.statistik_aus:
        konf["statistik"] = False
        geaendert = True
    if args.statistik_an:
        konf["statistik"] = True
        geaendert = True
    if geaendert:
        konfig.schreiben(konf)
        print(f"Teilnehmer: {konf.get('teilnehmer') or '(zufällige Kennung)'} · "
              f"KI: {konf.get('ki')} · Selbstprotokoll: "
              f"{'an' if konf.get('statistik', True) else 'aus'}")

    konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
    chronik.CHRONIK.mkdir(parents=True, exist_ok=True)
    chronik.SITZUNGEN.mkdir(parents=True, exist_ok=True)
    konfig.PROJEKT_CACHE.mkdir(parents=True, exist_ok=True)
    if not konfig.KONFIG_DATEI.exists():
        konfig.schreiben(konfig.STANDARD)
        print(f"Konfiguration angelegt: {_kurz(konfig.KONFIG_DATEI)}")
    else:
        print(f"Konfiguration vorhanden: {_kurz(konfig.KONFIG_DATEI)}")

    eigen = Path(__file__).resolve().parent.parent / "bin" / "landkarte"
    ziel = konfig.HEIM / ".local" / "bin" / "landkarte"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if ziel.is_symlink() or ziel.exists():
        if ziel.resolve() != eigen:
            ziel.unlink()
            ziel.symlink_to(eigen)
            print(f"Verknüpfung erneuert: {_kurz(ziel)} → {_kurz(eigen)}")
        else:
            print(f"Verknüpfung vorhanden: {_kurz(ziel)}")
    else:
        ziel.symlink_to(eigen)
        print(f"Verknüpfung angelegt: {_kurz(ziel)} → {_kurz(eigen)}")
    print("\nNächster Schritt:  landkarte regal")
    return 0


# ------------------------------------------------------------------- Zerleger


def _freigabe_stand() -> int:
    s = _freigabe.stand()
    print(f"Fassung hier          {s['lokal']}")
    if s.get("marke_draussen") is True:  # verbindlich: Markierung im Repository
        print(f"Auf GitHub            v{s['lokal']} ist veroeffentlicht")
    elif s.get("marke_draussen") is False:
        print(f"Auf GitHub            v{s['lokal']} fehlt noch"
              + (f" ({s['marke_fehler']})" if s.get("marke_fehler") else ""))
    if s["veroeffentlicht"]:
        nachlauf = ("" if s["gleich"]
                    else "   (Zwischenspeicher, laeuft ein paar Minuten nach)")
        print(f"Abholer sieht gerade  {s['veroeffentlicht']}{nachlauf}")
    else:
        print(f"Abholer sieht gerade  nicht abrufbar ({s['abruf_fehler']})")
    if s.get("kopie"):
        print("")
        if s.get("rueckstand"):
            print(f"Das ist eine installierte Kopie. Auf GitHub liegt schon "
                  f"{s['neuste']} — aktualisieren mit:")
            print("  claude plugin update landkarte@jan-werkzeuge")
            print("  oder die Einzeldatei neu herunterladen und ausfuehren")
        elif s["gleich"]:
            print("Das ist eine installierte Kopie und auf dem neusten Stand.")
        else:
            print("Das ist eine installierte Kopie; GitHub war nicht erreichbar"
                  + (f" ({s['marke_fehler']})" if s.get("marke_fehler") else "")
                  + ".")
        return 0
    print(f"Letzte Markierung     {s['letzter_tag'] or '(keine)'}")
    if s["tags"]:
        print(f"Markierungen          {', '.join(s['tags'])}")
    offen = s["offene_commits"]
    print(f"Seit der Fassung      {len(offen)} Commit(s)")
    for zeile in offen[:12]:
        print(f"   {zeile}")
    if len(offen) > 12:
        print(f"   ... und {len(offen) - 12} weitere")
    if s["ungeschoben"]:
        print(f"Noch nicht geschoben  {len(s['ungeschoben'])} Commit(s)")
    print("")
    if offen or s["ungeschoben"]:
        print("Naechster Schritt:  landkarte freigabe --neu fehler   (Probe, "
              "aendert nichts)")
    elif s.get("marke_draussen"):
        print("Nichts freizugeben - hier steht genau das, was draussen liegt.")
    else:
        print(f"Fassung {s['lokal']} ist hier fertig, aber noch nicht draussen:"
              " git push origin main --follow-tags")
    return 0


def _freigabe_bericht(bericht: dict) -> None:
    befunde = bericht["befunde"]
    schlecht = [b for b in befunde if not b["ok"]]
    print(f"{len(befunde)} Pruefungen in {bericht['dauer_s']} s, "
          f"{len(schlecht)} Befund(e)")
    print("")
    for b in befunde:
        if b["ok"]:
            marke = "ok     "
        else:
            marke = "FEHLER " if b["hart"] else "Hinweis"
        zeile = f"  {marke} {b['name']}"
        if b["hinweis"]:
            zeile += f" — {b['hinweis']}"
        print(zeile)


def befehl_freigabe(args) -> int:
    """Eine Fassung bewusst freigeben statt blind hochzuladen."""
    if args.pruefen:
        bericht = _freigabe.pruefen()
        _freigabe_bericht(bericht)
        print("")
        print("Bestanden." if bericht["bestanden"]
              else "Nicht bestanden - so wird nicht freigegeben.")
        return 0 if bericht["bestanden"] else 1

    if not args.neu and not args.fassung:
        return _freigabe_stand()

    ergebnis = _freigabe.freigeben(stufe=args.neu, genau=args.fassung,
                                   text=args.text or "", jetzt=args.jetzt,
                                   ohne_pruefung=args.ohne_pruefung)
    if "pruefung" in ergebnis:
        _freigabe_bericht(ergebnis["pruefung"])
        print("")
    if ergebnis.get("fehler"):
        print(f"Abgebrochen: {ergebnis['fehler']}")
        return 1
    print(f"Fassung {ergebnis['alt']} -> {ergebnis['neu']}")
    if ergebnis.get("commits") is not None:
        print(f"{len(ergebnis['commits'])} Commit(s) in dieser Fassung")
    print("")
    for nummer, schritt in enumerate(ergebnis["schritte"], 1):
        print(f"  {nummer}. {schritt}")
    print("")
    if ergebnis.get("probe"):
        marke = f"--fassung {args.fassung}" if args.fassung else f"--neu {args.neu}"
        print("Das war eine Probe - nichts geaendert, nichts hochgeladen.")
        print(f"Wirklich freigeben:  landkarte freigabe {marke} --jetzt")
        return 0
    if ergebnis.get("fertig"):
        print(f"Fassung {ergebnis['neu']} ist veroeffentlicht.")
        print("  Claude Code:  claude plugin update landkarte@jan-werkzeuge")
        print("  Einzeldatei:  neu herunterladen, dann erneut ausfuehren")
    return 0


def befehl_anweisung(args) -> int:
    """Die Regel "zuerst nachschlagen" in die Anweisungsdatei einhaengen."""
    from . import anweisung
    if args.zeigen:
        print(anweisung.block())
        return 0
    konf = konfig.laden()
    ziel = (Path(args.datei).expanduser() if args.datei
            else anweisung.zieldatei(args.ki or konf.get("ki", "")))
    ergebnis = anweisung.einhaengen(ziel, oben=not args.unten)
    print(f"{ergebnis}: {_kurz(ziel)}")
    if ergebnis in ("oben eingesetzt", "ergaenzt", "ersetzt"):
        print("Eine Kopie des vorherigen Stands liegt in "
              f"{_kurz(Path.home() / '.Papierkorb-Claude' / 'landkarte-anweisung')}")
    if ziel.name != "CLAUDE.md":
        print("")
        print("Diese Datei liest keine KI von selbst — leg sie deiner KI vor "
              "oder kopiere den Abschnitt in ihre Anweisungen.")
    return 0


def befehl_wache(args) -> int:
    """Platzanweiser: Stand zeigen, abschalten oder von Hand befragen."""
    konf = konfig.laden()
    if args.aus or args.an:
        konf["wache"] = bool(args.an)
        konfig.schreiben(konf)
        print("Platzanweiser " + ("an" if args.an else "aus")
              + ". Wirkt ab der naechsten Sitzung.")
        return 0
    if args.pfad:
        entscheidung = platzanweiser.pruefen(
            "Read", {"file_path": str(Path(args.pfad).expanduser())})
        if entscheidung.get("stopp"):
            print(entscheidung["grund"])
            return 1
        if entscheidung.get("hinweis"):
            print(entscheidung["hinweis"])
            return 0
        if not konf.get("wache", True):
            print("Platzanweiser ist abgeschaltet (landkarte wache --an).")
        else:
            print("Durchlassen - kein kartografiertes Projekt, oder in dieser "
                  "Sitzung wurde schon nachgeschlagen.")
        return 0
    kennung = platzanweiser.sitzung()
    stand = platzanweiser._laden()["sitzungen"].get(kennung, {})
    print(f"Platzanweiser: {'an' if konf.get('wache', True) else 'aus'}")
    print(f"Sitzung:       {kennung[:16]}")
    nach = stand.get("nachgeschlagen", [])
    print(f"Nachgeschlagen: {', '.join(_kurz(n) for n in nach) or 'noch nicht'}")
    gestoppt = stand.get("gestoppt", [])
    print(f"Angehalten:     {', '.join(_kurz(n) for n in gestoppt) or 'niemand'}")
    print(f"Nachgereicht:   {len(stand.get('gezeigt', []))} Seiten")
    return 0


class _KapitelWuensche:
    """Die Schalter, die _kapitel_machen erwartet - ohne argparse."""

    def __init__(self, modell=None, einfach=False, trocken=False):
        self.modell = modell
        self.einfach = einfach
        self.trocken = trocken


def befehl_aufnehmen(args) -> int:
    """Die Vergangenheit in die Bibliothek aufnehmen und sie danach pruefen.

    Vier Schritte. Die ersten zwei kosten nichts, die letzten zwei rufen ein
    Sprachmodell - darum wird vorher gesagt, wie oft, und ohne --ja gefragt.
    """
    tage = args.tage
    kapitel_grenze = args.kapitel
    anteil = args.anteil

    print("VERGANGENHEIT AUFNEHMEN")
    print("")
    print("1. Chronik nachtragen — was in alten Sitzungsprotokollen steht")
    ergebnis = nachtrag.nachtragen(tage, args.grenze)
    print(f"   {ergebnis['protokolle']} Protokolle, {ergebnis['sitzungen']} mit "
          f"Werkzeugaufrufen, {ergebnis['neu']} Einträge neu "
          f"({ergebnis['schon_vorhanden']} waren schon da)")

    print("")
    print("2. Regal bauen — jedes Projekt kartografieren")
    regal = register.regal_bauen()
    print(f"   {regal['projekte']} Projekte · {_kurz(regal['regal'])}")
    for f in regal.get("scanfehler", [])[:5]:
        print(f"   ! {f.get('projekt') or f.get('ordner')}: {f['fehler'][:90]}")

    offen = chronik.kapitel_faellig(min_aufrufe=args.min_aufrufe)
    # Sitzungen, deren Projektordner es nicht mehr GIBT, ergeben kein Kapitel.
    # Ein Ordner, der nur gerade nicht lesbar ist, bleibt dagegen drin.
    verschwunden = 0
    behalten = []
    for eintrag in offen:
        ordner = eintrag.get("projekt") or eintrag.get("ordner") or ""
        if ordner and register.lesbarkeit(Path(ordner)) == "fehlt":
            verschwunden += 1
            continue
        behalten.append(eintrag)
    offen = behalten
    zu_schreiben = min(len(offen), kapitel_grenze) if kapitel_grenze else 0
    vorhandene = testleser.kapitel_zaehlen()
    zu_lesen = testleser.anzahl_aus_anteil(anteil) if anteil else 0

    print("")
    print("3. Bücher schreiben und 4. rückwärts lesen brauchen ein Sprachmodell")
    print(f"   {len(offen)} Sitzungen wären ein Kapitel wert, davon werden "
          f"{zu_schreiben} geschrieben")
    if verschwunden:
        print(f"   ({verschwunden} übersprungen: Projektordner gibt es nicht "
              f"mehr)")
    print(f"   danach {round(anteil)} % der Bibliothek rückwärts lesen "
          f"(heute {vorhandene} Kapitel → etwa {zu_lesen})" if anteil else
          "   kein Rückwärtslesen (--anteil 0)")
    kosten = zu_schreiben * 3 + zu_lesen
    print(f"   zusammen etwa {kosten} Modellaufrufe "
          f"(je Kapitel zwei Schreiber und ein Schiedsrichter)")
    if not zu_schreiben and not zu_lesen:
        print("")
        print("Nichts weiter zu tun. Die Chronik und das Regal stehen.")
        return 0
    if not args.ja:
        print("")
        if not sys.stdin.isatty():
            # Niemand da, der zustimmen kann - also nicht zustimmen.
            print("Keine Rückfrage möglich (keine Eingabe). Chronik und Regal")
            print("bleiben, sie kosteten nichts.")
            print("Mit Modellaufrufen weitermachen:  landkarte aufnehmen --ja")
            return 0
        try:
            antwort = input("Weiter? [J/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("")
            print("Abgebrochen. Chronik und Regal bleiben.")
            return 0
        if antwort and antwort[0] not in ("j", "y"):
            print("Abgebrochen. Chronik und Regal bleiben, sie kosteten nichts.")
            print("Später weitermachen:  landkarte aufnehmen --ja")
            return 0

    geschrieben = 0
    if zu_schreiben:
        print("")
        print("3. Bücher schreiben")
        wuensche = _KapitelWuensche(modell=args.modell)
        for eintrag in offen[:zu_schreiben]:
            erg = _kapitel_machen(eintrag["sitzung"], wuensche)
            if erg.get("ok"):
                _kapitel_melden(erg)
                karte.bauen(Path(erg["projekt"]))
                geschrieben += 1
            else:
                print(f"   ✗ {eintrag['sitzung'][:8]}: {erg.get('grund')}")

    if not anteil:
        print("")
        print(f"Fertig. {geschrieben} Kapitel geschrieben.")
        return 0

    jetzt_vorhanden = testleser.kapitel_zaehlen()
    wieviel = testleser.anzahl_aus_anteil(anteil)
    print("")
    print(f"4. Testleser — {round(anteil)} % von {jetzt_vorhanden} Kapiteln "
          f"({wieviel}) rückwärts lesen")
    print("   Er kennt die Antwort und sucht die Frage: aus jedem Kapitel")
    print("   entstehen Suchbegriffe, dann wird wirklich nachgeschlagen.")
    ergebnisse = testleser.runde(anteil=anteil, modell=args.modell)
    gelesen = [e for e in ergebnisse if e.get("ok")]
    begriffe = sum(len(e.get("begriffe", [])) for e in gelesen)
    blind = sum(len(e.get("blind_vorher", [])) for e in gelesen)
    korrekturen = sum(len(e.get("korrekturen", [])) for e in gelesen)
    vorschlaege = [v for e in gelesen for v in e.get("vorschlaege", [])]
    for e in gelesen:
        treffer = len(e.get("begriffe", [])) - len(e.get("blind_vorher", []))
        print(f"   {Path(e['kapitel']).name[:44]:<46} "
              f"{treffer}/{len(e.get('begriffe', []))} gefunden")

    print("")
    print("ERGEBNIS")
    print(f"  {geschrieben} Kapitel geschrieben, {len(gelesen)} davon "
          f"rückwärts gelesen")
    if begriffe:
        quote = round((begriffe - blind) / begriffe * 100)
        print(f"  {begriffe} Suchbegriffe geprüft, {blind} liefen ins Leere "
              f"→ Trefferquote {quote} %")
        if quote < 60:
            print("  Unter 60 % — das Verzeichnis findet zu wenig. Der "
                  "Aufseher schlägt dazu Alarm: landkarte aufsicht")
    print(f"  {korrekturen} Stellen selbst berichtigt")
    for v in vorschlaege[:6]:
        print(f"  VORSCHLAG [{v['schwere']}] {v['befund']}")
    print("")
    print("Nachhalten:  landkarte lesung --bilanz")
    return 0


def zerleger() -> argparse.ArgumentParser:
    from . import __version__
    p = argparse.ArgumentParser(
        prog="landkarte",
        description="Inhaltsverzeichnis, Spickzettel, Fallenprotokoll und "
                    "Mindmap für alle Projekte.")
    p.add_argument("--fassung", "--version", action="version",
                   version=__version__, help="Fassungsnummer nennen")
    u = p.add_subparsers(dest="befehl", required=True)

    s = u.add_parser("scan", help="ein Projekt scannen und KARTE.md setzen")
    s.add_argument("pfad", nargs="?")
    s.add_argument("--mindmap", action="store_true", help="Mindmap mitbauen")
    s.set_defaults(fn=befehl_scan)

    s = u.add_parser("regal", aliases=["alle"], help="alle Projekte, Regal bauen")
    s.add_argument("--ohne-scan", action="store_true",
                   help="nur neu sortieren, nicht neu scannen")
    s.set_defaults(fn=befehl_regal)

    s = u.add_parser("digest", help="kompakter Auszug (für den Hook)")
    s.add_argument("pfad", nargs="?")
    s.add_argument("--mit-vorstellung", action="store_true",
                   dest="mit_vorstellung",
                   help="beim ersten Mal die Vorstellung voranstellen")
    s.set_defaults(fn=befehl_digest)

    s = u.add_parser("vorstellen", aliases=["erklaer"],
                     help="erklären, was die Bibliothek kann und wie man eingreift")
    s.add_argument("--fuer-ki", action="store_true", dest="fuer_ki",
                   help="die Fassung, die der Hook einer KI vorlegt")
    s.add_argument("--erneut", action="store_true",
                   help="Merker löschen, damit es noch einmal erklärt wird")
    s.set_defaults(fn=befehl_vorstellen)

    s = u.add_parser("finde", aliases=["such"], help="über alle Projekte suchen")
    s.add_argument("begriff")
    s.add_argument("--projekt")
    s.set_defaults(fn=befehl_finde)

    s = u.add_parser("notiz", help="Falle, Regel, Zugang oder offenen Punkt festhalten")
    s.add_argument("text")
    s.add_argument("--art", default="falle",
                   help="falle (Standard), regel, zugang, offen")
    s.add_argument("--projekt", help="Projektordner, Standard: hier")
    s.set_defaults(fn=befehl_notiz)

    s = u.add_parser("kapitel", help="Sitzung zu einem Buchkapitel verarbeiten")
    s.add_argument("--sitzung")
    s.add_argument("--faellig", action="store_true")
    s.add_argument("--modell")
    s.add_argument("--trocken", action="store_true", help="nur die Anfrage zeigen")
    s.add_argument("--grenze", type=int, default=5)
    s.add_argument("--min-aufrufe", type=int, default=8, dest="min_aufrufe")
    s.add_argument("--einfach", action="store_true",
                   help="nur ein Schreiber statt Zwillingen")
    s.set_defaults(fn=befehl_kapitel)

    s = u.add_parser("merke", aliases=["brainbook-merke"],
                     help="Stichwort, Kosename oder Synonym ins Brainbook")
    s.add_argument("stichwort", help='wie DU es sagst, z.B. "ETM CRM"')
    s.add_argument("--ist", action="append", default=[],
                   help="Projekt oder Pfad, mehrfach moeglich")
    s.add_argument("--auch", action="append", default=[],
                   help="weiteres Synonym")
    s.add_argument("--was", help="ein Satz: was ist das")
    s.add_argument("--kategorie", action="append", default=[])
    s.add_argument("--verweis", action="append", default=[])
    s.add_argument("--notiz", action="append", default=[])
    s.set_defaults(fn=befehl_merke)

    s = u.add_parser("brainbook", aliases=["tresen"],
                     help="dein Brainbook zeigen oder nachschlagen")
    s.add_argument("begriff", nargs="?")
    s.set_defaults(fn=befehl_brainbook)

    s = u.add_parser("wo", help="dreistufig nachschlagen: Regal, Fach, Inhalt")
    s.add_argument("begriff")
    s.add_argument("--grenze", type=int, default=5)
    s.set_defaults(fn=befehl_wo)

    s = u.add_parser("regale", help="Regalbeschriftung: Gruppen, Aliase, Fächer")
    s.add_argument("--faecher", action="store_true")
    s.add_argument("--journal", action="store_true")
    s.set_defaults(fn=befehl_regale)

    s = u.add_parser("korrigieren", aliases=["berichtigen"],
                     help="falsches Wissen richtigstellen, Original bleibt")
    s.add_argument("falsch", help="der falsche Satz (Teil genügt)")
    s.add_argument("richtig", help="wie es richtig ist")
    s.add_argument("--grund")
    s.add_argument("--projekt")
    s.set_defaults(fn=befehl_korrigieren)

    s = u.add_parser("lesung", aliases=["testleser"],
                     help="Kapitel stichprobenartig lesen und das "
                          "Verzeichnis daran messen")
    s.add_argument("--anzahl", type=int, default=1)
    s.add_argument("--anteil", type=float,
                   help="Anteil der Bibliothek in Prozent, z.B. 20")
    s.add_argument("--modell")
    s.add_argument("--trocken", action="store_true")
    s.add_argument("--bilanz", action="store_true",
                   help="gemessene Trefferquote des Verzeichnisses")
    s.add_argument("--tage", type=int, default=120)
    s.set_defaults(fn=befehl_lesung)

    s = u.add_parser("protokoll",
                     help="Spruchbuch des Schiedsrichters lesen")
    s.add_argument("--sitzung")
    s.add_argument("--grenze", type=int, default=10)
    s.add_argument("--tage", type=int, default=365)
    s.add_argument("--ausfuehrlich", action="store_true")
    s.set_defaults(fn=befehl_protokoll)

    s = u.add_parser("abweichungen", help="Strichliste der Schreiber-Abweichungen")
    s.add_argument("--tage", type=int, default=120)
    s.set_defaults(fn=befehl_abweichungen)

    s = u.add_parser("pruefen", help="Zusicherungen und Chronik-Gegenprobe")
    s.add_argument("pfad", nargs="?", help="nur dieses Projekt")
    s.add_argument("--sitzung", help="nur die Gegenprobe dieser Sitzung")
    s.set_defaults(fn=befehl_pruefen)

    s = u.add_parser("aufsicht", help="Zustand der Bibliothek prüfen")
    s.add_argument("--ohne-modell", action="store_true", dest="ohne_modell")
    s.add_argument("--tage", type=int, default=30)
    s.add_argument("--zeigen", action="store_true")
    s.add_argument("--einfach", action="store_true",
                   help="nur ein Aufseher statt Zwillingen")
    s.set_defaults(fn=befehl_aufsicht)

    s = u.add_parser("mindmap", help="HTML-Mindmap bauen")
    s.add_argument("pfad", nargs="?")
    s.add_argument("--oeffnen", action="store_true")
    s.set_defaults(fn=befehl_mindmap)

    s = u.add_parser("mermaid", help="Graph als Mermaid-Text")
    s.add_argument("pfad", nargs="?")
    s.set_defaults(fn=befehl_mermaid)

    s = u.add_parser("symbole", help="Symbole einer Datei")
    s.add_argument("datei")
    s.set_defaults(fn=befehl_symbole)

    s = u.add_parser("zeig", help="KARTE.md ausgeben")
    s.add_argument("pfad", nargs="?")
    s.set_defaults(fn=befehl_zeig)

    s = u.add_parser("chronik-eintrag", help="Hook-Rückfall ohne jq")
    s.set_defaults(fn=befehl_chronik_eintrag)

    s = u.add_parser("schwaerzen",
                     help="Zugangsdaten aus bestehenden Chronikdateien entfernen")
    s.add_argument("--probe", action="store_true", help="nur zeigen")
    s.set_defaults(fn=befehl_schwaerzen)

    s = u.add_parser("nachtragen",
                     help="Chronik rückwirkend aus Sitzungsprotokollen füllen")
    s.add_argument("--tage", type=int, default=365)
    s.add_argument("--grenze", type=int, help="nur die neuesten N Protokolle")
    s.set_defaults(fn=befehl_nachtragen)

    s = u.add_parser("stats", aliases=["statistik"],
                     help="Selbstprotokoll des Werkzeugs zeigen oder ausführen")
    s.add_argument("--export", nargs="?", const="~/Desktop",
                   help="als JSON ausführen (Standard: ~/Desktop)")
    s.add_argument("--roh", action="store_true", help="jede Rohzeile zeigen")
    s.add_argument("--monate", type=int, default=12)
    s.set_defaults(fn=befehl_stats)

    s = u.add_parser("status", help="Überblick")
    s.set_defaults(fn=befehl_status)

    s = u.add_parser("dienst",
                     help="nächtlicher Bibliothekar und wöchentlicher Aufseher")
    s.add_argument("--zeigen", action="store_true")
    s.add_argument("--einbauen", action="store_true")
    s.add_argument("--ausbauen", action="store_true")
    s.set_defaults(fn=befehl_dienst)

    s = u.add_parser("aufnehmen", aliases=["vergangenheit"],
                     help="die Vergangenheit in die Bibliothek aufnehmen und "
                          "sie danach rueckwaerts pruefen")
    s.add_argument("--tage", type=int, default=365)
    s.add_argument("--grenze", type=int,
                   help="nur die neuesten N Sitzungsprotokolle lesen")
    s.add_argument("--kapitel", type=int, default=10,
                   help="hoechstens so viele Kapitel schreiben (0 = keine)")
    s.add_argument("--anteil", type=float, default=20.0,
                   help="Anteil der Bibliothek, den der Testleser danach "
                        "rueckwaerts liest (Prozent, 0 = gar nicht)")
    s.add_argument("--min-aufrufe", type=int, default=8, dest="min_aufrufe")
    s.add_argument("--modell")
    s.add_argument("--ja", action="store_true",
                   help="nicht nachfragen, auch nicht vor Modellaufrufen")
    s.set_defaults(fn=befehl_aufnehmen)

    s = u.add_parser("bb", aliases=["signal"],
                     help="nachschlagen und als Signalzeile melden "
                          "(bb true N Eintraege / bb false)")
    s.add_argument("begriff", nargs="?")
    s.add_argument("--bilanz", action="store_true",
                   help="Bilanz der Sitzung: bb N uses")
    s.add_argument("--grenze", type=int, default=5)
    s.set_defaults(fn=befehl_bb)

    s = u.add_parser("anweisung", aliases=["regel"],
                     help="die Regel \"zuerst nachschlagen\" in die "
                          "Anweisungsdatei einhaengen")
    s.add_argument("--datei", help="Zieldatei, Standard richtet sich nach der KI")
    s.add_argument("--ki", help="claude-code, codex oder etwas anderes")
    s.add_argument("--unten", action="store_true",
                   help="ans Ende haengen statt nach oben")
    s.add_argument("--zeigen", action="store_true", help="nur den Text ausgeben")
    s.set_defaults(fn=befehl_anweisung)

    s = u.add_parser("wache", aliases=["platzanweiser"],
                     help="Platzanweiser: Stand, abschalten, von Hand pruefen")
    s.add_argument("pfad", nargs="?", help="eine Datei zur Probe vorlegen")
    s.add_argument("--aus", action="store_true")
    s.add_argument("--an", action="store_true")
    s.set_defaults(fn=befehl_wache)

    s = u.add_parser("freigabe", aliases=["freigeben"],
                     help="Stand gegen GitHub zeigen oder eine Fassung freigeben")
    s.add_argument("--pruefen", action="store_true",
                   help="nur pruefen, nichts aendern")
    s.add_argument("--neu", choices=["fehler", "klein", "gross"],
                   help="Fassung erhoehen: fehler 1.1.1, klein 1.2.0, gross 2.0.0")
    s.add_argument("--fassung", help="genaue Fassung setzen, z.B. 1.4.0")
    s.add_argument("--text", help="ein Satz fuer AENDERUNGEN.md und den Commit")
    s.add_argument("--jetzt", action="store_true",
                   help="wirklich stempeln, einchecken und hochladen")
    s.add_argument("--ohne-pruefung", action="store_true",
                   dest="ohne_pruefung",
                   help="Notausgang: Pruefungen ueberspringen")
    s.set_defaults(fn=befehl_freigabe)

    s = u.add_parser("einrichten", help="Ablage anlegen und verknüpfen")
    s.add_argument("--teilnehmer", help="dein Name für das Protokoll, z.B. andre")
    s.add_argument("--ki", help="welche KI benutzt du: claude-code, chatgpt, "
                               "grok, codex, keine")
    s.add_argument("--statistik-aus", action="store_true", dest="statistik_aus",
                   help="Selbstprotokoll abschalten")
    s.add_argument("--statistik-an", action="store_true", dest="statistik_an")
    s.set_defaults(fn=befehl_einrichten)
    return p


def main(argv: list[str] | None = None) -> int:
    rohargumente = list(argv if argv is not None else sys.argv[1:])
    beginn = time.time()
    args = zerleger().parse_args(argv)
    flaggen = [a.split("=")[0] for a in rohargumente if a.startswith("-")]
    befehl = getattr(args, "befehl", "?")

    def dauer() -> int:
        return int((time.time() - beginn) * 1000)

    try:
        code = args.fn(args) or 0
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        statistik.festhalten(befehl, flaggen, 130, dauer())
        return 130
    except Exception:
        statistik.absturz_festhalten(befehl, flaggen, dauer())
        raise
    projekt = _MESSUNG.pop("projekt", "")
    statistik.festhalten(befehl, flaggen, code, dauer(),
                         ergebnis=dict(_MESSUNG), projekt=projekt)
    return code
