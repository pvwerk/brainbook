# Landkarte: werkzeuge

> Projektgedächtnis für Menschen und KI-Assistenten

Stand **2026-11-08 23:20** · 47 Dateien · 11104 Zeilen · git `main@fd3eb6a`

`/Users/gustafbot/Projekte/werkzeuge`

Letzter Commit: 2026-11-08 Lizenz und Startseite fuer die Veroeffentlichung

Ausgelassen (von Git ignoriert oder in `.landkarte/ignorieren.txt`): `.landkarte/karte.json`, `.landkarte/symbole.md`, `landkarte/lk/__pycache__`

<!-- Diese Datei wird von `landkarte` erzeugt. Handschriftliches gehört in .landkarte/notizen.md, das bleibt beim Neubau erhalten. -->

## Spickzettel

**Befehle**

| Befehl                            | wofür |
| --------------------------------- | ---------------------------------------- |
| `python3 brainbook-einrichten.py` | aus README.md |

**Adressen und Hosts**

- `https://raw.githubusercontent.com/pvwerk/brainbook/main/landkarte/verteilen/brainbook-einrichten.py`

## Fallen

_Noch keine erfasst._

## Regeln

_Noch keine._

## Wo liegt was

**Wurzel**

- `.gitignore`
- `LICENSE`
- `README.md` — Brainbook & Landkarte  _[4 Verweise]_

**`landkarte/`** — 2 Dateien, 347 Zeilen

- `.gitignore`
- `README.md` — Landkarte  _[4 Verweise]_

**`landkarte/bin/`** — 2 Dateien, 0 Zeilen

- `brainbook`  _[17 Verweise]_
- `landkarte`  _[38 Verweise]_

**`landkarte/commands/`** — 1 Dateien, 23 Zeilen

- `brainbook.md` — description: Brainbook und Landkarte — Stichwort nachschlagen, eintragen, Selbstprotokoll  _[17 Verweise]_

**`landkarte/dienste/`** — 2 Dateien, 49 Zeilen

- `de.jan.landkarte.aufsicht.plist`
- `de.jan.landkarte.regal.plist`

**`landkarte/hooks/`** — 4 Dateien, 151 Zeilen

- `chronist.sh` — Der Chronist. Haengt einen Werkzeugaufruf an die Tageschronik an
- `hooks.json`  _[5 Verweise]_
- `sitzungsende.sh` — Stoesst am Sitzungsende den Schreiber an - vollstaendig abgekoppelt
- `sitzungsstart.sh` — Legt beim Sitzungsstart den Auszug der Landkarte in den Kontext

**`landkarte/lk/`** — 23 Dateien, 7199 Zeilen

- `__init__.py` — Landkarte - Inhaltsverzeichnis, Spickzettel, Fallenprotokoll, Mindmap
- `aufseher.py` — Der Aufseher - erkennt Muster, findet wo die Kette hakt, schlägt vor
- `brainbook.py` — Das Brainbook - Uebersetzung von Jans Worten in die Ablage  _[17 Verweise]_
- `buch.py` — Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen  _[11 Verweise]_
- `chronik.py` — Rohprotokoll aller Werkzeugaufrufe lesen, auswerten, verdichten  _[10 Verweise]_
- `cli.py` — Befehlszeile der Landkarte  _[Einstieg]_
- `digest.py` — Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt  _[3 Verweise]_
- `karte.py` — Der Setzer - aus Scan, Buch und Notizen die KARTE.md bauen  _[4 Verweise]_
- `konfig.py` — Einstellungen und Pfade der Landkarte, plus Projekterkennung  _[16 Verweise]_
- `korrektur.py` — Falsches Wissen richtigstellen, ohne das Original zu löschen  _[3 Verweise]_
- `mindmap.py` — Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver  _[3 Verweise]_
- `nachtrag.py` — Chronik rückwirkend aus den Sitzungsprotokollen von Claude Code füllen
- `notizen.py` — Handgepflegte Notizen eines Projekts - werden nie überschrieben  _[5 Verweise]_
- `pruefer.py` — Die Absicherung - Gegenprobe, Zwillinge, Schiedsspruch, Zusicherungen
- `regalwart.py` — Der Regalwart - beschriftet und sortiert die Regale, erkennt neue  _[4 Verweise]_
- `register.py` — Der Bibliothekar - Projekte finden, nach Nutzung sortieren, Regal schreiben  _[3 Verweise]_
- `scan.py` — Ein Projekt einlesen und als Datenmodell zurueckgeben  _[8 Verweise]_
- `schwaerzen.py` — Zugangsdaten aus Protokolltexten entfernen, bevor sie irgendwo landen  _[6 Verweise]_
- `sprachen.py` — Symbole, Zweckzeile, Markierungen und Verweise aus einer Datei ziehen
- `statistik.py` — Das Werkzeug protokolliert sich selbst - unabhaengig von jeder KI
- `suche.py` — In Sekunden finden - Symbole, Dateien, Fallen, Kapitel, alle Projekte
- `testleser.py` — Der Testleser - liest stichprobenartig ein Kapitel und prueft, ob  _[3 Verweise]_
- `vorstellung.py` — Die Bibliothek erklaert sich beim ersten Mal selbst

**`landkarte/skills/landkarte/`** — 1 Dateien, 160 Zeilen

- `SKILL.md` — name: landkarte

**`landkarte/verteilen/`** — 9 Dateien, 3005 Zeilen

- `AGENTS.md` — Anweisung für KI-Assistenten: Landkarte & Brainbook
- `RUECKMELDUNG.md` — Rückmeldung — wie das Werkzeug besser wird
- `START-HIER.md` — Landkarte & Brainbook — Startseite
- `brainbook-einrichten.py` — Brainbook & Landkarte — Einrichtung in einer einzigen Datei
- `einrichten.sh` — Landkarte und Brainbook auf einem neuen Rechner einrichten  _[9 Verweise]_
- `fuer-chatgpt.md` — Für ChatGPT
- `fuer-claude-code.md` — Für André — Claude Code
- `fuer-grok.md` — Für Christiane — Grok
- `paket-bauen.py` — Aus dem Repository eine einzige Einrichtungsdatei bauen

## Symbole der wichtigsten Dateien

Python exakt über den Syntaxbaum; andere Sprachen über Textregeln, also oberste Ebene zuverlässig, Verschachteltes nicht. Vollständig in `.landkarte/symbole.md`.

### `landkarte/lk/brainbook.py`
_Das Brainbook - Uebersetzung von Jans Worten in die Ablage_

```
   27  konstante BUCH
   28  konstante EINTRAGUNGEN
   30  konstante TRENNER
   31  konstante FELDER
   33  konstante KOPFTEXT
   60  def _normal(text)
   67  def laden()   # {stichwort: eintrag} in der Reihenfolge der Datei.
  113  def _regal_lesen(wert)
  120  def nachschlagen(begriff)   # Jans Wort in Ablagenorte uebersetzen. Genauer Treffer zuerst.
  150  def stichworte()   # Nur die Schluesselwoerter - fuer den Auszug beim Sitzungsstart.
  161  def _regal_aufloesen(angabe)   # Projektangabe auf ein bekanntes Regal abbilden.
  186  def merken(stichwort, ist, auch, was, kategorien, verweise, notiz)   # Eintrag anlegen oder ergaenzen. Es werden nur Verweise gespeichert.
  266  def _schreiben(eintraege)
  289  def ausgeben(eintrag)   # Einen Eintrag als Textblock.
```

### `landkarte/lk/konfig.py`
_Einstellungen und Pfade der Landkarte, plus Projekterkennung_

```
    9  konstante HEIM
   10  konstante LK_HEIM
   11  konstante REGISTER
   12  konstante PROJEKT_CACHE
   13  konstante KONFIG_DATEI
   15  konstante STANDARD
   54  konstante TEXT_ENDUNGEN
   64  konstante TEXT_NAMEN
   71  konstante MAX_DATEI
   72  konstante MAX_DATEIEN
   73  konstante MAX_EDGES_JE_DATEI
   76  konstante NIEMALS_PROJEKT
   85  konstante PUNKTORDNER_ERLAUBT
   88  konstante CLAUDE_ERLAUBT
   91  konstante PROJEKT_MARKER
   98  def laden()   # Konfiguration lesen, fehlende Schluessel aus STANDARD ergaenzen.
  111  def schreiben(konf)
  116  def ausklappen(pfad)
  120  def ist_text(p)
  126  def ist_projekt(ordner)
  144  def slug(pfad)
```

### `landkarte/lk/buch.py`
_Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen_

```
   24  konstante STANDARD_MODELL
   26  konstante ANWEISUNG
   65  def _dauer(sek)
   74  def bericht_text(bericht)   # Den verdichteten Bericht als Text fuer das Modell.
  128  def _gescheitert(datei, fehler_je_datei)
  135  def _claude_rufen(anfrage, modell)   # Ein Sprachmodell mit einer Textaufgabe rufen.
  164  def _titel_trennen(rohtext)
  179  def _dateiname(datum, titel, sitzung)
  187  def buchordner(projekt_wurzel)
  191  def kapitel_schreiben(sitzung, modell, trocken)   # Ein Kapitel fuer eine Sitzung erzeugen und ablegen.
  257  konstante KOPF_MUSTER
  260  def kapitel_lesen(pfad)   # Ein Kapitel in Kopfdaten und Abschnitte zerlegen.
  298  def _punkte(zeilen)
  309  def kapitel_sammeln(projekt_wurzel)
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

### `landkarte/verteilen/einrichten.sh`
_Landkarte und Brainbook auf einem neuen Rechner einrichten_

```
    8  variable WURZEL
    9  variable ZIEL
   11  funktion sage
   12  funktion fehler
   71  variable NAME
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
   25  def messen(**werte)   # Zaehlwerte fuer das Selbstprotokoll hinterlegen - niemals Inhalte.
   30  def projektwurzel(pfad)   # Projektordner bestimmen: Angabe, sonst von hier aufwaerts suchen.
   47  def _kurz(p)
   54  def befehl_scan(args)
   76  def befehl_regal(args)
   91  def befehl_digest(args)
  105  def befehl_vorstellen(args)   # Erklären, was die Bibliothek kann und wie man eingreift.
  116  def befehl_finde(args)
  123  def befehl_notiz(args)
  136  def _kapitel_machen(sitzung, args)   # Einfach oder doppelt, je nach Einstellung.
  144  def _kapitel_melden(ergebnis)
  164  def befehl_kapitel(args)
  198  def befehl_merke(args)   # Ein Stichwort von Jan in das Brainbook eintragen.
  215  def befehl_brainbook(args)
  243  def befehl_wo(args)   # Dreistufig nachschlagen: Regal, Fach, Inhalt.
  379  def befehl_regale(args)
  408  def befehl_korrigieren(args)
  418  def befehl_lesung(args)   # Testleser: Kapitel lesen, Verzeichnis daran messen, Belegbares richten
  463  def befehl_protokoll(args)   # Das Spruchbuch des Schiedsrichters lesen.
  512  def befehl_abweichungen(args)
  531  def befehl_pruefen(args)
  557  def befehl_aufsicht(args)
       ... 13 weitere
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

### `README.md`
_Brainbook & Landkarte_

```
    1  ueberschrift1 Brainbook & Landkarte
   10  ueberschrift2 In einem Befehl einrichten
   30  ueberschrift2 Was es tut
   53  ueberschrift2 Das Brainbook
   67  ueberschrift2 Sieben Teile, drei mit Sprachmodell
   82  ueberschrift2 Absicherung gegen eigene Fehler
  106  ueberschrift2 Selbstprotokoll — kontextlos
  126  ueberschrift2 Mehr
```

### `landkarte/README.md`
_Landkarte_

```
    1  ueberschrift1 Landkarte
   10  ueberschrift2 Fünf Rollen
   23  ueberschrift2 Der Testleser — Rückwärtssuche
   47  ueberschrift3 Was er selbst richtet und was nicht
   61  ueberschrift2 Das Brainbook — am Tresen, in keiner Liste
   98  ueberschrift2 Drei Listen
  119  ueberschrift2 Absicherung gegen eigene Fehler
  140  ueberschrift3 Was mit der falschen Fassung passiert
  160  ueberschrift2 Weitergeben
  180  ueberschrift2 Erklärt sich selbst
  192  ueberschrift2 Selbstprotokoll — kontextlos
  219  ueberschrift2 Befehle
  258  ueberschrift2 Was wohin geschrieben wird
  287  ueberschrift2 Grenzen
  297  ueberschrift2 Zugangsdaten
  324  ueberschrift2 Was ins Repository gehört
  339  ueberschrift2 Keine Fremdabhängigkeiten
```

### `landkarte/lk/testleser.py`
_Der Testleser - liest stichprobenartig ein Kapitel und prueft, ob_

```
   27  konstante LESUNGEN
   28  konstante SCHLAGWORT_DATEI
   29  konstante MAX_NEUE_SCHLAGWORTE
   30  konstante EINDEUTIG_AB
   32  konstante ANWEISUNG
   59  def _antwort_lesen(text)
   90  def kapitel_auswaehlen(anzahl)   # Kapitel aussuchen: lange nicht geprueft und inhaltsreich zuerst.
  129  def _suchprobe(begriff, kapitelpfad, projektwurzel)   # Findet das Verzeichnis dieses Kapitel oder sein Projekt?
  139  def schlagwortdatei(wurzel)
  143  def schlagworte_laden(wurzel)   # {kapitel-datei: [begriffe]} aus der maschinell gepflegten Datei.
  165  def schlagworte_ergaenzen(wurzel, kapiteldatei, neue)   # Begriffe anhaengen. Eigene Datei, damit notizen.md dem Menschen bleibt
  209  def _regal_pruefen(kapitel, projektwurzel, vermutet)   # Steht das Buch im richtigen Regal, ist das Regal richtig beschriftet.
  285  def _alias_eintragen(projektwurzel, alias)
  301  def lesung(kapitel, projektwurzel, modell, trocken)   # Ein Kapitel lesen, das Verzeichnis daran pruefen, Belegbares korrigier
  386  def _journal(wurzel, kapitel, vorschlaege)
  398  def runde(anzahl, modell, trocken)
  407  def bilanz(zurueck_tage)   # Wie gut ist das Verzeichnis - gemessen, nicht geschaetzt.
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

### `landkarte/lk/digest.py`
_Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt_

```
   17  konstante GRENZE
   20  def _kuerzen(zeilen, grenze)
   36  def bauen(wurzel, grenze)   # Auszug für ein Projekt. Leerer Text, wenn es keine Karte gibt.
```

### `landkarte/lk/mindmap.py`
_Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver_

```
   13  konstante KOPF
  248  def bauen(modell, ziel)   # HTML-Mindmap aus einem Scan-Modell schreiben.
  279  def mermaid(modell, grenze)   # Kleiner Graph als Mermaid-Text - für schnelles Einfügen in Notizen.
```

## Verflechtung

- `landkarte/lk/cli.py` → `landkarte/lk/mindmap.py`, `landkarte/lk/chronik.py`, `landkarte/lk/scan.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`, `landkarte/lk/register.py`, `landkarte/lk/testleser.py`, `landkarte/lk/konfig.py`
- `landkarte/README.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/mindmap.py`, `landkarte/lk/schwaerzen.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/verteilen/einrichten.sh`
- `landkarte/lk/pruefer.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/korrektur.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`
- `landkarte/lk/digest.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/korrektur.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`
- `landkarte/lk/aufseher.py` → `landkarte/lk/pruefer.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/register.py`, `landkarte/lk/testleser.py`, `landkarte/hooks/chronist.sh`, `landkarte/lk/konfig.py`
- `landkarte/lk/karte.py` → `landkarte/lk/korrektur.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/lk/scan.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`, `landkarte/lk/testleser.py`, `landkarte/lk/konfig.py`
- `landkarte/lk/statistik.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/schwaerzen.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/bin/landkarte`, `landkarte/lk/sprachen.py`, `landkarte/lk/konfig.py`
- `landkarte/lk/vorstellung.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`, `README.md`, `landkarte/README.md`, `landkarte/bin/landkarte`, `landkarte/lk/konfig.py`
- `landkarte/skills/landkarte/SKILL.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/mindmap.py`, `landkarte/lk/schwaerzen.py`, `landkarte/lk/scan.py`, `landkarte/bin/landkarte`, `landkarte/hooks/hooks.json`
- `landkarte/lk/register.py` → `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/lk/scan.py`, `landkarte/bin/landkarte`, `landkarte/lk/regalwart.py`, `landkarte/lk/konfig.py`, `landkarte/lk/karte.py`
- `landkarte/verteilen/RUECKMELDUNG.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/lk/scan.py`, `landkarte/lk/statistik.py`, `landkarte/bin/landkarte`
- `landkarte/lk/konfig.py` → `LICENSE`, `landkarte/lk/statistik.py`, `README.md`, `landkarte/README.md`, `landkarte/bin/landkarte`, `landkarte/hooks/hooks.json`
- `landkarte/lk/testleser.py` → `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/suche.py`, `landkarte/lk/regalwart.py`, `landkarte/lk/konfig.py`, `landkarte/lk/karte.py`
- `landkarte/verteilen/paket-bauen.py` → `landkarte/bin/landkarte`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/hooks/hooks.json`
- `README.md` → `landkarte/bin/landkarte`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`
- `landkarte/lk/scan.py` → `landkarte/bin/landkarte`, `landkarte/lk/sprachen.py`, `README.md`, `landkarte/README.md`, `landkarte/lk/konfig.py`
- `landkarte/verteilen/AGENTS.md` → `landkarte/lk/scan.py`, `landkarte/bin/landkarte`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`
- `landkarte/verteilen/START-HIER.md` → `landkarte/bin/landkarte`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`
- `landkarte/verteilen/brainbook-einrichten.py` → `landkarte/bin/landkarte`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`
- `landkarte/lk/brainbook.py` → `landkarte/bin/landkarte`, `landkarte/lk/regalwart.py`, `landkarte/lk/konfig.py`, `landkarte/lk/buch.py`

## Offene Punkte

**Markierungen im Code**

- `landkarte/README.md:152` OFFEN: lassen, nicht raten |
- `landkarte/README.md:230` OFFEN: ]
- `landkarte/lk/aufseher.py:449` OFFEN: [{v['schwere']}] {v.get('kapitel')}: "
- `landkarte/lk/buch.py:60` OFFEN: 
- `landkarte/lk/buch.py:319` OFFEN: "] = _punkte(k["abschnitte"].get("Offen", []))
- `landkarte/lk/cli.py:127` OFFEN: ": "Offen"}.get(args.art.lower(), "Fallen")
- `landkarte/lk/cli.py:166` OFFEN: chronik.kapitel_faellig(min_aufrufe=args.min_aufrufe)
- `landkarte/lk/cli.py:167` OFFEN: 
- `landkarte/lk/cli.py:170` OFFEN: )} Kapitel fällig.")
- `landkarte/lk/cli.py:171` OFFEN: [: args.grenze]:
- `landkarte/lk/cli.py:396` ACHTUNG: ähnlich: "
- `landkarte/lk/cli.py:525` ACHTUNG: Positionsvorliebe: "
- `landkarte/lk/cli.py:953` OFFEN: ")
- `landkarte/lk/digest.py:116` OFFEN: list(notiz.get("Offen", []))
- `landkarte/lk/digest.py:118` OFFEN: += k.get("offen", [])
- `landkarte/lk/digest.py:119` OFFEN: 
- `landkarte/lk/digest.py:120` OFFEN: ")
- `landkarte/lk/digest.py:121` OFFEN: [:10]:
- `landkarte/lk/karte.py:153` OFFEN: list(notiz.get("Offen", []))
- `landkarte/lk/karte.py:159` OFFEN: ", []):
- `landkarte/lk/karte.py:160` OFFEN: .append(f"{o}  _({k['kopf'].get('datum','')})_")
- `landkarte/lk/karte.py:165` OFFEN: korrektur.anwenden(offen, korrekturen)
- `landkarte/lk/karte.py:287` WICHTIG: sorted(kanten.items(), key=lambda kv: -len(kv[1]))[:20]
- `landkarte/lk/karte.py:288` WICHTIG: 
- `landkarte/lk/karte.py:292` OFFEN: 
- `landkarte/lk/karte.py:295` OFFEN: 
- `landkarte/lk/karte.py:296` OFFEN: 
- `landkarte/lk/karte.py:306` OFFEN: and not marken:
- `landkarte/lk/konfig.py:66` TODO: ",
- `landkarte/lk/nachtrag.py:8` WICHTIG: sie dürfen die Gegenprobe des Chronisten nicht bestätigen, denn sie

