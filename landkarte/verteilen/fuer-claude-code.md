# Für André — Claude Code

Du bekommst die volle Fassung: der Chronist schreibt automatisch mit, und am
Sitzungsende entstehen von selbst Buchkapitel.

## Einrichten

```sh
./verteilen/einrichten.sh                     # fragt Name und KI ab
claude plugin marketplace add <ordner>/..     # der Ordner ÜBER landkarte/
claude plugin install landkarte@jan-werkzeuge
```

Der Marktplatz ist der Ordner, der `landkarte/` enthält — dort liegt
`.claude-plugin/marketplace.json`.

Prüfen:

```sh
claude plugin list | grep -A3 landkarte       # muss "enabled" zeigen
landkarte status
```

## Was dann von selbst läuft

| Wann | Was |
|---|---|
| jeder Werkzeugaufruf | Chronist hängt eine Zeile an die Tageschronik (2 ms, 0 Token) |
| Sitzungsstart | Auszug des Projekts liegt im Kontext: Befehle, Fallen, wichtigste Dateien |
| Sitzungsende | zwei unabhängige Schreiber machen ein Buchkapitel, ein Schiedsrichter vergleicht sie |

Das kostet pro Sitzung drei Modellaufrufe, grob ein Cent.

## Rückwirkend füllen

Deine bisherigen Claude-Code-Sitzungen liegen schon auf der Platte:

```sh
landkarte nachtragen --tage 120    # Chronik aus den Sitzungsprotokollen
landkarte regal                    # alle Projekte kartografieren
landkarte kapitel --faellig --grenze 5   # erst fünf, dann schauen was es kostet
```

## Nachtlauf

```sh
landkarte dienst --zeigen          # erst ansehen
landkarte dienst --einbauen        # täglich 03:15 und montags 07:30
landkarte dienst --ausbauen        # wieder weg
```

Es schreibt zwei Dateien nach `~/Library/LaunchAgents`. Wenn dir das zu weit
geht, lass es — alles läuft auch von Hand.

## Rückmeldung an Jan

```sh
brainbook stats --roh                # erst selbst ansehen
brainbook stats --export ~/Desktop   # Datei zum Verschicken
```
