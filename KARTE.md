# Landkarte: werkzeuge

> Eigene Claude-Code-Erweiterungen

Stand **2026-11-08 22:23** · 29 Dateien · 5899 Zeilen

`/Users/gustafbot/Projekte/werkzeuge`

<!-- Diese Datei wird von `landkarte` erzeugt. Handschriftliches gehört in .landkarte/notizen.md, das bleibt beim Neubau erhalten. -->

## Spickzettel

## Fallen

_Noch keine erfasst._

## Regeln

_Noch keine._

## Wo liegt was

**Wurzel**

- `README.md` — Werkzeuge  _[3 Verweise]_

**`landkarte/`** — 1 Dateien, 128 Zeilen

- `README.md` — Landkarte  _[3 Verweise]_

**`landkarte/bin/`** — 1 Dateien, 0 Zeilen

- `landkarte`  _[23 Verweise]_

**`landkarte/dienste/`** — 2 Dateien, 49 Zeilen

- `de.jan.landkarte.aufsicht.plist`
- `de.jan.landkarte.regal.plist`

**`landkarte/hooks/`** — 4 Dateien, 149 Zeilen

- `chronist.sh` — Der Chronist. Haengt einen Werkzeugaufruf an die Tageschronik an
- `hooks.json`  _[4 Verweise]_
- `sitzungsende.sh` — Stoesst am Sitzungsende den Schreiber an - vollstaendig abgekoppelt
- `sitzungsstart.sh` — Legt beim Sitzungsstart den Auszug der Landkarte in den Kontext

**`landkarte/lk/`** — 19 Dateien, 5453 Zeilen

- `__init__.py` — Landkarte - Inhaltsverzeichnis, Spickzettel, Fallenprotokoll, Mindmap
- `aufseher.py` — Der Aufseher - erkennt Muster, findet wo die Kette hakt, schlägt vor
- `buch.py` — Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen  _[8 Verweise]_
- `chronik.py` — Rohprotokoll aller Werkzeugaufrufe lesen, auswerten, verdichten  _[10 Verweise]_
- `cli.py` — Befehlszeile der Landkarte  _[Einstieg]_
- `digest.py` — Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt  _[3 Verweise]_
- `karte.py` — Der Setzer - aus Scan, Buch und Notizen die KARTE.md bauen  _[4 Verweise]_
- `konfig.py` — Einstellungen und Pfade der Landkarte, plus Projekterkennung  _[11 Verweise]_
- `korrektur.py` — Falsches Wissen richtigstellen, ohne das Original zu löschen  _[3 Verweise]_
- `mindmap.py` — Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver  _[3 Verweise]_
- `nachtrag.py` — Chronik rückwirkend aus den Sitzungsprotokollen von Claude Code füllen
- `notizen.py` — Handgepflegte Notizen eines Projekts - werden nie überschrieben  _[5 Verweise]_
- `pruefer.py` — Die Absicherung - Gegenprobe, Zwillinge, Schiedsspruch, Zusicherungen
- `regalwart.py` — Der Regalwart - beschriftet und sortiert die Regale, erkennt neue  _[3 Verweise]_
- `register.py` — Der Bibliothekar - Projekte finden, nach Nutzung sortieren, Regal schreiben  _[3 Verweise]_
- `scan.py` — Ein Projekt einlesen und als Datenmodell zurueckgeben  _[6 Verweise]_
- `schwaerzen.py` — Zugangsdaten aus Protokolltexten entfernen, bevor sie irgendwo landen  _[4 Verweise]_
- `sprachen.py` — Symbole, Zweckzeile, Markierungen und Verweise aus einer Datei ziehen
- `suche.py` — In Sekunden finden - Symbole, Dateien, Fallen, Kapitel, alle Projekte

**`landkarte/skills/landkarte/`** — 1 Dateien, 101 Zeilen

- `SKILL.md` — name: landkarte

## Symbole der wichtigsten Dateien

Python exakt über den Syntaxbaum; andere Sprachen über Textregeln, also oberste Ebene zuverlässig, Verschachteltes nicht. Vollständig in `.landkarte/symbole.md`.

### `landkarte/lk/konfig.py`
_Einstellungen und Pfade der Landkarte, plus Projekterkennung_

```
    9  konstante HEIM
   10  konstante LK_HEIM
   11  konstante REGISTER
   12  konstante PROJEKT_CACHE
   13  konstante KONFIG_DATEI
   15  konstante STANDARD
   42  konstante TEXT_ENDUNGEN
   52  konstante TEXT_NAMEN
   59  konstante MAX_DATEI
   60  konstante MAX_DATEIEN
   61  konstante MAX_EDGES_JE_DATEI
   64  konstante NIEMALS_PROJEKT
   73  konstante PUNKTORDNER_ERLAUBT
   76  konstante CLAUDE_ERLAUBT
   79  konstante PROJEKT_MARKER
   86  def laden()   # Konfiguration lesen, fehlende Schluessel aus STANDARD ergaenzen.
   99  def schreiben(konf)
  104  def ausklappen(pfad)
  108  def ist_text(p)
  114  def ist_projekt(ordner)
  132  def slug(pfad)
```

### `landkarte/lk/chronik.py`
_Rohprotokoll aller Werkzeugaufrufe lesen, auswerten, verdichten_

```
   19  konstante CHRONIK
   20  konstante SITZUNGEN
   22  konstante DATEI_WERKZEUGE
   26  konstante SCHREIB_WERKZEUGE
   31  def _projektwurzeln()   # Bekannte Projektwurzeln, laengste zuerst - zum Zuordnen von cwd.
   53  def projektschluessel(ordner)   # Unterordner auf die Projektwurzel zurechnen.
   67  def tage(zurueck)
   81  def eintraege(zurueck, sitzung, projekt)   # Chronik-Eintraege als Generator.
  107  def _dateiziel(e)
  119  def nutzung(zurueck)   # Wie oft wurde welches Projekt und welche Datei angefasst.
  145  def sitzung_verdichten(sitzung)   # Rohprotokoll einer Sitzung zu einem kompakten Bericht eindicken.
  205  def sitzungen_mit_aktivitaet(zurueck)   # Je Sitzung: Anzahl Aufrufe, Fehler, Hauptprojekt, letzte Aktivitaet.
  226  def kapitel_faellig(zurueck, min_aufrufe)   # Sitzungen, die ein Kapitel verdienen und noch keins haben.
  246  def abgeschlossen_merken(sitzung, inhalt)
```

### `landkarte/lk/buch.py`
_Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen_

```
   24  konstante STANDARD_MODELL
   26  konstante ANWEISUNG
   65  def _dauer(sek)
   74  def bericht_text(bericht)   # Den verdichteten Bericht als Text fuer das Modell.
  128  def _gescheitert(datei, fehler_je_datei)
  135  def _claude_rufen(anfrage, modell)
  163  def _titel_trennen(rohtext)
  178  def _dateiname(datum, titel, sitzung)
  186  def buchordner(projekt_wurzel)
  190  def kapitel_schreiben(sitzung, modell, trocken)   # Ein Kapitel fuer eine Sitzung erzeugen und ablegen.
  256  konstante KOPF_MUSTER
  259  def kapitel_lesen(pfad)   # Ein Kapitel in Kopfdaten und Abschnitte zerlegen.
  297  def _punkte(zeilen)
  308  def kapitel_sammeln(projekt_wurzel)
```

### `landkarte/lk/scan.py`
_Ein Projekt einlesen und als Datenmodell zurueckgeben_

```
   15  konstante URL_MUSTER
   18  konstante TOKEN_MUSTER
   19  konstante MAX_TOKEN
   20  konstante IP_MUSTER
   21  konstante SSH_MUSTER
   22  konstante URL_MUELL
   26  konstante BEFEHL_ANFANG
   34  def _lesen(p)
   52  def _git_stand(wurzel)
   71  def _git_ignoriert(wurzel)   # Pfade, die Git ignoriert - also Erzeugnisse, keine Quellen.
   97  def _eigene_ignorierliste(wurzel)   # Zusaetzliche Ausnahmen, die nur dieses Projekt kennt.
  109  def _dateien_sammeln(wurzel, ignorieren, ausnahmen)   # Dateien in Breitensuche sammeln: flach vor tief.
  157  def _befehle_sammeln(wurzel, dateien)
  248  def _adressen_sammeln(wurzel, dateien)
  274  def _graph_bauen(dateien, wurzel)   # Verweise zwischen Dateien des Projekts.
  322  konstante EINSTIEG_NAMEN
  329  def projekt_scannen(wurzel, konf)   # Vollstaendiges Datenmodell eines Projekts.
```

### `landkarte/lk/notizen.py`
_Handgepflegte Notizen eines Projekts - werden nie überschrieben_

```
    8  konstante VORLAGE
   33  konstante ABSCHNITTE
   36  def pfad(wurzel)
   40  def anlegen_wenn_fehlt(wurzel)
   48  def laden(wurzel)
   71  def anhaengen(wurzel, abschnitt, text)   # Einen Punkt in einen Abschnitt schreiben, Abschnitt notfalls anlegen.
```

### `landkarte/lk/cli.py`
_Befehlszeile der Landkarte_

```
   20  def projektwurzel(pfad)   # Projektordner bestimmen: Angabe, sonst von hier aufwaerts suchen.
   37  def _kurz(p)
   44  def befehl_scan(args)
   57  def befehl_regal(args)
   69  def befehl_digest(args)
   78  def befehl_finde(args)
   84  def befehl_notiz(args)
   97  def _kapitel_machen(sitzung, args)   # Einfach oder doppelt, je nach Einstellung.
  105  def _kapitel_melden(ergebnis)
  125  def befehl_kapitel(args)
  159  def befehl_wo(args)   # Dreistufig nachschlagen: Regal, Fach, Inhalt.
  261  def befehl_regale(args)
  290  def befehl_korrigieren(args)
  300  def befehl_protokoll(args)   # Das Spruchbuch des Schiedsrichters lesen.
  349  def befehl_abweichungen(args)
  368  def befehl_pruefen(args)
  394  def befehl_aufsicht(args)
  404  def befehl_mindmap(args)
  417  def befehl_mermaid(args)
  426  def befehl_symbole(args)
  448  def befehl_zeig(args)
  458  def befehl_chronik_eintrag(args)   # Rückfall, wenn jq fehlt: Hook-JSON von stdin in die Chronik schreiben.
       ... 7 weitere
```

### `landkarte/lk/karte.py`
_Der Setzer - aus Scan, Buch und Notizen die KARTE.md bauen_

```
   12  konstante SPITZE_DATEIEN
   13  konstante MAX_SYMBOLE
   16  def _pruefmarke(kopf)   # Zeigt in der Karte, wie gut ein Kapitel abgesichert ist.
   34  def _zeit(stempel)
   38  def _tabelle(zeilen, kopf)
   49  def _baum(dateien, nutzung_dateien)   # Ordnerbaum mit Zweck je Datei, nach Ordnern gruppiert.
   88  def _symbole(dateien, nutzung_dateien)
  112  def _symboldatei_schreiben(modell, wurzel)   # Vollstaendige Symbolliste getrennt ablegen, damit KARTE.md lesbar blei
  134  def bauen(wurzel, modell, nutzungsdaten)   # KARTE.md, .landkarte/karte.json und .landkarte/symbole.md schreiben.
```

### `landkarte/lk/schwaerzen.py`
_Zugangsdaten aus Protokolltexten entfernen, bevor sie irgendwo landen_

```
   16  konstante ERSATZ
   61  def schwaerzen(text)   # Alle erkannten Zugangsdaten durch *** ersetzen - beide Linien.
   71  def eintrag_schwaerzen(eintrag)   # Die Textfelder eines Chronik-Eintrags schwaerzen.
   91  konstante _QUELLEN
   97  konstante _MIN_LAENGE
  100  def _aus_text_ziehen(text)   # Werte, die unsere eigenen Muster als Geheimnis erkennen.
  127  def bekannte_geheimnisse(neu_laden)
  151  def woertlich_schwaerzen(text)
```

### `landkarte/lk/regalwart.py`
_Der Regalwart - beschriftet und sortiert die Regale, erkennt neue_

```
   28  konstante REGALE
   29  konstante JOURNAL
   32  konstante FUELLWOERTER
   36  konstante UMSCHRIFT
   45  def _normal(text)   # Vergleichsform. Umlaute werden umgeschrieben, nicht verworfen -
   51  def _wortteile(name)
   57  def aliase_bilden(wurzel, modell, handgesetzt)   # Namen, unter denen ein Projekt gemeint sein kann.
   86  def gruppe_bestimmen(wurzel, konf)
  100  def _aehnlich(a, b)
  104  def verwechslungsgefahr(regale)   # Projektpaare, die man verwechseln kann - nach Name und nach Aliasen.
  119  def faecher_bilden(modell)   # Liste 2: die Teile eines Projekts - oberste Ordnerebene mit Zweck.
  154  def laden()
  163  def pflegen(modelle)   # Regale beschriften, neue aufbauen, verschwundene vermerken.
  254  def regal_finden(begriff, hier)   # Liste 1: welches Projekt ist gemeint.
  298  def fach_finden(pfad, begriff)   # Liste 2: welcher Teil des Projekts.
```

### `landkarte/lk/korrektur.py`
_Falsches Wissen richtigstellen, ohne das Original zu löschen_

```
   17  konstante DATEI
   20  def pfad(wurzel)
   24  def _kern(text)   # Vergleichsform: ohne Auszeichnung, ohne Datumsanhang, zusammengezogen.
   31  def anlegen(wurzel, falsch, richtig, grund)
   47  def laden(wurzel)
   66  def anwenden(eintraege, korrekturen, fuer_auszug)   # Falsche Einträge markieren oder (für den Auszug) ersetzen.
```

### `landkarte/lk/register.py`
_Der Bibliothekar - Projekte finden, nach Nutzung sortieren, Regal schreiben_

```
   19  def projekte_finden(konf)
   62  def rang_berechnen(wurzel, nutz, modell_knapp)   # Platz im Regal: Nutzungshäufigkeit, Aktualität, Größe.
   81  def regal_bauen(neu_scannen, nur)   # Alle Projekte scannen und das Regal (LANDKARTE.md) schreiben.
  147  def _regal_text(eintraege, scanfehler)
```

### `README.md`
_Werkzeuge_

```
    1  ueberschrift1 Werkzeuge
    6  ueberschrift2 Enthalten
   11  ueberschrift2 Einrichten
```

### `landkarte/lk/digest.py`
_Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt_

```
   16  konstante GRENZE
   19  def _kuerzen(zeilen, grenze)
   35  def bauen(wurzel)   # Auszug für ein Projekt. Leerer Text, wenn es keine Karte gibt.
```

### `landkarte/lk/mindmap.py`
_Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver_

```
   13  konstante KOPF
  248  def bauen(modell, ziel)   # HTML-Mindmap aus einem Scan-Modell schreiben.
  279  def mermaid(modell, grenze)   # Kleiner Graph als Mermaid-Text - für schnelles Einfügen in Notizen.
```

### `landkarte/README.md`
_Landkarte_

```
    1  ueberschrift1 Landkarte
   10  ueberschrift2 Fünf Rollen
   24  ueberschrift2 Absicherung gegen eigene Fehler
   45  ueberschrift3 Was mit der falschen Fassung passiert
   65  ueberschrift2 Befehle
   89  ueberschrift2 Was wohin geschrieben wird
  113  ueberschrift2 Grenzen
  123  ueberschrift2 Keine Fremdabhängigkeiten
```

### `landkarte/lk/aufseher.py`
_Der Aufseher - erkennt Muster, findet wo die Kette hakt, schlägt vor_

```
   23  konstante WERKSTATT
   24  konstante BEFUND_JSON
   26  konstante _PFAD
   27  konstante _ZAHL
   28  konstante _HEX
   31  def fehlersignatur(text)
   40  def _claude_sitzungen_vorhanden(zurueck_tage)   # Wie viele Claude-Sitzungsdateien gab es zuletzt - Gegenprobe zur Chron
   59  def befund(zurueck)   # Alle Messwerte. Reine Rechnung, kein Modell.
  214  def beispiel_text(orte)
  218  konstante ANWEISUNG
  255  konstante SCHIEDS_ANWEISUNG
  271  def bericht(mit_modell, zurueck, doppelt)
  341  def messwerte_text(d)
```

### `landkarte/lk/pruefer.py`
_Die Absicherung - Gegenprobe, Zwillinge, Schiedsspruch, Zusicherungen_

```
   33  konstante PRUEFORDNER
   34  konstante ABWEICHUNGEN
   38  konstante SPRUCHBUCH
   39  konstante MAX_FASSUNG
   42  def protokoll_fingerabdruck(protokoll)   # Kennung des Protokoll-FORMATS, nicht des Inhalts.
   56  def spruch_festhalten(satz)   # Einen Schiedsspruch anhaengen. Niemals ueberschreiben.
   64  konstante _SCHLUESSELWORT
   70  konstante _BEKANNTE_PREFIXE
   76  konstante _BEARER
   77  konstante _PLATZHALTER
   85  def geheimnisverdacht(zeile)   # Gibt den verdaechtigen Ausschnitt zurueck, sonst None.
  117  def transkript_pfad(sitzung)
  127  def transkript_aufrufe(sitzung)   # Werkzeugaufrufe aus dem Sitzungsprotokoll von Claude Code.
  169  def chronik_gegenpruefen(sitzung)   # Hook-Chronik gegen das Sitzungsprotokoll stellen, Aufruf für Aufruf.
  220  def _zaehlen(liste)
  229  konstante SCHIEDS_ANWEISUNG
  279  konstante ARTEN
  282  def abweichungen_lesen(text)   # Die Zeilen des Schiedsspruchs in Daten verwandeln.
  303  def _abweichungen_trennen(text)
  312  def _aehnlichkeit(a, b)
  317  def kapitel_doppelt(sitzung, modell)   # Zwei unabhängige Schreiber, dann Schiedsspruch. Ergebnis wird abgelegt
  470  def _abweichungen_merken(sitzung, projekt, modell, geparst, reihenfolge, aehnlichkeit, fingerabdruck)   # Strichliste der Abweichungen - Rohstoff für den Aufseher.
       ... 5 weitere
```

### `landkarte/lk/sprachen.py`
_Symbole, Zweckzeile, Markierungen und Verweise aus einer Datei ziehen_

```
   16  konstante MARKIERUNG
   20  konstante GEHEIM_VERDACHT
   21  konstante KOMMENTAR_ZEICHEN
   25  konstante ZWECK_MARKER
   28  def _saubern(zeile)
   39  def zweck(text, pfad)   # Einzeiler, was die Datei tut. Leer, wenn die Datei es nicht sagt.
  106  def _kuerzen(s, grenze)
  123  def _py(text)
  227  konstante _ENDUNG_ZU_SPRACHE
  237  def sprache(pfad)
  243  def symbole(text, pfad)   # Definitionen der obersten Ebene mit Zeilennummer.
  285  def markierungen(text)
  302  konstante _IMPORT_PY
  303  konstante _IMPORT_JS
  304  konstante _IMPORT_PHP
  307  def rohverweise(text, pfad)   # Textstellen, die auf andere Dateien zeigen - noch nicht aufgeloest.
```

## Verflechtung

- `landkarte/lk/cli.py` → `landkarte/lk/mindmap.py`, `landkarte/lk/aufseher.py`, `landkarte/lk/chronik.py`, `landkarte/dienste/de.jan.landkarte.aufsicht.plist`, `landkarte/lk/regalwart.py`, `landkarte/lk/scan.py`, `landkarte/lk/notizen.py`, `landkarte/lk/buch.py`
- `landkarte/lk/pruefer.py` → `landkarte/hooks/hooks.json`, `landkarte/lk/notizen.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/register.py`, `landkarte/lk/chronik.py`, `landkarte/lk/konfig.py`, `landkarte/lk/karte.py`
- `landkarte/lk/aufseher.py` → `landkarte/lk/pruefer.py`, `landkarte/hooks/chronist.sh`, `landkarte/lk/register.py`, `landkarte/bin/landkarte`, `landkarte/lk/buch.py`, `landkarte/lk/chronik.py`, `landkarte/lk/konfig.py`, `landkarte/lk/karte.py`
- `landkarte/README.md` → `landkarte/lk/mindmap.py`, `landkarte/lk/scan.py`, `landkarte/hooks/hooks.json`, `landkarte/lk/digest.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/chronik.py`
- `landkarte/lk/digest.py` → `landkarte/lk/regalwart.py`, `landkarte/lk/notizen.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/chronik.py`, `landkarte/lk/konfig.py`, `landkarte/lk/korrektur.py`
- `landkarte/lk/karte.py` → `landkarte/lk/scan.py`, `landkarte/lk/notizen.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/chronik.py`, `landkarte/lk/konfig.py`, `landkarte/lk/korrektur.py`
- `landkarte/lk/register.py` → `landkarte/lk/regalwart.py`, `landkarte/lk/scan.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/chronik.py`, `landkarte/lk/konfig.py`, `landkarte/lk/karte.py`
- `landkarte/lk/scan.py` → `landkarte/bin/landkarte`, `landkarte/lk/sprachen.py`, `landkarte/lk/konfig.py`, `README.md`, `landkarte/README.md`
- `landkarte/lk/konfig.py` → `landkarte/bin/landkarte`, `landkarte/hooks/hooks.json`, `README.md`, `landkarte/README.md`
- `landkarte/lk/regalwart.py` → `landkarte/bin/landkarte`, `landkarte/lk/konfig.py`, `README.md`, `landkarte/README.md`
- `landkarte/lk/suche.py` → `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`, `landkarte/lk/konfig.py`, `landkarte/lk/buch.py`
- `landkarte/skills/landkarte/SKILL.md` → `landkarte/lk/mindmap.py`, `landkarte/hooks/hooks.json`, `landkarte/bin/landkarte`, `landkarte/lk/scan.py`
- `landkarte/hooks/chronist.sh` → `landkarte/bin/landkarte`, `landkarte/lk/schwaerzen.py`, `landkarte/lk/chronik.py`
- `landkarte/hooks/sitzungsstart.sh` → `landkarte/bin/landkarte`, `landkarte/lk/digest.py`, `landkarte/lk/scan.py`
- `landkarte/lk/buch.py` → `landkarte/bin/landkarte`, `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`
- `landkarte/lk/nachtrag.py` → `landkarte/lk/konfig.py`, `landkarte/lk/schwaerzen.py`, `landkarte/lk/chronik.py`
- `landkarte/lk/chronik.py` → `landkarte/lk/konfig.py`, `landkarte/lk/schwaerzen.py`
- `README.md` → `landkarte/bin/landkarte`
- `landkarte/dienste/de.jan.landkarte.aufsicht.plist` → `landkarte/bin/landkarte`
- `landkarte/dienste/de.jan.landkarte.regal.plist` → `landkarte/bin/landkarte`

## Offene Punkte

**Markierungen im Code**

- `landkarte/README.md:57` OFFEN: lassen, nicht raten |
- `landkarte/README.md:76` OFFEN: ]
- `landkarte/lk/buch.py:60` OFFEN: 
- `landkarte/lk/buch.py:318` OFFEN: "] = _punkte(k["abschnitte"].get("Offen", []))
- `landkarte/lk/cli.py:88` OFFEN: ": "Offen"}.get(args.art.lower(), "Fallen")
- `landkarte/lk/cli.py:127` OFFEN: chronik.kapitel_faellig(min_aufrufe=args.min_aufrufe)
- `landkarte/lk/cli.py:128` OFFEN: 
- `landkarte/lk/cli.py:131` OFFEN: )} Kapitel fällig.")
- `landkarte/lk/cli.py:132` OFFEN: [: args.grenze]:
- `landkarte/lk/cli.py:278` ACHTUNG: ähnlich: "
- `landkarte/lk/cli.py:362` ACHTUNG: Positionsvorliebe: "
- `landkarte/lk/cli.py:716` OFFEN: ")
- `landkarte/lk/digest.py:115` OFFEN: list(notiz.get("Offen", []))
- `landkarte/lk/digest.py:117` OFFEN: += k.get("offen", [])
- `landkarte/lk/digest.py:118` OFFEN: 
- `landkarte/lk/digest.py:119` OFFEN: ")
- `landkarte/lk/digest.py:120` OFFEN: [:10]:
- `landkarte/lk/karte.py:150` OFFEN: list(notiz.get("Offen", []))
- `landkarte/lk/karte.py:156` OFFEN: ", []):
- `landkarte/lk/karte.py:157` OFFEN: .append(f"{o}  _({k['kopf'].get('datum','')})_")
- `landkarte/lk/karte.py:162` OFFEN: korrektur.anwenden(offen, korrekturen)
- `landkarte/lk/karte.py:275` WICHTIG: sorted(kanten.items(), key=lambda kv: -len(kv[1]))[:20]
- `landkarte/lk/karte.py:276` WICHTIG: 
- `landkarte/lk/karte.py:280` OFFEN: 
- `landkarte/lk/karte.py:283` OFFEN: 
- `landkarte/lk/karte.py:284` OFFEN: 
- `landkarte/lk/karte.py:294` OFFEN: and not marken:
- `landkarte/lk/konfig.py:54` TODO: ",
- `landkarte/lk/nachtrag.py:8` WICHTIG: sie dürfen die Gegenprobe des Chronisten nicht bestätigen, denn sie
- `landkarte/lk/notizen.py:28` OFFEN: 

