# Für ChatGPT

ChatGPT im Browser sieht deinen Rechner nicht. Es kann also nicht selbst
mitschreiben. **Was trotzdem voll funktioniert:** das Inhaltsverzeichnis, der
Spickzettel, die dreistufige Suche, Notizen und das Brainbook. Du führst die
Befehle im Terminal aus, ChatGPT arbeitet mit der Ausgabe.

## 1. Einrichten

```sh
./verteilen/einrichten.sh
```

## 2. ChatGPT einmal beibringen, wie es geht

Lege ein **Projekt** an (linke Spalte → Projekte → Neu) und füge unter
*Anweisungen* den Inhalt von `AGENTS.md` ein. Dann gilt es für jede Unterhaltung
in diesem Projekt, und du musst es nie wieder einfügen.

Ohne Projekte geht es auch über *Einstellungen → Personalisierung →
Benutzerdefinierte Anweisungen*, dort reicht der Kurztext:

> Auf meinem Rechner liegt ein Werkzeug `landkarte`. Wenn ich nach Code oder
> einem Projekt frage, gib mir zuerst den passenden Befehl zum Kopieren
> (`landkarte wo "<begriff>"`, `landkarte zeig`, `landkarte symbole <datei>`)
> und arbeite dann mit meiner eingefügten Ausgabe. Wenn ich ein eigenes Wort
> für etwas präge, gib mir den Befehl `landkarte merke "<wort>" --ist <projekt>`.
> Wenn ich an etwas lange hänge, erinnere mich an
> `landkarte notiz "<was überrascht hat>"`.

## 3. Der Ablauf im Alltag

Am Anfang eines Themas:

```sh
landkarte zeig          # Inhaltsverzeichnis des Projekts → in den Chat einfügen
```

Wenn du etwas suchst:

```sh
landkarte wo "rechnung" # drei Listen: Projekt → Teil → Datei:Zeile
```

Nur die Stelle einfügen, die du brauchst — nicht die ganze Datei. Genau das ist
der Gewinn: 30 Zeilen statt 3000.

Wenn etwas lange gedauert hat:

```sh
landkarte notiz "Panel zeigt den falschen Pfad an, richtig ist /mnt/web206/..."
```

## 4. Kapitel von Hand

Du hast keinen automatischen Chronisten. Du kannst ein Kapitel aber selbst
schreiben lassen: lass ChatGPT zusammenfassen, was heute passiert ist, und
übernimm die Punkte als Notizen:

```sh
landkarte notiz --art regel "<Regel aus der Zusammenfassung>"
landkarte notiz --art offen "<was offen blieb>"
```

Das landet im Verzeichnis und steht beim nächsten Mal wieder da.

## 5. Rückmeldung an Jan

```sh
brainbook stats --roh                # erst selbst ansehen
brainbook stats --export ~/Desktop
```
