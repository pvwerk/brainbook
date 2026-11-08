# Rückmeldung — wie das Werkzeug besser wird

Das Werkzeug protokolliert **sich selbst**. Nicht, was du tust — was *es* tut.

## Was erfasst wird

Je Aufruf eine Zeile:

| Feld | Beispiel | wozu |
|---|---|---|
| Befehl | `wo`, `scan`, `notiz` | welche Teile überhaupt benutzt werden |
| Flaggen | `--projekt`, `--art` | welche Schalter jemand braucht |
| Rückgabewert | `0`, `1`, `70` | wie oft etwas fehlschlägt |
| Dauer | `32 ms` | wo es langsam ist |
| Zählwerte | `treffer: 3` | wie oft eine Suche ins Leere läuft |
| Absturzspur | `KeyError` + Zeilen | damit der Fehler zu finden ist |
| Umgebung | `darwin`, Python 3.12, `grok` | ob ein Fehler nur auf einem System auftritt |
| Projekt | `h7f3a2c1` | gesalzener Kurz-Hash, erkennt Wiederholung |

## Was NICHT erfasst wird

Projektnamen · Dateipfade · Dateiinhalte · Suchbegriffe · Notizen ·
Brainbook-Einträge · Zugangsdaten.

Pfade in Absturzspuren werden auf den Dateinamen gekürzt, der Heimordner wird
zu `~`, und erkannte Zugangsdaten werden durch `***` ersetzt. Das Salz für den
Projekt-Hash wird auf deinem Rechner erzeugt und verlässt ihn nie — aus dem
Hash lässt sich kein Name zurückrechnen.

## Selbst nachsehen, bevor du etwas schickst

```sh
brainbook stats          # die Zusammenfassung
brainbook stats --roh    # JEDE einzelne Rohzeile, ungefiltert
```

`--roh` zeigt genau das, was in der Exportdatei landet. Wenn dir etwas darin
nicht gefällt, schick es nicht — und sag Jan, welche Zeile dich gestört hat.
Das ist selbst schon eine brauchbare Rückmeldung.

## Schicken

```sh
brainbook stats --export ~/Desktop
```

Legt `brainbook-stats-<name>-<datum>.json` auf den Schreibtisch. Diese Datei
per Mail oder Messenger an Jan.

## Abschalten

```sh
landkarte einrichten --statistik-aus    # sammelt nichts mehr
landkarte einrichten --statistik-an     # wieder an
```

Die bisherigen Dateien liegen in `~/.landkarte/statistik/` und können gelöscht
werden, ohne dass etwas kaputtgeht.

## Was am meisten hilft

Die Zahlen zeigen, **wo** es hakt, aber nicht **warum**. Schreib einen Satz
dazu, wenn dir etwas auffiel:

- ein Befehl, den du gesucht und nicht gefunden hast
- eine Ausgabe, die du nicht verstanden hast
- ein Fall, in dem `landkarte wo` das Falsche gefunden hat
- etwas, das du erwartet hast und das es nicht gibt

Besonders wertvoll: die Zeile **„nach Fehlschlag oder Nulltreffer anders
versucht"** in `brainbook stats`. Jeder Eintrag dort ist eine Stelle, an der das
Werkzeug dich im Stich gelassen hat.
