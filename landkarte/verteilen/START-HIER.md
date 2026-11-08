# Landkarte & Brainbook — Startseite

Ein Werkzeug, das Projektwissen festhält: ein Inhaltsverzeichnis je Projekt,
einen Spickzettel mit den Befehlen, ein Protokoll der Fallen und ein eigenes
Buch für die Worte, die **du** benutzt.

Es ist **reines Python ohne Fremdpakete**. Es braucht keine KI, um zu laufen.
Die KI wird nur angewiesen, es zu benutzen.

## Was deine KI kann, und was nicht

| | Claude Code | ChatGPT / Grok (Browser) |
|---|---|---|
| Verzeichnis, Spickzettel, Suche, Brainbook | ja | ja |
| Notizen, Berichtigungen, Mindmap | ja | ja |
| Selbstprotokoll für Rückmeldungen | ja | ja |
| **Mitschreiben, was die KI tut** | automatisch | nein |
| **Kapitel am Sitzungsende** | automatisch | nein (von Hand möglich) |

Der Unterschied kommt daher, dass Claude Code auf dem Rechner mitläuft und bei
jedem Schritt einen Haken auslösen kann. Eine KI im Browser kann das nicht —
sie sieht deinen Rechner nicht.

**Das heißt nicht, dass es für dich weniger nützt.** Der größte Gewinn ist das
Verzeichnis und das Brainbook, und das funktioniert überall gleich.

## Einrichten — 2 Minuten

```sh
cd ~/Downloads/landkarte          # oder wohin du es entpackt hast
./verteilen/einrichten.sh
```

Das Skript prüft Python, legt die Ablage an, fragt nach deinem Namen und deiner
KI und baut das erste Verzeichnis.

## Dann weiter bei deiner KI

- **Claude Code** → [`fuer-claude-code.md`](fuer-claude-code.md)
- **ChatGPT** → [`fuer-chatgpt.md`](fuer-chatgpt.md)
- **Grok** → [`fuer-grok.md`](fuer-grok.md)
- eine andere (Codex, Cursor, Copilot, Aider …) → [`AGENTS.md`](AGENTS.md)

## Rückmeldung

Damit das Werkzeug besser wird, protokolliert es **sich selbst**: welcher
Befehl, wie lange, mit welchem Ergebnis, ob er fehlschlug. Nicht, was in deinen
Projekten steht.

```sh
brainbook stats                      # ansehen
brainbook stats --roh                # jede Rohzeile einzeln prüfen
brainbook stats --export ~/Desktop   # Datei zum Verschicken
```

Was drin steht: Befehlsnamen, Dauern, Fehlschläge, Abstürze, Betriebssystem,
Python-Fassung, welche KI. Was **nicht** drin steht: Projektnamen, Dateipfade,
Dateiinhalte, Suchbegriffe, Notizen. Pfade erscheinen nur als gesalzener
Kurz-Hash, dessen Salz deinen Rechner nie verlässt.

Nichts geht automatisch raus. Der Export ist ein eigener Befehl, und du kannst
die Datei vorher lesen. Ganz abschalten:

```sh
landkarte einrichten --statistik-aus
```

Details in [`RUECKMELDUNG.md`](RUECKMELDUNG.md).
