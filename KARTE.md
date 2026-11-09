# Landkarte: werkzeuge

> Projektgedächtnis für Menschen und KI-Assistenten

Stand **2026-11-09 21:20** · 58 Dateien · 16049 Zeilen · git `main@b76f918`, 2 geändert

`/Users/gustafbot/Projekte/werkzeuge`

Letzter Commit: 2026-11-09 Fassung 2.0.0 — Passwort-Tresor, Tresorwache und Verzeichnis der offenen Punkte

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

Hier wurde schon Zeit verloren. Vor dem Anfassen lesen.

- [2026-11-09] Marktplatz NIEMALS auf eine Kopie zeigen lassen. Zeigte am 08.11. auf ~/brainbook (eine Kopie aus einem Fehltest); Claude Code lud daraufhin eine eingefrorene 1.0.0 aus dem Zwischenspeicher, und neue Hooks wurden nie aktiv. Der Chronist schrieb trotzdem mit, weil seine Skripte ueber ~/.local/bin/landkarte liefen - deshalb fiel es wochenlang nicht auf. Pruefen mit: claude plugin list (Zeile 'Read from:' muss ~/Projekte/werkzeuge/landkarte sein).
- [2026-11-09] Verbindlich fuer 'was liegt draussen' ist die Markierung im Repository (git ls-remote --tags), nicht raw.githubusercontent.com - die Rohdatei kommt aus einem Zwischenspeicher und laeuft nach dem Schieben einige Minuten nach. Fassungen nach Nummern vergleichen, nicht als Text.
- [2026-11-09] Eine Geheimnis-Erkennung muss zwei Scharfstellungen haben, sonst zerstoert sie den Verlauf. Im Chat darf sie raten, beim Rundgang ueber Protokolle nur bei eindeutigen Formen (sk-ant-, ghp_, AKIA, JWT, URL-Anmeldung, bestimmte Umgebungsvariablen). Mit lockeren Regeln fand sie am 09.11.2026 in einem Protokoll 155 'Geheimnisse' und haette 12788 Stellen ueberschrieben: UUIDs, Zeitstempel und das Wort 'passwort', das in deutschsprachigem Code ueberall steht. Nach dem Verschaerfen 8 echte Werte. Weitere Einzelfallen: Hochkommata um PGPASSWORD werden mitgefangen; Shell-Verweise und bereits Geschwaerztes sind Platzhalter; ein Codefragment ging als AWS-Schluessel durch; AWS-Schluessel enthalten Schraegstriche und fielen dem Pfadfilter zum Opfer.

## Regeln

- [2026-11-09] Freigabe: nie von Hand pushen. 'landkarte freigabe --pruefen' (13 Pruefungen), dann 'landkarte freigabe --neu fehler|klein|gross --jetzt --text ...'. Reihenfolge fest: pruefen, stempeln (plugin.json + lk/__init__.py), Paket bauen, AENDERUNGEN.md, Commit, Markierung vX.Y.Z, push --follow-tags. Harte Pruefung fehlgeschlagen = nichts geaendert. Stand gegen GitHub: 'landkarte freigabe' ohne Schalter.
- [2026-11-09] Tresor und Tresorwache seit Fassung 2.0.0 (09.11.2026). Der Tresor liegt unter ~/.landkarte/tresor.enc, aes-256-cbc/pbkdf2-600000 ueber openssl plus HMAC ueber den Geheimtext; Hauptschluessel im macOS-Schluesselbund, sonst Datei mit 600. Die Tresorwache haengt am UserPromptSubmit-Hook und ist die EINZIGE Stelle, die am Sitzungsprotokoll etwas aendern darf - sie ersetzt Geheimnisse durch einen Verweis und legt vorher eine Kopie in ~/.Papierkorb-Claude/tresorwache/. Wichtig: UserPromptSubmit kann den Prompt NICHT umschreiben (nur PreToolUse kann updatedInput), das eine Mal sieht das Modell das Passwort also noch; verhindert wird das Weiterleben im Protokoll.

## Wo liegt was

**Wurzel**

- `.gitignore`
- `AENDERUNGEN.md` — Änderungen
- `LICENSE`
- `README.md` — Brainbook & Landkarte  _[4 Verweise]_

**`landkarte/`** — 2 Dateien, 423 Zeilen

- `.gitignore`
- `README.md` — Landkarte  _[4 Verweise]_

**`landkarte/bin/`** — 4 Dateien, 0 Zeilen

- `brainbook`  _[20 Verweise]_
- `landkarte`  _[46 Verweise]_
- `platzanweiser`  _[4 Verweise]_
- `tresorwache`

**`landkarte/commands/`** — 1 Dateien, 23 Zeilen

- `brainbook.md` — description: Brainbook und Landkarte — Stichwort nachschlagen, eintragen, Selbstprotokoll  _[20 Verweise]_

**`landkarte/dienste/`** — 2 Dateien, 65 Zeilen

- `de.jan.landkarte.aufsicht.plist`
- `de.jan.landkarte.regal.plist`

**`landkarte/hooks/`** — 6 Dateien, 208 Zeilen

- `chronist.sh` — Der Chronist. Haengt einen Werkzeugaufruf an die Tageschronik an
- `hooks.json`  _[5 Verweise]_
- `platzanweiser.sh` — Haelt eine KI an, die Code liest, ohne vorher nachzuschlagen  _[4 Verweise]_
- `sitzungsende.sh` — Stoesst am Sitzungsende den Schreiber an - vollstaendig abgekoppelt
- `sitzungsstart.sh` — Legt beim Sitzungsstart den Auszug der Landkarte in den Kontext
- `tresorwache.sh` — Erkennt Zugangsdaten im Gespraech, legt sie verschluesselt ab und

**`landkarte/lk/`** — 29 Dateien, 10752 Zeilen

- `__init__.py` — Landkarte - Inhaltsverzeichnis, Spickzettel, Fallenprotokoll, Mindmap
- `anweisung.py` — Die eine Regel, die vor jeder Aenderung gilt - an einer Stelle  _[6 Verweise]_
- `aufgaben.py` — Verzeichnis der offenen Punkte im Brainbook
- `aufseher.py` — Der Aufseher - erkennt Muster, findet wo die Kette hakt, schlägt vor
- `brainbook.py` — Das Brainbook - Uebersetzung von Jans Worten in die Ablage  _[20 Verweise]_
- `buch.py` — Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen  _[11 Verweise]_
- `chronik.py` — Rohprotokoll aller Werkzeugaufrufe lesen, auswerten, verdichten  _[9 Verweise]_
- `cli.py` — Befehlszeile der Landkarte  _[Einstieg]_
- `digest.py` — Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt  _[5 Verweise]_
- `freigabe.py` — Eine Fassung bewusst freigeben - pruefen, stempeln, hochladen  _[4 Verweise]_
- `karte.py` — Der Setzer - aus Scan, Buch und Notizen die KARTE.md bauen  _[6 Verweise]_
- `konfig.py` — Einstellungen und Pfade der Landkarte, plus Projekterkennung  _[21 Verweise]_
- `korrektur.py` — Falsches Wissen richtigstellen, ohne das Original zu löschen  _[4 Verweise]_
- `mindmap.py` — Mindmap als eine einzelne HTML-Datei - offline, ohne Fremdserver
- `nachtrag.py` — Chronik rückwirkend aus den Sitzungsprotokollen von Claude Code füllen
- `notizen.py` — Handgepflegte Notizen eines Projekts - werden nie überschrieben  _[5 Verweise]_
- `platzanweiser.py` — Haelt eine KI an, die Code liest, ohne vorher nachzuschlagen  _[3 Verweise]_
- `pruefer.py` — Die Absicherung - Gegenprobe, Zwillinge, Schiedsspruch, Zusicherungen
- `regalwart.py` — Der Regalwart - beschriftet und sortiert die Regale, erkennt neue  _[5 Verweise]_
- `register.py` — Der Bibliothekar - Projekte finden, nach Nutzung sortieren, Regal schreiben
- `scan.py` — Ein Projekt einlesen und als Datenmodell zurueckgeben  _[7 Verweise]_
- `schwaerzen.py` — Zugangsdaten aus Protokolltexten entfernen, bevor sie irgendwo landen  _[7 Verweise]_
- `sprachen.py` — Symbole, Zweckzeile, Markierungen und Verweise aus einer Datei ziehen
- `statistik.py` — Das Werkzeug protokolliert sich selbst - unabhaengig von jeder KI  _[3 Verweise]_
- `suche.py` — In Sekunden finden - Symbole, Dateien, Fallen, Kapitel, alle Projekte
- `testleser.py` — Der Testleser - liest stichprobenartig ein Kapitel und prueft, ob  _[3 Verweise]_
- `tresor.py` — verschluesselter Tresor fuer Zugangsdaten im Brainbook  _[4 Verweise]_
- `tresorwache.py` — Passwoerter im Gespraech erkennen, in den Tresor legen, aus dem
- `vorstellung.py` — Die Bibliothek erklaert sich beim ersten Mal selbst

**`landkarte/skills/landkarte/`** — 1 Dateien, 160 Zeilen

- `SKILL.md` — name: landkarte

**`landkarte/verteilen/`** — 9 Dateien, 4041 Zeilen

- `AGENTS.md` — Anweisung für KI-Assistenten: Landkarte & Brainbook
- `RUECKMELDUNG.md` — Rückmeldung — wie das Werkzeug besser wird
- `START-HIER.md` — Landkarte & Brainbook — Startseite
- `brainbook-einrichten.py` — Brainbook & Landkarte — Einrichtung in einer einzigen Datei
- `einrichten.sh` — Landkarte und Brainbook auf einem neuen Rechner einrichten  _[10 Verweise]_
- `fuer-chatgpt.md` — Für ChatGPT
- `fuer-claude-code.md` — Für André — Claude Code
- `fuer-grok.md` — Für Christiane — Grok
- `paket-bauen.py` — Aus dem Repository eine einzige Einrichtungsdatei bauen

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
   57  konstante TEXT_ENDUNGEN
   67  konstante TEXT_NAMEN
   74  konstante MAX_DATEI
   75  konstante MAX_DATEIEN
   76  konstante MAX_EDGES_JE_DATEI
   79  konstante NIEMALS_PROJEKT
   88  konstante PUNKTORDNER_ERLAUBT
   91  konstante CLAUDE_ERLAUBT
   94  konstante PROJEKT_MARKER
  101  def laden()   # Konfiguration lesen, fehlende Schluessel aus STANDARD ergaenzen.
  114  def schreiben(konf)
  119  def ausklappen(pfad)
  123  def ist_text(p)
  129  def ist_projekt(ordner)
  147  def slug(pfad)
```

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

### `landkarte/lk/buch.py`
_Der Schreiber - aus dem Rohprotokoll einer Sitzung ein Kapitel machen_

```
   24  konstante STANDARD_MODELL
   26  konstante ANWEISUNG
   65  def _dauer(sek)
   74  def bericht_text(bericht)   # Den verdichteten Bericht als Text fuer das Modell.
  128  def _gescheitert(datei, fehler_je_datei)
  135  konstante ZUSATZPFADE
  139  def _pfad_ergaenzen(pfad)   # Die ueblichen Orte anhaengen, falls der PATH beschnitten ist.
  149  def _programm_finden(name)   # Einen Programmnamen zu einem Pfad machen.
  170  def _claude_rufen(anfrage, modell)   # Ein Sprachmodell mit einer Textaufgabe rufen.
  201  def _titel_trennen(rohtext)
  216  def _dateiname(datum, titel, sitzung)
  224  def buchordner(projekt_wurzel)
  228  def kapitel_schreiben(sitzung, modell, trocken)   # Ein Kapitel fuer eine Sitzung erzeugen und ablegen.
  294  konstante KOPF_MUSTER
  297  def kapitel_lesen(pfad)   # Ein Kapitel in Kopfdaten und Abschnitte zerlegen.
  335  def _punkte(zeilen)
  346  def kapitel_sammeln(projekt_wurzel)
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
  159  def woertlich_schwaerzen(text)
```

### `landkarte/lk/anweisung.py`
_Die eine Regel, die vor jeder Aenderung gilt - an einer Stelle_

```
   20  konstante ANFANG
   21  konstante ENDE
   23  konstante UEBERSCHRIFT
   25  konstante TEXT
  136  def block()
  140  def kurzfassung()   # Eine Zeile fuer Hooks und Alarmmeldungen.
  148  def enthalten(datei)
  155  def einhaengen(datei, sicherung, oben)   # Den Block in eine Markdown-Datei einhaengen.
  204  def _sichern(datei)   # Eine Kopie in den Papierkorb legen, bevor eine fremde Datei angefasst 
  216  def zieldatei(ki)   # Wohin die Regel bei dieser KI gehoert.
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

### `landkarte/lk/digest.py`
_Der kompakte Auszug, den der Hook beim Sitzungsstart in den Kontext legt_

```
   17  konstante GRENZE
   20  def _kuerzen(zeilen, grenze)
   36  def bauen(wurzel, grenze)   # Auszug für ein Projekt. Leerer Text, wenn es keine Karte gibt.
```

### `README.md`
_Brainbook & Landkarte_

```
    1  ueberschrift1 Brainbook & Landkarte
   10  ueberschrift2 In einem Befehl einrichten
   30  ueberschrift2 Die Regel, auf der alles steht
   85  ueberschrift2 Du siehst in jeder Antwort, ob die Bibliothek etwas wusste
  107  ueberschrift2 Die Vergangenheit aufnehmen
  141  ueberschrift2 Aktualisieren
  167  ueberschrift2 Was es tut
  190  ueberschrift2 Das Brainbook
  204  ueberschrift2 Sieben Teile, drei mit Sprachmodell
  219  ueberschrift2 Absicherung gegen eigene Fehler
  243  ueberschrift2 Selbstprotokoll — kontextlos
  263  ueberschrift2 Mehr
```

### `landkarte/lk/cli.py`
_Befehlszeile der Landkarte_

```
   30  def messen(**werte)   # Zaehlwerte fuer das Selbstprotokoll hinterlegen - niemals Inhalte.
   35  def projektwurzel(pfad)   # Projektordner bestimmen: Angabe, sonst von hier aufwaerts suchen.
   52  def _kurz(p)
   59  def befehl_scan(args)
   81  def befehl_regal(args)
   96  def befehl_digest(args)
  110  def befehl_vorstellen(args)   # Erklären, was die Bibliothek kann und wie man eingreift.
  121  def _bb_zeile(treffer)   # Die Signalzeile, die Jan in jeder Antwort sehen will.
  132  def befehl_bb(args)   # Nachschlagen und das Ergebnis als Signalzeile melden.
  154  def befehl_finde(args)
  165  def befehl_notiz(args)
  178  def _kapitel_machen(sitzung, args)   # Einfach oder doppelt, je nach Einstellung.
  186  def _kapitel_melden(ergebnis)
  206  def befehl_kapitel(args)
  240  def befehl_merke(args)   # Ein Stichwort von Jan in das Brainbook eintragen.
  257  def befehl_brainbook(args)
  286  def befehl_wo(args)   # Dreistufig nachschlagen: Regal, Fach, Inhalt.
  430  def befehl_regale(args)
  459  def befehl_korrigieren(args)
  469  def befehl_lesung(args)   # Testleser: Kapitel lesen, Verzeichnis daran messen, Belegbares richten
  522  def befehl_protokoll(args)   # Das Spruchbuch des Schiedsrichters lesen.
  571  def befehl_abweichungen(args)
       ... 26 weitere
```

### `landkarte/lk/freigabe.py`
_Eine Fassung bewusst freigeben - pruefen, stempeln, hochladen_

```
   30  konstante PLUGIN
   31  konstante WURZEL
   32  konstante PLUGIN_JSON
   33  konstante INIT_PY
   34  konstante PAKETBAUER
   35  konstante INSTALLER
   36  konstante AENDERUNGEN
   38  konstante HERKUNFT
   39  konstante ZWEIG
   40  konstante ROH
   42  konstante MARKIERUNGEN
   45  konstante ERZEUGT
   54  konstante STUFEN
   59  def _git(*args, zeit=)   # git im Original aufrufen. Gibt (Code, Ausgabe) zurueck, wirft nie.
   71  def _lauf(befehl, heim, zeit)
   86  def _befund(name, ok, hinweis, hart)
   92  def fassung()   # Die gueltige Fassung - plugin.json ist die Quelle.
   97  def fassung_im_paket()   # Welche Fassung im Modul steht (muss mit plugin.json uebereinstimmen).
  103  def naechste(stufe)   # gross -> 2.0.0, klein -> 1.2.0, fehler -> 1.1.1
  117  def fassung_setzen(neu)   # Die Nummer an beiden Stellen setzen. Gibt die geaenderten Dateien.
  139  def als_zahlen(name)   # 1.2.10 -> (1, 2, 10). Fuer Vergleiche; "10" ist mehr als "9".
  150  def neueste_markierung(zeit)   # Die hoechste veroeffentlichte Fassung laut Markierungen. (Fassung, Feh
       ... 25 weitere
```

### `landkarte/lk/tresor.py`
_verschluesselter Tresor fuer Zugangsdaten im Brainbook_

```
   45  konstante TRESOR
   46  konstante SCHLUESSEL_DATEI
   47  konstante SCHLUESSELBUND_DIENST
   48  konstante ITERATIONEN
   49  konstante FASSUNG
   52  class TresorFehler(RuntimeError)   # Etwas stimmt mit dem Tresor nicht - nie mit Geheimnis im Text.
   59  def _openssl()
   74  konstante _SCHLUESSEL_NUR_DATEI
   77  def _schluesselbund_lesen()
   91  def _schluesselbund_schreiben(wert)
  105  def hauptschluessel(anlegen)   # Den Hauptschluessel holen, bei Bedarf einen neuen erzeugen.
  129  def schluessel_ort()
  137  def _mac_schluessel(haupt)   # Eigener Schluessel fuer den HMAC - nie derselbe wie zum Verschluesseln
  145  def _verschluesseln(klartext, haupt)
  165  def _entschluesseln(huelle, haupt)
  187  def _leer()
  199  def _stempel()
  206  def speicher_leeren()
  211  def laden()
  231  def sichern(daten)
  246  def _name_frei(daten, wunsch)
  255  def einlegen(name, geheimnis, herkunft, notiz)   # Ein Geheimnis ablegen. Gibt (Name, war_neu) zurueck.
       ... 6 weitere
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
  345  ueberschrift2 Entwickeln und freigeben
  373  ueberschrift3 Was geprüft wird
  394  ueberschrift2 Platzanweiser
```

## Verflechtung

- `landkarte/README.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/chronik.py`, `landkarte/hooks/hooks.json`, `landkarte/verteilen/einrichten.sh`, `landkarte/lk/freigabe.py`, `landkarte/lk/buch.py`
- `landkarte/lk/cli.py` → `landkarte/lk/konfig.py`, `landkarte/lk/buch.py`, `landkarte/lk/statistik.py`, `landkarte/lk/karte.py`, `landkarte/lk/testleser.py`, `landkarte/lk/vorstellung.py`, `landkarte/bin/platzanweiser`, `landkarte/hooks/platzanweiser.sh`
- `landkarte/lk/freigabe.py` → `AENDERUNGEN.md`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/lk/pruefer.py`, `landkarte/lk/aufgaben.py`, `landkarte/bin/landkarte`
- `landkarte/lk/pruefer.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`, `landkarte/lk/korrektur.py`, `landkarte/hooks/hooks.json`, `landkarte/lk/buch.py`
- `landkarte/verteilen/paket-bauen.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/hooks/hooks.json`, `landkarte/verteilen/einrichten.sh`, `landkarte/lk/freigabe.py`, `landkarte/bin/landkarte`, `landkarte/lk/anweisung.py`
- `landkarte/lk/digest.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`, `landkarte/lk/korrektur.py`, `landkarte/lk/buch.py`, `landkarte/lk/regalwart.py`
- `landkarte/lk/platzanweiser.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/lk/suche.py`, `landkarte/lk/digest.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`
- `landkarte/lk/aufseher.py` → `landkarte/lk/pruefer.py`, `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/karte.py`, `landkarte/lk/testleser.py`, `landkarte/lk/register.py`
- `landkarte/lk/vorstellung.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/bin/landkarte`, `README.md`, `landkarte/README.md`
- `landkarte/lk/karte.py` → `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`, `landkarte/lk/korrektur.py`, `landkarte/lk/buch.py`, `landkarte/bin/landkarte`, `landkarte/lk/notizen.py`, `landkarte/lk/testleser.py`, `landkarte/lk/scan.py`
- `landkarte/lk/statistik.py` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/lk/konfig.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/bin/landkarte`, `landkarte/lk/sprachen.py`, `landkarte/lk/schwaerzen.py`
- `landkarte/skills/landkarte/SKILL.md` → `landkarte/lk/schwaerzen.py`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/hooks/hooks.json`, `landkarte/lk/mindmap.py`, `landkarte/bin/landkarte`, `landkarte/lk/scan.py`
- `README.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/lk/freigabe.py`, `landkarte/bin/landkarte`, `landkarte/lk/anweisung.py`
- `landkarte/lk/register.py` → `landkarte/lk/konfig.py`, `landkarte/lk/chronik.py`, `landkarte/lk/buch.py`, `landkarte/lk/regalwart.py`, `landkarte/bin/landkarte`, `landkarte/lk/karte.py`, `landkarte/lk/scan.py`
- `landkarte/verteilen/RUECKMELDUNG.md` → `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/verteilen/einrichten.sh`, `landkarte/bin/landkarte`, `landkarte/lk/statistik.py`, `landkarte/lk/scan.py`
- `landkarte/lk/anweisung.py` → `landkarte/lk/aufgaben.py`, `landkarte/bin/landkarte`, `landkarte/bin/tresorwache`, `landkarte/hooks/tresorwache.sh`, `landkarte/lk/tresorwache.py`, `landkarte/lk/tresor.py`
- `landkarte/lk/konfig.py` → `landkarte/hooks/hooks.json`, `landkarte/bin/landkarte`, `landkarte/lk/statistik.py`, `README.md`, `landkarte/README.md`, `LICENSE`
- `landkarte/lk/testleser.py` → `landkarte/lk/suche.py`, `landkarte/lk/konfig.py`, `landkarte/lk/buch.py`, `landkarte/lk/regalwart.py`, `landkarte/bin/landkarte`, `landkarte/lk/karte.py`
- `landkarte/verteilen/AGENTS.md` → `landkarte/lk/scan.py`, `landkarte/bin/brainbook`, `landkarte/commands/brainbook.md`, `landkarte/lk/brainbook.py`, `landkarte/bin/landkarte`, `landkarte/lk/anweisung.py`
- `landkarte/lk/scan.py` → `landkarte/lk/sprachen.py`, `README.md`, `landkarte/README.md`, `landkarte/bin/landkarte`, `landkarte/lk/konfig.py`

## Offene Punkte

**Markierungen im Code**

- `landkarte/README.md:152` OFFEN: lassen, nicht raten |
- `landkarte/README.md:230` OFFEN: ]
- `landkarte/lk/anweisung.py:129` OFFEN: .md`, `TODO.md`, unerledigten `- [ ]`-Haken und
- `landkarte/lk/aufgaben.py:3` OFFEN: .md`, als
- `landkarte/lk/aufgaben.py:4` TODO: im Code
- `landkarte/lk/aufgaben.py:20` OFFEN: ist; ein eingetragener
- `landkarte/lk/aufgaben.py:37` TODO: mitten im Code ist eine Notiz an den naechsten Leser, keine Aufgabe.
- `landkarte/lk/aufgaben.py:39` OFFEN: .md", "TODO.md", "AUFGABEN.md", "OPEN.md",
- `landkarte/lk/aufgaben.py:40` OFFEN: .md", "docs/TODO.md", "docs/AUFGABEN.md",
- `landkarte/lk/aufgaben.py:46` OFFEN: bezeichnen. Genommen wird ab dem Fund,
- `landkarte/lk/aufgaben.py:49` OFFEN: |offen:|zu tun:|to ?do:|nicht erledigt|"
- `landkarte/lk/aufgaben.py:58` OFFEN: |TODO|AUFGABEN|OPEN)\.md$")
- `landkarte/lk/aufgaben.py:65` OFFEN: )\s*[:\-]\s*", "", text.strip())
- `landkarte/lk/aufgaben.py:92` OFFEN: .md` steht der Punkt in der Spalte nach der laufenden Nummer.
- `landkarte/lk/aufgaben.py:141` OFFEN: |zu tun|to ?do)\s*:\s*", "", rest)
- `landkarte/lk/aufgaben.py:152` WICHTIG: |kritisch|sofort)\b", text)),
- `landkarte/lk/aufgaben.py:287` OFFEN: .")
- `landkarte/lk/aufseher.py:449` OFFEN: [{v['schwere']}] {v.get('kapitel')}: "
- `landkarte/lk/buch.py:60` OFFEN: 
- `landkarte/lk/buch.py:356` OFFEN: "] = _punkte(k["abschnitte"].get("Offen", []))
- `landkarte/lk/cli.py:169` OFFEN: ": "Offen"}.get(args.art.lower(), "Fallen")
- `landkarte/lk/cli.py:208` OFFEN: chronik.kapitel_faellig(min_aufrufe=args.min_aufrufe)
- `landkarte/lk/cli.py:209` OFFEN: 
- `landkarte/lk/cli.py:212` OFFEN: )} Kapitel fällig.")
- `landkarte/lk/cli.py:213` OFFEN: [: args.grenze]:
- `landkarte/lk/cli.py:447` ACHTUNG: ähnlich: "
- `landkarte/lk/cli.py:584` ACHTUNG: Positionsvorliebe: "
- `landkarte/lk/cli.py:1005` OFFEN: s["offene_commits"]
- `landkarte/lk/cli.py:1006` OFFEN: )} Commit(s)")
- `landkarte/lk/cli.py:1007` OFFEN: [:12]:

