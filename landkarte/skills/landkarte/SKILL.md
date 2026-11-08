---
name: landkarte
description: Projektwissen nachschlagen und festhalten — Inhaltsverzeichnis, Spickzettel, Fallenprotokoll, Buch und Mindmap aller Projekte. Benutze dies, wenn du ein Projekt wiederaufnimmst und nicht weißt wo etwas liegt, wenn du suchst wo eine Funktion/ein Befehl/ein Zugang steckt, wenn du Zeit an einer Überraschung verloren hast (Falle festhalten), wenn sich gespeichertes Wissen als falsch erweist, oder wenn nach dem Zustand der Bibliothek, der Chronik, der Kapitel oder der Abweichungen gefragt wird.
---

# Landkarte

Das Werkzeug `landkarte` ist das Gedächtnis über Sitzungen hinweg. Es besteht aus
fünf Rollen, von denen nur zwei ein Sprachmodell brauchen:

| Rolle | Was sie tut | Besetzung |
|---|---|---|
| Chronist | schreibt jeden Werkzeugaufruf mit | Hook + jq, 0 Token |
| Schreiber | macht aus einer Sitzung ein Buchkapitel | 2 unabhängige Agenten + Schiedsrichter |
| Setzer | baut `KARTE.md` je Projekt | Skript |
| Bibliothekar | baut das Regal, sortiert nach echter Nutzung | Skript |
| Aufseher | findet Muster und Schwachstellen, schlägt vor | Skript + Agent, wöchentlich |

## Zuerst nachsehen, dann lesen

Beim Sitzungsstart liegt der Auszug des Projekts im Kontext: Befehle, Adressen,
Fallen, Regeln, die wichtigsten Dateien. **Lies ihn, bevor du Dateien öffnest.**

Wenn du etwas suchst, frag das Verzeichnis statt den Dateibaum zu durchkämmen:

```
landkarte wo <begriff>               # DREISTUFIG: Regal → Fach → genaue Stelle
landkarte finde <begriff>            # flache Suche über alles
landkarte finde <begriff> --projekt etm
landkarte symbole <datei>            # Symbole einer Datei mit Zeilennummern
landkarte zeig                       # KARTE.md des Projekts hier
landkarte scan [pfad]                # Karte neu setzen (nach größeren Änderungen)
```

**`landkarte wo` ist der Normalfall.** Es beantwortet in einem Aufruf drei
Fragen: welches Projekt, welcher Teil davon, welche Datei und Zeile. Das
verhindert den häufigsten Fehler — im falschen Projekt nachzusehen, weil
`PVWERK-CRM`, `PVWERK-CRM-tablet-app` und `pvwerk-ai-bridge` ähnlich heißen.
Der Auszug beim Sitzungsstart nennt die Verwechslungskandidaten ausdrücklich.

`landkarte finde` ist fast immer schneller als `grep` über den Baum, weil es den
Index liest. Wenn nichts gefunden wird, ist das Regal veraltet → `landkarte regal`.

## Wissen festhalten — das ist die Pflicht, nicht die Kür

Der Chronist hält fest, *was* passiert ist. Er kann nicht wissen, *warum* etwas
so ist. Dafür gibt es zwei Wege:

**Sofort, wenn du Zeit an einer Überraschung verloren hast:**

```
landkarte notiz "Webspace-Pfad im Strato-Panel ist falsch: angezeigt /mnt/rid/02/04/…, echt /mnt/web206/e1/04/…"
landkarte notiz --art regel "Bei Strato immer den echten Pfad per PHP-Probe prüfen, nie dem Panel glauben"
landkarte notiz --art zugang "SMTP-Daten in formular-config.php, nicht im Repo"
landkarte notiz --art offen "SPF und DMARC erst nach NS-Umstellung setzbar"
```

Die Regel: **sobald etwas länger gedauert hat als es hätte dürfen, ist das eine
Falle.** Nicht warten, bis die Sitzung vorbei ist — bis dahin ist der Grund
vergessen. Keine Passwörter, Token oder Schlüssel in Notizen, nur Zeiger darauf.

**Automatisch am Sitzungsende:** zwei Schreiber verarbeiten das Protokoll
unabhängig zu einem Kapitel, ein Schiedsrichter vergleicht sie am Protokoll.
Das passiert ohne dein Zutun.

## Wenn gespeichertes Wissen falsch ist

Nie das Kapitel oder das Rohprotokoll ändern — daran entscheidet der
Schiedsrichter Streitfälle. Stattdessen berichtigen:

```
landkarte korrigieren "Die Seite liegt nicht bei Strato" "Sie liegt beim Strato-Baukasten (CM4all)" --grund "onecdn.io führte in die Irre"
```

Das Original bleibt stehen, wird in Karte und Auszug durchgestrichen, und der
richtige Sachverhalt steht dahinter.

## Zustand prüfen

```
landkarte status          # Chronik, fällige Kapitel, Regal
landkarte pruefen         # Zusicherungen + Gegenprobe der Chronik gegen das Sitzungsprotokoll
landkarte abweichungen    # Strichliste: wo die beiden Schreiber auseinandergehen
landkarte protokoll       # Spruchbuch des Schiedsrichters, nach Protokollfassung
landkarte regale          # Regalbeschriftung: Gruppen, Aliase, Verwechslungsgefahr
landkarte schwaerzen      # Zugangsdaten aus der Chronik entfernen
landkarte aufsicht        # vollständiger Werkstattbericht (nutzt ein Modell)
landkarte mindmap --oeffnen
```

### Was eine Häufung bei `abweichungen` bedeutet

Beide Schreiber sind **derselbe Prompt in zwei Prozessen**. Eine Häufung ist
deshalb nie die Schuld eines Schreibers, sondern ein Mangel an der Anweisung
oder am Protokoll:

- viele `erfindung` → `lk/buch.py: ANWEISUNG` schärfen
- viele `auslassung` → Verdichtung in `lk/buch.py: bericht_text` verbessern
- viele `fehldeutung` → fehlendes Feld in `hooks/chronist.sh` nachrüsten
- `Positionsvorliebe` gemeldet → schwerer Befund, die Reihenfolge wird zufällig
  vertauscht, also kann eine Schieflage keine Wahrheit sein

## Grenzen, die du kennen musst

- Symbole: Python exakt über den Syntaxbaum. Andere Sprachen über Textregeln —
  oberste Ebene zuverlässig, Verschachteltes und dynamisch Erzeugtes nicht.
- Verweise im Graphen sind teils heuristisch (Dateinamen im Text), also ein
  Hinweis, kein Beweis.
- Der Aufseher ändert **nichts**. Er schreibt Vorschläge in
  `~/.landkarte/WERKSTATT.md`. Eingebaut wird von Hand.
- Zugangsdaten werden dreifach geschwärzt (Hook, Nachtrag, Lesen) plus wörtlich
  gegen bekannte Geheimnisse. Trotzdem: **keine Passwörter in Notizen**, nur
  Zeiger darauf.
- Der Schiedsspruch liegt unabhängig in `~/.landkarte/pruefung/protokoll.jsonl`
  (nur angehängt) und je Lauf als Bericht unter
  `~/.landkarte/pruefung/<sitzung>/<zeit>.md`. Er wird **vor** dem Kapitel
  geschrieben, damit die Beweislage nicht vom Erfolg des nächsten Schritts
  abhängt.
