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
