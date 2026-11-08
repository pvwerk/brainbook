---
description: Brainbook und Landkarte — Stichwort nachschlagen, eintragen, Selbstprotokoll
argument-hint: [wort | stats | merke "<wort>" --ist <projekt>]
allowed-tools: Bash(landkarte *), Bash(brainbook *)
---

Führe `brainbook $ARGUMENTS` aus und zeige die Ausgabe.

Ohne Argument zeigt es Jans Brainbook: die Stichworte, unter denen er seine
Projekte anspricht, mit den Orten in der Ablage.

Nützliche Formen:

- `/brainbook` — das ganze Buch
- `/brainbook ETM CRM` — ein Stichwort nachschlagen
- `/brainbook stats` — Selbstprotokoll des Werkzeugs
- `/brainbook stats --export ~/Desktop` — Protokoll als Datei zum Verschicken
- `/brainbook merke "ETM CRM" --ist etm-gutachten --was "..."` — Stichwort eintragen

Prägt Jan im Gespräch ein neues Wort für etwas („speicher das als X"), trage es
unaufgefordert mit `merke` ein — das Brainbook ist die Übersetzung von seinen
Worten in die Ablage.
