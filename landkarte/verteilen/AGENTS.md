# Anweisung für KI-Assistenten: Landkarte & Brainbook

<!-- landkarte:anfang - von `landkarte anweisung` gepflegt -->

## Projektgedächtnis zuerst (Priorität 1)

Wenn an einem **bestehenden Projekt** etwas angepasst oder geändert werden
soll, wird **zuerst** im Brainbook und in der Bibliothek nachgesehen, wo die
Sache liegt. Nicht anfangen, den Code zu lesen.

```sh
landkarte wo <begriff>      # Regal → Buch → Seite, also Projekt → Teil → Datei:Zeile
```

`<begriff>` darf alles sein: das eigene Wort dafür („ETM CRM"), ein
Dateiname, ein Funktionsname, eine Tabelle, ein Thema. Das Brainbook
übersetzt eigene Begriffe in Projektnamen, deshalb funktioniert auch, was
nirgends im Code steht.

Erst wenn das nichts hergibt, wird gesucht und gelesen. Was dabei auffällt,
gehört zurück in die Bibliothek — sonst muss es beim nächsten Mal wieder
erarbeitet werden:

```sh
landkarte notiz "Falle: ..." --art falle
landkarte merke "<mein Wort>" --ist <projektordner>
```

**Warum:** Code jedes Mal neu zu lesen kostet jedes Mal von vorn — bei einem
gewachsenen Projekt sind das Minuten bis Stunden, und das Gelesene ist nach
der Sitzung wieder weg. Das Verzeichnis beantwortet dieselbe Frage in
Sekunden und wird mit jeder Nutzung genauer.

### Sag jedes Mal, ob die Bibliothek etwas hergab

Bei **jeder** Anfrage beginnt die Antwort mit einer dieser Zeilen — so ist auf
den ersten Blick zu sehen, ob die Bibliothek benutzt wurde und ob sie etwas
wusste:

```
bb false                  nichts in der Bibliothek gefunden
bb true 7 Einträge        7 Fundstellen gefunden und benutzt
```

Die Zahl wird nicht geschätzt. `landkarte bb <begriff>` schlägt nach **und**
gibt die Zeile fertig aus:

```sh
landkarte bb "mahnung"
→ bb true 19 Einträge
```

Steht da `bb false`, ist das ein Befund und keine Panne: die Bibliothek hat
eine Lücke. Was dann erarbeitet wird, gehört mit `landkarte notiz` oder
`landkarte merke` hinein, damit beim nächsten Mal `bb true` dasteht.

### Nach einer langen Aufgabe: Bilanz

Am Ende einer längeren Aufgabe kommt eine Zeile dazu — wie oft die Bibliothek
in dieser Sitzung überhaupt etwas geliefert hat:

```sh
landkarte bb --bilanz
→ bb 12 uses
```

Gezählt werden ergiebige Abfragen, nachgereichte Verzeichniseinträge und die
Male, in denen der Platzanweiser angehalten und die Auskunft mitgegeben hat.

<!-- landkarte:ende -->

Diese Datei ist KI-neutral. Sie funktioniert für Codex, Cursor, Copilot, Aider
und als Text, den man ChatGPT oder Grok einmal einfügt.

Auf diesem Rechner liegt ein Werkzeug namens `landkarte` (zweiter Einstieg:
`brainbook`). Es ist das Projektgedächtnis. **Benutze es, bevor du Dateien
liest.**

## Beim ersten Mal: erklären

Hat der Mensch noch nie mit dir über dieses Werkzeug gesprochen, erkläre ihm
zuerst in höchstens zehn Zeilen und in eigenen Worten:

1. **Was es kann** — je Projekt ein Inhaltsverzeichnis mit Spickzettel
   (Befehle, Adressen), Fallenprotokoll, einer Zeile Zweck je Datei und den
   Symbolen mit Zeilennummern.
2. **Wie gesucht wird** — `landkarte wo "<begriff>"` antwortet dreistufig:
   welches Projekt, welcher Teil, welche Datei und Zeile.
3. **Was von selbst passiert** — bei Claude Code schreibt ein Chronist mit und
   am Sitzungsende entstehen Buchkapitel; ohne Claude Code nichts, aber alles
   von Hand.
4. **Wie er eingreift** — `landkarte notiz`, `landkarte korrigieren`,
   `.landkarte/notizen.md` (seine Datei, wird nie überschrieben),
   `.landkarte/ignorieren.txt`. Erzeugtes wie `KARTE.md` wird bei jedem Scan
   neu gebaut, dort hineinschreiben lohnt nicht.
5. **Das Brainbook** — sein eigenes Buch, in keinem Regal und keiner Liste; es
   übersetzt seine Worte in Orte der Ablage.

Den vollen Text liefert `landkarte vorstellen`. Danach nicht wiederholen.

## Wenn du Befehle auf diesem Rechner ausführen kannst

```sh
landkarte wo "<begriff>"     # DREISTUFIG: welches Projekt → welcher Teil → Datei:Zeile
landkarte zeig               # Inhaltsverzeichnis des Projekts hier (KARTE.md)
landkarte finde "<begriff>"  # flache Suche über alle Projekte
landkarte symbole <datei>    # Funktionen und Klassen einer Datei mit Zeilennummern
landkarte scan               # Verzeichnis neu bauen, nach größeren Änderungen
```

`landkarte wo` ist der Normalfall. Es liest einen Index und ist fast immer
schneller als den Dateibaum zu durchsuchen.

## Wenn du keine Befehle ausführen kannst (KI im Browser)

Dann bitte den Menschen, den Befehl auszuführen und die Ausgabe einzufügen.
Formuliere das kurz und gib den Befehl fertig zum Kopieren:

> Führe bitte aus und füge die Ausgabe ein: `landkarte wo "rechnung"`

Bitte am Anfang eines neuen Themas einmal um:

> `landkarte zeig` — damit ich das Inhaltsverzeichnis des Projekts kenne

## Pflicht: Wissen festhalten

**Sobald etwas länger gedauert hat als es hätte dürfen, ist das eine Falle.**
Halte sie sofort fest, nicht am Ende — bis dahin ist der Grund vergessen.

```sh
landkarte notiz "<was überrascht hat und warum>"
landkarte notiz --art regel "<was man beim nächsten Mal von Anfang an tun muss>"
landkarte notiz --art zugang "<WO die Zugangsdaten liegen — niemals die Daten selbst>"
landkarte notiz --art offen "<was unfertig blieb>"
```

Stellt sich gespeichertes Wissen später als falsch heraus, **nie den alten Text
ändern**, sondern berichtigen:

```sh
landkarte korrigieren "<falsche Aussage>" "<richtige Aussage>" --grund "<warum>"
```

## Das Brainbook geht vor

Menschen haben eigene Worte für ihre Projekte. „ETM CRM" kann ein Ordner
namens `etm-gutachten` sein. Diese Übersetzung steht im Brainbook, das in
keinem Regal und keiner Liste geführt wird.

Benutzt der Mensch eines seiner Worte: `landkarte wo "<wort>"` sieht dort von
selbst zuerst nach. Nur den Eintrag zeigen: `brainbook "<wort>"`.

**Prägt der Mensch ein neues Wort** („speicher das als X", „nenn das ab jetzt
Y"), trage es sofort ein:

```sh
landkarte merke "X" --ist <projektordner> --auch "<synonym>" \
  --was "<ein Satz: was ist das>" --notiz "<kurznotiz>"
```

Dort stehen **nur Verweise** — keine Inhalte, keine Zugangsdaten.

## Grenzen, die du kennen musst

- Symbole: Python exakt über den Syntaxbaum. Andere Sprachen über Textregeln —
  oberste Ebene zuverlässig, Verschachteltes nicht.
- Findet `landkarte wo` nichts, ist das Verzeichnis veraltet → `landkarte regal`.
- Keine Passwörter in Notizen oder im Brainbook. Nur Zeiger darauf.
- Das Werkzeug protokolliert seine eigene Benutzung lokal, damit Fehler
  gefunden werden können. Es verschickt nichts von selbst.
