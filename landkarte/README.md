# Landkarte

Projektgedächtnis über Sitzungen hinweg: Inhaltsverzeichnis, Spickzettel,
Fallenprotokoll, Buch und Mindmap — für jedes Projekt und über alle Projekte.

Das Problem, das es löst: wer ein Projekt nach Wochen wiederaufnimmt, weiß
nicht mehr, *wo* etwas liegt und *warum* es so ist. Das Zweite ist das Teure.
Es steht in keiner Datei, weil es nur beim Arbeiten entsteht.

## Fünf Rollen

| Rolle | Aufgabe | Besetzung | Takt |
|---|---|---|---|
| **Chronist** | schreibt jeden Werkzeugaufruf mit | Hook + `jq`, 2 ms | jeder Aufruf |
| **Schreiber** | macht aus einer Sitzung ein Buchkapitel | 2 unabhängige Agenten + Schiedsrichter | je Sitzung |
| **Setzer** | baut `KARTE.md` je Projekt | Skript, < 1 s | bei Bedarf |
| **Regalwart** | beschriftet und gruppiert die Regale, erkennt neue, warnt vor Verwechslung | Skript | mit dem Regal |
| **Bibliothekar** | baut das Regal, sortiert nach echter Nutzung | Skript | nächtlich |
| **Testleser** | Rückwärtssuche: kennt die Antwort, sucht die Frage | Skript + Agent | nächtlich, stichprobenartig |
| **Brainbook** | Jans Worte → Orte in der Ablage; am Tresen, in keiner Liste | von Hand, `landkarte merke` | wenn Jan ein Wort prägt |
| **Aufseher** | findet Muster, benennt Schwachstellen, schlägt vor | Skript + Agent | wöchentlich |

## Der Testleser — Rückwärtssuche

Er nimmt stichprobenartig ein Kapitel, liest es ganz, und prüft, ob das
Verzeichnis darauf schließen lässt, was darin steht. Er **kennt die Antwort
und sucht die Frage.**

Der entscheidende Griff: das Modell wird nicht gefragt, ob das Verzeichnis gut
ist — das wäre eine Meinung. Es sagt nur, *wonach jemand suchen würde*, um
dieses Kapitel wiederzufinden. Dann schlägt das Verzeichnis wirklich nach:

```
landkarte lesung
  NEIN  Eturnity-Auslegung                 0 Treffer
  ja    print_helper.py                    4 Treffer (direkt aufs Kapitel)
  ja    user:mcp_servers                   1 Treffer (direkt aufs Kapitel)
  NEIN  Dymo-Etikettendruck                0 Treffer
  → 2 Begriffe ergänzt, 2 davon nachweislich jetzt auffindbar
```

Eine Frage, die ins Leere läuft, ist ein **Beweis**, keine Einschätzung. Und
nach der Korrektur wird dieselbe Frage erneut gestellt — findet sie jetzt, ist
die Korrektur belegt. `landkarte lesung --bilanz` zeigt die gemessene
Trefferquote des Verzeichnisses.

### Was er selbst richtet und was nicht

| Befund | Umgang | Warum |
|---|---|---|
| Schlagworte fehlen | trägt er nach | nur ergänzend, rückbaubar, Wirkung messbar |
| Regal falsch beschriftet, Alias fehlt | trägt er nach | reines Etikett, keine Inhalte |
| Buch im **falschen Regal** | nur bei eindeutigem Befund (≥ 80 % der Dateien), sonst Vorschlag im Journal | ändert zwei Projekte |
| Kapiteltext falsch | **nie** | das Kapitel ist Beweismittel des Schiedsrichters |

Einen Alias übernimmt er nur, wenn er keinem anderen Regal gehört — sonst
entstünde genau die Verwechslung, die er verhindern soll. Maschinelle
Schlagworte stehen in `.landkarte/schlagworte.md`; `notizen.md` bleibt dem
Menschen.

## Das Brainbook — am Tresen, in keiner Liste

Jans eigenes Buch. Es steht in **keinem Regal und in keiner Liste**, wird nicht
gescannt, nicht sortiert, nicht vom Testleser geprüft und erscheint nicht im
Regal. Es liegt beim Bibliothekar am Tresen: `~/.landkarte/brainbook.md`.

Darin stehen **nur Verweise** — links ein Wort, wie Jan es sagt, rechts der Ort
in der Ablage. Es ist das Übersetzungsbuch von seinem Gedächtnis in diese
Bibliothek:

```sh
landkarte merke "ETM CRM" --ist etm-gutachten \
  --auch "Mängelaufnahme" --auch "Gutachter-Tool" \
  --was "Werkzeug, mit dem ich meine PV-Gutachten schreibe" \
  --notiz "löst das alte Tool auf der Synology ab"
```

```
ETM CRM
   auch: Mängelaufnahme, Gutachter-Tool, ETM-Tool
   was: Werkzeug, mit dem ich meine PV-Gutachten schreibe
   Regal: etm-gutachten  ~/Projekte/etm-gutachten
   Kategorien: ETM
   → ~/Projekte/etm-gutachten/KARTE.md
   Notiz: löst das alte Mängelaufnahme-Tool auf der Synology (Port 4100) ab
```

`landkarte wo "ETM CRM"` sieht **zuerst** hier nach — Jans Wort zählt mehr als
jeder Ordnername. Übernommen wird nur, was belegt ist: Regal und Pfade aus dem
Verzeichnis, die Gruppe als Kategorie. Ordnernamen wie `app/` oder `tests/`
kommen nicht hinein; die stehen in Liste 2. Beim Sitzungsstart liegen die
Stichworte im Kontext, damit ein Wort wie „Unser Betriebssystem" sofort sitzt.

Das Verzeichnis zum Brainbook hat Jan selbst — deshalb ist es eine einzige, von
Hand lesbare Datei. `landkarte pruefen` prüft nur zwei Dinge daran: keine
Zugangsdaten, keine toten Verweise.

## Drei Listen

Nachschlagen geht dreistufig, damit man nicht im falschen Projekt sucht:

```
landkarte wo "rechnung"
  LISTE 1 — Regal    welches Projekt   (Name, Aliase, Gruppe, Inhaltstreffer)
  LISTE 2 — Fach     welcher Teil      (src/, api/, supabase/ …)
  LISTE 3 — Inhalt   die genaue Stelle (Datei:Zeile, Symbolart)
```

Liste 1 entsteht aus zwei Quellen: dem Namen des Regals **und** seinem Inhalt.
Nur über den Namen zu gehen würde bedeuten, dass man nur findet, wessen Regal
man schon kennt. Ähnlich benannte Projekte — `PVWERK-CRM` gegen
`PVWERK-CRM-tablet-app`, `etm-website` gegen `etm-gutachten` — werden
gegenseitig als Verwechslungsgefahr vermerkt und im Auszug genannt.

Nur zwei Rollen brauchen ein Sprachmodell. Mitschreiben, zählen und sortieren
ist Rechnen: ein Skript macht das in Millisekunden, deterministisch, und baut
es jederzeit identisch neu.

## Absicherung gegen eigene Fehler

Redundanz hilft nur gegen **unabhängige** Fehler. Zwei Kopien desselben Skripts
über dieselbe Eingabe liefern denselben Fehler — ein Vergleich davon kann nie
anschlagen und erzeugt falsches Vertrauen. Deshalb an jeder Stelle die passende
Absicherung:

- **Chronist** — kein Zwilling, sondern eine Gegenprobe gegen das
  Sitzungsprotokoll, das Claude Code selbst schreibt: anderer Code, anderer
  Weg. Verglichen wird über die `tool_use_id`, Aufruf für Aufruf.
- **Schreiber und Aufseher** — echte Zwillinge, zwei getrennte Prozesse, die
  sich nicht sehen. Hier sind die Fehler wirklich unabhängig, weil ein
  Sprachmodell etwas übersehen oder dazuerfinden kann.
- **Setzer und Bibliothekar** — Zusicherungen statt Kopien: taucht jede Falle
  aus jedem Kapitel auch in der Karte auf, hat jedes Projekt im Regal eine
  Karte, ist kein Zugangsdatum durchgerutscht.

Bei zwei Stimmen ist nicht abstimmbar. Widersprechen sie sich, entscheidet der
Schiedsrichter **am Rohprotokoll** — das deshalb von keiner Rolle verändert
wird, nur angehängt.

### Was mit der falschen Fassung passiert

Beide Schreiber sind derselbe Prompt in zwei Prozessen; nach dem Lauf existiert
keiner mehr. Es gibt also keinen Arbeiter zu korrigieren. Der Schiedsspruch ist
eine **Fehlermeldung gegen Anweisung oder Protokoll**, und die Art der
Abweichung sagt, gegen welche:

| Art | Ursache | Korrektur |
|---|---|---|
| `erfindung` | Anweisung zu lasch, Protokoll zu dünn | `lk/buch.py: ANWEISUNG` |
| `auslassung` | Protokoll stellt die Stelle schlecht dar | `lk/buch.py: bericht_text` |
| `fehldeutung` | Protokoll ist mehrdeutig | Feld in `hooks/chronist.sh` |
| `strittig` | Datenlage deckt die Frage nicht | offen lassen, nicht raten |

Die Reihenfolge der beiden Fassungen wird vor dem Schiedsspruch **zufällig
vertauscht**, weil Modelle die erste Position bevorzugen. Entscheidet der
Schiedsrichter über die Zeit zu oft für dieselbe Position, meldet der Aufseher
das als schweren Befund — bei zufälliger Reihenfolge kann eine Schieflage keine
Wahrheit sein.

## Weitergeben

Eine einzige Datei richtet alles ein — sie enthält das Werkzeug, packt es nach
`~/brainbook` aus, verknüpft die Befehle und erkennt selbst, was möglich ist:

```sh
python3 brainbook-einrichten.py
```

- **Claude Code gefunden** → Plugin mit Hooks wird eingerichtet. Chronist
  schreibt mit, Kapitel entstehen am Sitzungsende, und beim ersten Start
  erklärt die KI selbst, was die Bibliothek kann.
- **kein Claude Code** → beste Alternative: `AGENTS.md` zum Einfügen in
  ChatGPT (Projekt → Anweisungen) oder Grok (Custom Instructions), plus der
  volle Erklärtext direkt im Terminal.

Gebaut wird die Datei mit `python3 verteilen/paket-bauen.py` — **nach jeder
Änderung am Werkzeug neu**, sonst veraltet sie. Alles Weitere in
[`verteilen/START-HIER.md`](verteilen/START-HIER.md).

## Erklärt sich selbst

```sh
landkarte vorstellen          # was es kann, wie es vorgeht, wie man eingreift
landkarte vorstellen --erneut # Merker löschen, KI erklärt es noch einmal
```

Beim allerersten Sitzungsstart legt der Hook eine Vorstellung in den Kontext,
damit die KI es dem Menschen in eigenen Worten erklärt — die fünf Punkte: was
es kann, wie gesucht wird, was von selbst passiert, wie man eingreift, und was
das Brainbook ist. Danach nie wieder.

## Selbstprotokoll — kontextlos

Das Werkzeug protokolliert **sich selbst**, damit mehrere Leute mit
verschiedenen KIs Fehler finden können. Es ist kontextlos **schon beim
Schreiben**, nicht erst beim Export — darum ist auch das Rohprotokoll harmlos
und `--roh` zeigt nichts anderes als die Exportdatei.

Festgehalten wird: welche **Art** von Aufgabe (der Befehl), welche **Art** von
Struktur (Größenklassen, Sprachen, mit oder ohne Git), welche Fehlerklasse an
welcher Stelle im **eigenen** Code, und wie oft. Fehlermeldungen werden auf ihr
Muster zurückgeführt: aus `KeyError: 'vorlage/layout.html'` wird
`KeyError: <text>`.

Nicht festgehalten wird, **woran**: keine Projektnamen, keine Dateipfade, keine
Inhalte, keine Suchbegriffe, keine Notizen.

```sh
brainbook stats                      # Zusammenfassung
brainbook stats --roh                # jede Rohzeile einzeln prüfen
brainbook stats --export ~/Desktop   # Datei zum Verschicken
landkarte einrichten --statistik-aus # ganz abschalten
```

Besonders brauchbar ist die Zeile **„nach Fehlschlag oder Nulltreffer anders
versucht"**: jeder Eintrag dort ist eine Stelle, an der das Werkzeug seinen
Benutzer im Stich gelassen hat.

## Befehle

```sh
landkarte einrichten                 # Ablage anlegen, nach ~/.local/bin verknüpfen
landkarte regal                      # alle Projekte scannen, Regal bauen
landkarte scan [pfad]                # ein Projekt, KARTE.md setzen
landkarte finde <begriff>            # Symbole, Dateien, Befehle, Fallen, Kapitel
landkarte symbole <datei>
landkarte zeig [pfad]                # KARTE.md ausgeben
landkarte digest [pfad]              # kompakter Auszug (nutzt der Hook)

landkarte notiz "..." [--art falle|regel|zugang|offen]
landkarte korrigieren "falsch" "richtig" [--grund ...]

landkarte kapitel --faellig [--einfach] [--trocken]
landkarte pruefen [pfad] [--sitzung ID]
landkarte abweichungen [--tage 120]
landkarte aufsicht [--ohne-modell] [--einfach] [--zeigen]

landkarte merke "<wort>" --ist <projekt> [--auch ...] [--was ...] [--notiz ...]
landkarte brainbook ["<wort>"]       # dein Buch zeigen oder nachschlagen

landkarte wo <begriff>               # dreistufig: Regal, Fach, Inhalt
landkarte regale [--faecher] [--journal]

landkarte lesung [--anzahl 3]        # Testleser: Rückwärtssuche auf Stichproben
landkarte lesung --bilanz            # gemessene Trefferquote des Verzeichnisses
landkarte protokoll [--ausfuehrlich] # Spruchbuch des Schiedsrichters
landkarte nachtragen [--tage 365]    # Chronik rückwirkend aus Sitzungsprotokollen
landkarte schwaerzen [--probe]       # Zugangsdaten aus der Chronik entfernen
landkarte dienst [--einbauen]        # nächtlicher und wöchentlicher Lauf (launchd)

landkarte mindmap [--oeffnen]        # eine HTML-Datei, offline, ohne CDN
landkarte mermaid
landkarte status
landkarte vorstellen                 # erklären, was es kann und wie man eingreift
landkarte stats [--roh] [--export]   # kontextloses Selbstprotokoll
```

## Was wohin geschrieben wird

```
~/.landkarte/
  konfig.json            Wurzeln, Ignorierliste, Modelle, Zwillingsschalter
  chronik/YYYY-MM-DD.jsonl   Rohprotokoll — nur angehängt, nie verändert
  sitzungen/<id>.json    welche Sitzung schon ein Kapitel hat
  pruefung/<sitzung>/<zeit>.md  Schiedsspruch je Lauf, nie überschrieben
  pruefung/protokoll.jsonl  Spruchbuch mit Fingerabdruck der Protokollfassung
  lesungen.jsonl         jede Lesung samt Messung vorher und nachher
  abweichungen.jsonl     Strichliste der Abweichungsarten
  projekte/<slug>.json   Suchindex je Projekt
  register.json          das Regal, maschinenlesbar
  brainbook.md           Jans Buch am Tresen — in keiner Liste, von Hand lesbar
  brainbook-eintragungen.jsonl  wann welches Stichwort dazukam, nur angehängt
  WERKSTATT.md           Befund und Vorschläge des Aufsehers
  befund.json            dieselben Messwerte maschinenlesbar

<projekt>/KARTE.md                 Inhaltsverzeichnis und Spickzettel (erzeugt)
<projekt>/.landkarte/notizen.md    handgepflegt, wird nie überschrieben
<projekt>/.landkarte/buch/*.md     die Kapitel
<projekt>/.landkarte/korrekturen.jsonl  Berichtigungen
<projekt>/.landkarte/schlagworte.md vom Testleser nachgetragene Suchbegriffe
<projekt>/.landkarte/symbole.md    vollständige Symbolliste
<projekt>/.landkarte/karte.json    Scan-Modell
<projekt>/.landkarte/mindmap.html  Mindmap
~/Projekte/LANDKARTE.md            das Regal, lesbar
```

## Grenzen

- **Symbole:** Python exakt über `ast`. Andere Sprachen über Textregeln: oberste
  Ebene zuverlässig, Verschachteltes und dynamisch Erzeugtes nicht. Bewusst so,
  damit das Werkzeug ohne Fremdpakete läuft; die Karte sagt es an der Stelle.
- **Verweise:** teils heuristisch (Dateinamen im Text) — ein Hinweis, kein Beweis.
- **Unteragenten:** ihre Werkzeugaufrufe lösen keine `PostToolUse`-Hooks der
  Hauptsitzung aus. Die Gegenprobe rechnet sie deshalb heraus.
- **Der Aufseher ändert nichts.** Er schlägt vor. Eingebaut wird von Hand.

## Zugangsdaten

Der Chronist schreibt Befehlszeilen mit. Darin stehen manchmal Passwörter —
etwa in einer Postgres-URL. Ungeschwärzt landeten sie in der Chronik, im
Werkstattbericht und in der Anfrage an das Modell. Deshalb wird an **drei
Stellen** geschwärzt: beim Schreiben im Hook, beim Nachtragen und noch einmal
beim Lesen. Die dritte Stelle ist die wichtigste, weil sie auch Dateien
abdeckt, die vorher entstanden sind.

Mustererkennung allein lässt immer etwas durch — ein Passwort ohne
Schlüsselwort in einer mehrfach shell-verschachtelten Zeile ist nicht
erkennbar. Deshalb gibt es eine zweite, unabhängige Linie: bekannte
Geheimnisse werden dort gelesen, wo sie ohnehin schon liegen
(`~/.claude/settings.local.json`, optional `~/.landkarte/geheimnisse.txt`) und
dann wörtlich ersetzt. Es entsteht keine neue Kopie.

`landkarte pruefen` schlägt Alarm, wenn in Karte, Buch oder Notizen etwas wie
ein Zugangsdatum aussieht. Die Prüfung ist bewusst streng gegen Fehlalarme:
ein Routen-Platzhalter wie `/d/:token: Label` darf nicht anschlagen, sonst
wird der Wächter ignoriert.

`landkarte schwaerzen` räumt bestehende Chronikdateien nachträglich auf. Das
ist die **einzige** Stelle, an der die Chronik umgeschrieben wird — ein
Passwort im Klartext wiegt schwerer als die Unveränderlichkeit. Die Urfassung
geht nach `~/.Papierkorb-Claude/`, nicht weg; dort liegt sie dann aber im
Klartext und sollte gelöscht werden, sobald sie nicht mehr gebraucht wird.

## Was ins Repository gehört

Mitnehmen: `KARTE.md`, `.landkarte/notizen.md`, `.landkarte/buch/`,
`.landkarte/korrekturen.jsonl`, `.landkarte/ignorieren.txt` — das ist
Handgeschriebenes und Erarbeitetes.

Ignorieren: `.landkarte/karte.json`, `.landkarte/symbole.md`,
`.landkarte/mindmap.html` — erzeugt und jederzeit neu baubar.

```gitignore
.landkarte/karte.json
.landkarte/symbole.md
.landkarte/mindmap.html
```

## Keine Fremdabhängigkeiten

Nur Python-Standardbibliothek, `jq` und `git`. Die Mindmap lädt nichts aus dem
Netz. Es verlässt nichts den Rechner außer den beiden Modellaufrufen für
Kapitel und Werkstattbericht.

## Entwickeln und freigeben

Geschrieben wird immer im Original — `~/Projekte/werkzeuge`. Dorthin zeigen
auch `~/.local/bin/landkarte` und `~/.local/bin/brainbook`, deshalb wirkt jede
Änderung sofort. **Diese Verknüpfung nie auf eine installierte Kopie umbiegen:**
man entwickelt sonst gegen die Kopie und wundert sich, dass nichts ankommt.

Nach GitHub geht nichts nebenbei. Eine Fassung wird benannt, geprüft und dann
geschoben:

```sh
landkarte freigabe                       # Stand: hier gegen GitHub
landkarte freigabe --pruefen             # alle Prüfungen, ändert nichts
landkarte freigabe --neu klein           # Probe: was würde passieren
landkarte freigabe --neu klein --jetzt --text "Freigabe mit Prüflauf"
```

`--neu fehler` zählt 1.1.0 auf 1.1.1, `--neu klein` auf 1.2.0, `--neu gross`
auf 2.0.0. Mit `--fassung 1.4.0` setzt man eine Nummer genau.

Mit `--jetzt` läuft genau diese Reihenfolge, und sie wird nicht umgestellt:

1. **prüfen** — ändert nichts; schlägt eine harte Prüfung fehl, bricht alles ab
2. **stempeln** — die Fassung an genau zwei Stellen: `plugin.json` und `lk/__init__.py`
3. **Paket bauen** — `brainbook-einrichten.py` neu, sonst verteilt man eine veraltete Datei
4. **AENDERUNGEN.md** — die Commits seit der letzten Markierung
5. **hochladen** — Commit, Markierung `vX.Y.Z`, `git push --follow-tags`

### Was geprüft wird

| Prüfung | Warum es sie gibt |
|---|---|
| Original, Ziel, Zweig | Freigeben nur aus dem Repository, nie aus einer installierten Kopie |
| Arbeitsbaum | Was nicht eingecheckt ist, ist auch nicht geprüft |
| Fassungsnummern | `plugin.json` und `lk/__init__.py` driften sonst auseinander |
| Syntax | Eine nicht übersetzbare Datei darf nie hinausgehen |
| Hilfe aller Befehle | Fängt ein zerbrochenes `argparse`, das sonst erst beim Nutzer auffällt |
| Keine Zugangsdaten | Das Repository ist öffentlich |
| Einzeldatei aktuell | Baut eine Probe in einen Wegwerfordner und vergleicht |
| Installation in Wegwerf-Heim | Packt die Einzeldatei mit eigenem `HOME` aus und führt sie aus |
| Prüfen bleibt folgenlos | Zählt die Einträge im echten Heimverzeichnis vorher und nachher |

Die Installationsprüfung prüft drei Fälle, die schon schiefgingen: `--help`
hat installiert statt zu helfen, ein Tippfehler im Schalter hat installiert,
und die ausgepackte Fassung lief nicht.

`--ohne-pruefung` ist der Notausgang. Wer ihn benutzt, schreibt in `--text`
hinein, warum.
