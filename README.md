# Brainbook & Landkarte

Projektgedächtnis für Menschen und KI-Assistenten. Es hält fest, **wo** etwas
liegt und **warum** es so ist — das Zweite ist das Teure, denn es steht in
keiner Datei. Es entsteht nur beim Arbeiten und ist nach zwei Wochen weg.

Reines Python aus der Standardbibliothek. Keine Fremdpakete, keine Cloud,
keine Konten. Es läuft ohne KI; die KI wird nur angewiesen, es zu benutzen.

## In einem Befehl einrichten

```sh
curl -fsSLO https://raw.githubusercontent.com/pvwerk/brainbook/main/landkarte/verteilen/brainbook-einrichten.py
python3 brainbook-einrichten.py
```

Die Datei enthält das ganze Werkzeug, packt es nach `~/brainbook`, verknüpft
die Befehle `landkarte` und `brainbook` und erkennt dann selbst, was möglich
ist: **mit Claude Code** wird das Plugin samt Hooks eingerichtet, **ohne** legt
sie die Anweisungsdatei für deine KI bereit und erklärt dir das Werkzeug direkt
im Terminal.

Mit Claude Code geht es auch nativ:

```sh
claude plugin marketplace add pvwerk/brainbook
claude plugin install landkarte@jan-werkzeuge
```

## Die Regel, auf der alles steht

Vor jeder Änderung an einem bestehenden Projekt wird **zuerst nachgeschlagen**
— nicht angefangen, den Code zu lesen. Ohne diese Regel bleibt die beste
Bibliothek ungenutzt stehen.

Die Einrichtung schreibt sie darum in die Anweisungsdatei deiner KI (bei
Claude Code `~/.claude/CLAUDE.md`, sonst eine Datei zum Vorlegen). Es wird
nichts überschrieben: der Abschnitt steht zwischen zwei Markierungen, und
ein zweites Einrichten ersetzt nur ihn.

Und damit sie nicht nur dasteht, gibt es einen **Platzanweiser**. Er steht am
Eingang und hält eine KI an, die ins Regal greift, ohne ins Verzeichnis
gesehen zu haben — aber er hält sie nicht auf: die Auskunft kommt gleich mit.

```
Angehalten vom Platzanweiser: in diesem Projekt wurde in dieser Sitzung
noch nicht im Verzeichnis nachgesehen, und es gibt eines.

Regal: PVWERK-CRM — ~/Desktop/PVWERK-CRM

Seite api/mahnwesen/freigabe.js:
  Zweck: Ja/Nein zu einer vorgemerkten Mahnung
  Darin: getDb:18

Inhaltsverzeichnis zu "freigabe":
  funktion  ~/Desktop/PVWERK-CRM/src/lib/protocolApproval.js:32  istFreigabepflichtig
  tabelle   ~/Desktop/.../20261108c_mahnung_freigaben.sql:21     mahnung_freigaben
```

Alles darin stammt aus dem Verzeichnis — es wurde keine Datei gelesen.

Drei Regeln, die ihn erträglich machen:

- **Höchstens einmal je Projekt und Sitzung.** Ein Wächter, der dauernd
  blockiert, wird abgeschaltet — und wirkt dann nie.
- **Nur wo es auch eine Auskunft gibt.** Ohne Inhaltsverzeichnis schweigt er.
- **Jeder Fehler endet in Durchlassen.** Ein kaputter Wächter darf keine
  Sitzung lahmlegen.

Danach schweigt er und reicht zu jeder neuen Datei nur noch den
Verzeichniseintrag nach — Zweck und Symbole mit Zeilennummern, die eine KI
sonst durch Lesen erarbeiten müsste.

```sh
landkarte wache            # Stand: nachgeschlagen? wer wurde angehalten?
landkarte wache <datei>    # von Hand befragen
landkarte wache --aus      # abschalten
landkarte anweisung        # die Regel (neu) einhängen
```

Das Anhalten braucht Hooks und geht daher nur mit Claude Code. Bei ChatGPT und
Grok steht die Regel in der Anweisungsdatei — mehr ist dort technisch nicht
möglich, weil die KI auf dem Rechner nichts ausführen kann.

## Aktualisieren

Welche Fassung bei dir liegt:

```sh
landkarte --fassung
```

Was neu ist, steht in [AENDERUNGEN.md](AENDERUNGEN.md). Eine neuere Fassung
holst du so:

```sh
claude plugin update landkarte@jan-werkzeuge      # mit Claude Code
```

Ohne Claude Code lädst du die Einzeldatei neu herunter und führst sie erneut
aus — sie überschreibt das Werkzeug, lässt aber alles Geschriebene stehen:
Chronik, Kapitel, Notizen, Brainbook und Protokoll liegen in `~/.landkarte`
und werden nie angefasst.

Hier wird **nicht** laufend ins Repository geschrieben. Veröffentlicht werden
nur benannte Fassungen, die vorher jede Prüfung bestanden haben — unter anderem
eine echte Installation in einem Wegwerf-Verzeichnis. So lässt sich sagen,
welcher Stand bei wem liegt, und ein Fehler vermehrt sich nicht still bei
allen.

## Was es tut

Je Projekt entsteht ein Inhaltsverzeichnis `KARTE.md` mit vier Teilen:

| Teil | Inhalt |
|---|---|
| **Spickzettel** | die Befehle, Adressen und Zugänge-Zeiger des Projekts |
| **Fallen** | wo schon Zeit verloren ging, und warum |
| **Wo liegt was** | jede Datei mit einem Satz, wofür sie da ist |
| **Symbole** | Funktionen und Klassen mit Zeilennummer |

Gesucht wird **dreistufig**, damit man nicht im falschen Projekt nachsieht:

```
landkarte wo "rechnung"
  LISTE 1 — Regal    welches Projekt   [PVWERK] PVWERK-CRM  ← du arbeitest hier
  LISTE 2 — Fach     welcher Teil      src/ (813 Dateien, 5530 Symbole) ← 66 Treffer
  LISTE 3 — Inhalt   die Stelle        migration_rechnungen.sql:47  funktion generate_rechnung_number
```

Ähnlich benannte Projekte — `etm-website` gegen `etm-gutachten` — werden
gegenseitig als Verwechslungsgefahr vermerkt.

## Das Brainbook

Dein eigenes Buch. Es steht in **keinem Regal und in keiner Liste**, wird nicht
gescannt und nicht geprüft. Es übersetzt deine Worte in Orte der Ablage:

```sh
landkarte merke "ETM CRM" --ist etm-gutachten --auch "Mängelaufnahme" \
  --was "Werkzeug, mit dem ich meine Gutachten schreibe"
```

Danach findet `landkarte wo "ETM CRM"` den Ordner `etm-gutachten` — auch wenn
du gerade in einem anderen Projekt stehst. Darin stehen nur Verweise, keine
Inhalte.

## Sieben Teile, drei mit Sprachmodell

| Teil | Aufgabe | Besetzung |
|---|---|---|
| **Chronist** | schreibt jeden Werkzeugaufruf mit | Hook + `jq`, 2 ms, 0 Token |
| **Schreiber** | macht aus einer Sitzung ein Buchkapitel | zwei unabhängige Agenten + Schiedsrichter |
| **Setzer** | baut `KARTE.md` | Skript |
| **Regalwart** | beschriftet Regale, warnt vor Verwechslung | Skript |
| **Bibliothekar** | sortiert nach **echter** Nutzung aus der Chronik | Skript |
| **Testleser** | Rückwärtssuche: kennt die Antwort, sucht die Frage | Skript + Agent |
| **Brainbook** | deine Worte → Orte in der Ablage | von Hand |

Mitschreiben, zählen und sortieren ist Rechnen, nicht Denken — das macht ein
Skript in Millisekunden, deterministisch, und baut es jederzeit identisch neu.

## Absicherung gegen eigene Fehler

Redundanz hilft nur gegen **unabhängige** Fehler. Zwei Kopien desselben
Skripts über dieselbe Eingabe liefern denselben Fehler; so ein Vergleich kann
nie anschlagen und erzeugt falsches Vertrauen. Deshalb an jeder Stelle die
passende Absicherung:

- **Chronist** — kein Zwilling, sondern eine Gegenprobe gegen das
  Sitzungsprotokoll, das Claude Code selbst schreibt. Anderer Code, anderer
  Weg, Vergleich je `tool_use_id`.
- **Schreiber und Aufseher** — echte Zwillinge, zwei getrennte Prozesse, die
  sich nicht sehen. Die Reihenfolge wird vor dem Schiedsspruch **zufällig
  vertauscht**, weil Modelle die erste Position bevorzugen.
- **Setzer und Bibliothekar** — Zusicherungen statt Kopien: steht jede Falle
  auch in der Karte, hat jedes Regal ein Verzeichnis, ist kein Zugangsdatum
  durchgerutscht.
- **Testleser** — das Modell wird nicht gefragt, *ob* das Verzeichnis gut ist.
  Es nennt nur Suchbegriffe zu einem Kapitel, dann schlägt das Verzeichnis
  wirklich nach. Eine Frage, die ins Leere läuft, ist ein **Beweis**.

Bei zwei Stimmen ist nicht abstimmbar. Widersprechen sie sich, entscheidet der
Schiedsrichter **am Rohprotokoll** — das deshalb von keinem Teil verändert
wird, nur angehängt.

## Selbstprotokoll — kontextlos

Damit mehrere Leute mit verschiedenen KIs Fehler finden können, protokolliert
das Werkzeug **sich selbst**. Kontextlos schon beim Schreiben, nicht erst beim
Export — darum ist auch das Rohprotokoll harmlos.

Festgehalten wird die **Art**: welcher Befehl, welche Größenklassen und
Sprachen, welche Fehlerklasse an welcher Stelle im **eigenen** Code, wie oft.
Fehlermeldungen werden auf ihr Muster zurückgeführt — aus
`KeyError: 'vorlage/layout.html'` wird `KeyError: <text>`.

Nicht festgehalten wird das **Woran**: keine Projektnamen, keine Pfade, keine
Inhalte, keine Suchbegriffe, keine Notizen.

```sh
brainbook stats --roh                # jede Rohzeile einzeln prüfen
brainbook stats --export ~/Desktop   # Datei zum Verschicken
landkarte einrichten --statistik-aus # ganz abschalten
```

## Mehr

- [Startseite für neue Nutzer](landkarte/verteilen/START-HIER.md)
- [Anweisung für KI-Assistenten](landkarte/verteilen/AGENTS.md) — KI-neutral
- [ChatGPT](landkarte/verteilen/fuer-chatgpt.md) · [Grok](landkarte/verteilen/fuer-grok.md) · [Claude Code](landkarte/verteilen/fuer-claude-code.md)
- [Was das Werkzeug im Einzelnen kann](landkarte/README.md)
- [Wie Rückmeldungen helfen](landkarte/verteilen/RUECKMELDUNG.md)
- [Was sich je Fassung geändert hat](AENDERUNGEN.md)

MIT-Lizenz.
