# Notizen: werkzeuge

Diese Datei gehört dem Menschen (und Claude per `landkarte notiz`).
`landkarte` liest sie und baut sie in die KARTE.md ein, überschreibt sie aber
nie. Alles Handgeschriebene gehört hierher, nicht in die KARTE.md.

**Keine Passwörter, Token oder Schlüssel hier hinein.** Nur Zeiger darauf.

## Fallen

Wo schon Zeit verloren ging. Form: **kurze Benennung** — was passiert und warum.


- [2026-11-09] Marktplatz NIEMALS auf eine Kopie zeigen lassen. Zeigte am 08.11. auf ~/brainbook (eine Kopie aus einem Fehltest); Claude Code lud daraufhin eine eingefrorene 1.0.0 aus dem Zwischenspeicher, und neue Hooks wurden nie aktiv. Der Chronist schrieb trotzdem mit, weil seine Skripte ueber ~/.local/bin/landkarte liefen - deshalb fiel es wochenlang nicht auf. Pruefen mit: claude plugin list (Zeile 'Read from:' muss ~/Projekte/werkzeuge/landkarte sein).
- [2026-11-09] Verbindlich fuer 'was liegt draussen' ist die Markierung im Repository (git ls-remote --tags), nicht raw.githubusercontent.com - die Rohdatei kommt aus einem Zwischenspeicher und laeuft nach dem Schieben einige Minuten nach. Fassungen nach Nummern vergleichen, nicht als Text.
- [2026-11-09] Eine Geheimnis-Erkennung muss zwei Scharfstellungen haben, sonst zerstoert sie den Verlauf. Im Chat darf sie raten, beim Rundgang ueber Protokolle nur bei eindeutigen Formen (sk-ant-, ghp_, AKIA, JWT, URL-Anmeldung, bestimmte Umgebungsvariablen). Mit lockeren Regeln fand sie am 09.11.2026 in einem Protokoll 155 'Geheimnisse' und haette 12788 Stellen ueberschrieben: UUIDs, Zeitstempel und das Wort 'passwort', das in deutschsprachigem Code ueberall steht. Nach dem Verschaerfen 8 echte Werte. Weitere Einzelfallen: Hochkommata um PGPASSWORD werden mitgefangen; Shell-Verweise und bereits Geschwaerztes sind Platzhalter; ein Codefragment ging als AWS-Schluessel durch; AWS-Schluessel enthalten Schraegstriche und fielen dem Pfadfilter zum Opfer.
## Regeln

Was man beim nächsten Mal von Anfang an richtig machen muss.


- [2026-11-09] Freigabe: nie von Hand pushen. 'landkarte freigabe --pruefen' (13 Pruefungen), dann 'landkarte freigabe --neu fehler|klein|gross --jetzt --text ...'. Reihenfolge fest: pruefen, stempeln (plugin.json + lk/__init__.py), Paket bauen, AENDERUNGEN.md, Commit, Markierung vX.Y.Z, push --follow-tags. Harte Pruefung fehlgeschlagen = nichts geaendert. Stand gegen GitHub: 'landkarte freigabe' ohne Schalter.
- [2026-11-09] Tresor und Tresorwache seit Fassung 2.0.0 (09.11.2026). Der Tresor liegt unter ~/.landkarte/tresor.enc, aes-256-cbc/pbkdf2-600000 ueber openssl plus HMAC ueber den Geheimtext; Hauptschluessel im macOS-Schluesselbund, sonst Datei mit 600. Die Tresorwache haengt am UserPromptSubmit-Hook und ist die EINZIGE Stelle, die am Sitzungsprotokoll etwas aendern darf - sie ersetzt Geheimnisse durch einen Verweis und legt vorher eine Kopie in ~/.Papierkorb-Claude/tresorwache/. Wichtig: UserPromptSubmit kann den Prompt NICHT umschreiben (nur PreToolUse kann updatedInput), das eine Mal sieht das Modell das Passwort also noch; verhindert wird das Weiterleben im Protokoll.
## Zugaenge

Wo die Zugangsdaten liegen — nicht die Daten selbst.

## Offen

Was noch zu tun ist.
