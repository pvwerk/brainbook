"""Zweck: Die Bibliothek erklaert sich beim ersten Mal selbst.

Wer das Werkzeug neu einrichtet, soll nicht erst eine README suchen muessen.
Beim ersten Start legt der Hook eine Vorstellung in den Kontext, und die KI
erklaert in eigenen Worten, was die Bibliothek kann, wie sie vorgeht, was von
selbst passiert und wie man eingreift. Danach nie wieder - ein Merker verhindert
die Wiederholung.

`landkarte vorstellen` zeigt denselben Text fuer Menschen, jederzeit.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import konfig

MERKER = konfig.LK_HEIM / "vorgestellt"


def schon_vorgestellt() -> bool:
    return MERKER.exists()


def merken() -> None:
    try:
        konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
        MERKER.write_text(date.today().isoformat() + "\n", "utf-8")
    except OSError:
        pass


def zuruecksetzen() -> None:
    try:
        MERKER.unlink()
    except OSError:
        pass


# --------------------------------------------------------------- fuer Menschen

TEXT = """\
LANDKARTE & BRAINBOOK — was das ist

DIE REGEL
Vor jeder Änderung an einem bestehenden Projekt wird zuerst nachgeschlagen —
nicht angefangen, den Code zu lesen. Diese Regel steht in deiner
Anweisungsdatei (landkarte anweisung zeigt sie), und ein Platzanweiser hält
eine KI an, die sie übergeht: beim ersten Lesezugriff in einem Projekt, in
dem noch nicht nachgeschlagen wurde, blockiert er einmal und liefert die
Auskunft gleich mit — Zweck der Datei, ihre Symbole mit Zeilennummern und die
Fundstellen zum Begriff, ohne eine Datei zu lesen. Danach schweigt er und
reicht zu jeder neuen Seite nur noch den Verzeichniseintrag nach.
  landkarte wache        Stand: wurde nachgeschlagen, wer wurde angehalten
  landkarte wache --aus  abschalten, wenn er im Weg ist

DU SIEHST ES IN JEDER ANTWORT
Die KI beginnt jede Antwort mit einer Zeile, damit du nicht raten musst, ob
sie nachgesehen hat:
  bb false               nichts in der Bibliothek gefunden
  bb true 7 Einträge     7 Fundstellen gefunden und benutzt
Nach langen Aufgaben kommt die Bilanz dazu:
  bb 12 uses             so oft hat die Bibliothek etwas geliefert
Selbst abfragen: landkarte bb "<begriff>" und landkarte bb --bilanz.
Steht oft bb false, hat die Bibliothek eine Lücke - das ist ein Befund.

DIE VERGANGENHEIT AUFNEHMEN
Eine frische Bibliothek ist leer und sagt immer bb false. Einmal
  landkarte aufnehmen
traegt nach, was in alten Sitzungsprotokollen steht, baut das Regal, schreibt
Kapitel daraus und laesst danach den Testleser 20 % der Bibliothek rueckwaerts
lesen. Die ersten zwei Schritte kosten nichts; vor den Modellaufrufen wird
gesagt, wie viele es sind, und gefragt.

WAS ES KANN
Es hält Projektwissen fest, damit niemand nach Wochen wieder von vorn anfängt.
Je Projekt entsteht ein Inhaltsverzeichnis (KARTE.md) mit vier Teilen:
  Spickzettel   die Befehle, Adressen und Zugänge-Zeiger des Projekts
  Fallen        wo schon Zeit verloren ging, und warum
  Wo liegt was  jede Datei mit einem Satz, wofür sie da ist
  Symbole       Funktionen und Klassen mit Zeilennummer

WIE ES VORGEHT
Gesucht wird dreistufig, damit man nicht im falschen Projekt nachsieht:
  landkarte wo "<begriff>"
    Liste 1  Regal     welches Projekt
    Liste 2  Fach      welcher Teil davon
    Liste 3  Inhalt    Datei und Zeile
Ähnlich benannte Projekte werden gegenseitig als Verwechslungsgefahr vermerkt.

WAS VON SELBST PASSIERT
  - Beim Start einer Sitzung liegt der Auszug des Projekts im Kontext.
  - Mit Claude Code: ein Chronist schreibt jeden Werkzeugaufruf mit (2 ms,
    keine Token), und am Sitzungsende machen zwei unabhängige Schreiber daraus
    ein Buchkapitel; ein Schiedsrichter vergleicht die beiden am Rohprotokoll.
  - Nachts: Verzeichnis neu bauen, nach echter Nutzung sortieren, und ein
    Testleser prüft stichprobenartig, ob das Verzeichnis zum Finden taugt.
  - Ohne Claude Code läuft nichts automatisch, aber alles von Hand.

WIE DU EINFLUSS NIMMST
  landkarte notiz "..."                    eine Falle festhalten
  landkarte notiz --art regel "..."        eine Regel für das nächste Mal
  landkarte notiz --art zugang "..."       WO Zugangsdaten liegen, nie welche
  landkarte notiz --art offen "..."        offener Punkt
  landkarte korrigieren "falsch" "richtig" gespeichertes Wissen berichtigen
  .landkarte/notizen.md                    deine Datei, wird nie überschrieben
  .landkarte/ignorieren.txt                was nicht kartografiert werden soll
  ~/.landkarte/konfig.json                 Wurzeln, Gruppen, Aliase, Modell
  landkarte dienst --einbauen / --ausbauen Nachtlauf an oder aus
  landkarte einrichten --statistik-aus     Selbstprotokoll abschalten

Erzeugtes wird bei jedem Scan neu gebaut — schreib nicht in KARTE.md hinein,
sondern in notizen.md. Von Hand Geschriebenes bleibt immer erhalten.

DAS BRAINBOOK
Dein eigenes Buch: ~/.landkarte/brainbook.md
Es steht in keinem Regal und in keiner Liste, wird nicht gescannt, nicht
sortiert und nicht geprüft. Es liegt beim Bibliothekar am Tresen.

Es ist ein Übersetzungsbuch: links ein Wort, wie DU es sagst, rechts der Ort in
der Ablage. Sagst du "ETM CRM", wird daraus der Ordner etm-gutachten, ohne dass
du den Ordnernamen kennen musst. Darin stehen nur Verweise — Projekt,
Kategorien, Pfade, ein Satz "was ist das" und Kurznotizen.

  brainbook                      das ganze Buch
  brainbook "<wort>"             ein Stichwort nachschlagen
  landkarte merke "<wort>" --ist <projekt> --auch "<synonym>" --was "..."

landkarte wo sieht dort ZUERST nach: dein Wort zählt mehr als jeder Ordnername.
Prägst du im Gespräch ein neues Wort, sag es — es wird eingetragen.

MITHELFEN
Das Werkzeug protokolliert sich selbst, damit Fehler gefunden werden: Befehle,
Dauern, Fehlerklassen, Größenklassen. Nicht: Projektnamen, Pfade, Inhalte,
Suchbegriffe.
  brainbook stats --roh                jede Rohzeile einzeln prüfen
  brainbook stats --export ~/Desktop   Datei zum Verschicken
"""

# ------------------------------------------------------------------- fuer die KI

ANWEISUNG = """\
NEUE EINRICHTUNG — dieser Mensch benutzt die Landkarte zum ersten Mal.

Erkläre ihm zu Beginn deiner ersten Antwort kurz und in eigenen Worten, was
hier eingerichtet wurde. Höchstens etwa zehn Zeilen, dann weiter mit seinem
eigentlichen Anliegen. Biete am Ende an, Einzelheiten zu zeigen. Wenn er sofort
eine andere Aufgabe stellt, hat die Aufgabe Vorrang; erkläre es dann in zwei
Sätzen und biete den Rest an.

Diese sieben Punkte gehören in die Erklärung:

0. DIE REGEL — vor jeder Änderung an einem bestehenden Projekt wird zuerst
   nachgeschlagen, nicht Code gelesen. Die Regel steht jetzt in seiner
   Anweisungsdatei, ein Platzanweiser hält eine KI an, die sie übergeht, und
   gibt ihr die Auskunft gleich mit. Angehalten wird höchstens einmal je
   Projekt und Sitzung; `landkarte wache --aus` schaltet ihn ab.

1. WAS ES KANN — je Projekt ein Inhaltsverzeichnis (KARTE.md) mit Spickzettel
   (Befehle, Adressen), Fallenprotokoll, einer Zeile Zweck je Datei und den
   Symbolen mit Zeilennummern.

2. WIE GESUCHT WIRD — `landkarte wo "<begriff>"` antwortet dreistufig: welches
   Projekt, welcher Teil davon, welche Datei und Zeile. Ähnlich benannte
   Projekte werden als Verwechslungsgefahr genannt.

3. WAS VON SELBST PASSIERT — beim Sitzungsstart liegt der Auszug des Projekts
   im Kontext. Beim ersten Lesezugriff in einem kartografierten Projekt, in
   dem noch nicht nachgeschlagen wurde, hält der Platzanweiser einmal an und
   liefert Zweck, Symbole und Fundstellen mit — ohne eine Datei zu lesen. Mit Claude Code schreibt ein Chronist jeden Werkzeugaufruf mit
   und am Sitzungsende machen zwei unabhängige Schreiber ein Buchkapitel, das
   ein Schiedsrichter am Rohprotokoll vergleicht. Nachts wird neu kartografiert
   und ein Testleser prüft, ob das Verzeichnis zum Finden taugt.

4. WIE ER EINFLUSS NIMMT — `landkarte notiz "..."` hält eine Falle fest,
   `--art regel|zugang|offen` die anderen Sorten; `landkarte korrigieren
   "falsch" "richtig"` berichtigt falsches Wissen, ohne das Original zu
   löschen. `.landkarte/notizen.md` ist seine Datei und wird nie überschrieben,
   `.landkarte/ignorieren.txt` nimmt Ordner aus. Erzeugtes (KARTE.md) wird bei
   jedem Scan neu gebaut — Handschriftliches gehört in notizen.md.

5. DAS BRAINBOOK — sein eigenes Buch in ~/.landkarte/brainbook.md, das in
   keinem Regal und keiner Liste steht. Es übersetzt seine Worte in Orte der
   Ablage: sagt er "ETM CRM", findet `landkarte wo` den Ordner etm-gutachten.
   Darin stehen nur Verweise, keine Inhalte. Prägt er im Gespräch ein eigenes
   Wort für etwas, trage es unaufgefordert ein:
   `landkarte merke "<wort>" --ist <projekt> --was "..."`.

6. WIE ER ES ABFRAGT — nenne die vier Befehle wörtlich, mit je einem
   Halbsatz dazu:
     landkarte bb "<begriff>"   nachschlagen; gibt die Signalzeile für die
                                Antwort gleich mit
     landkarte wo "<begriff>"   dasselbe ausführlich: Regal, Fach, Seite
     landkarte bb --bilanz      `bb N uses` — wie oft die Bibliothek in dieser
                                Sitzung etwas geliefert hat
     brainbook stats --roh      das Selbstprotokoll des Werkzeugs, Zeile für
                                Zeile; `brainbook stats --export ~/Desktop`
                                macht daraus eine Datei für die Rückmeldung

   Sage dazu, dass du von jetzt an jede Antwort mit `bb false` oder
   `bb true <N> Einträge` beginnst, damit er sieht, ob die Bibliothek etwas
   wusste, und nach langen Aufgaben `bb <N> uses` anhängst.

DANACH, UNAUFGEFORDERT: biete ihm an, die Vergangenheit aufzunehmen.
Eine frische Bibliothek ist leer, und eine leere Bibliothek antwortet immer
`bb false` — dann glaubt niemand mehr, dass Nachschlagen sich lohnt. Sage:

  * aus alten Sitzungsprotokollen lässt sich nachtragen, was schon passiert
    ist; daraus entstehen Buchkapitel mit den Fallen, die schon Zeit gekostet
    haben
  * Chronik und Regal kosten nichts, erst Kapitel und Rücklesen rufen ein
    Modell — der Befehl sagt vorher, wie oft, und fragt
  * der Befehl ist `landkarte aufnehmen`

Sagt er ja, führe `landkarte aufnehmen --ja` aus. Danach liest der Testleser
von selbst 20 % der Bibliothek rückwärts — er kennt die Antwort und sucht die
Frage. **Teile ihm das Ergebnis mit**: wie viele Kapitel geschrieben und
gelesen wurden, die gemessene Trefferquote und was dabei berichtigt wurde.
Liegt die Trefferquote unter 60 %, sage es deutlich: dann findet das
Verzeichnis zu wenig, und `landkarte aufsicht` zeigt, woran es liegt.

Erwähne auch in einem Satz, dass das Werkzeug sich selbst protokolliert, damit
Fehler gefunden werden können, dass darin keine Projektnamen, Pfade oder
Inhalte stehen und dass `brainbook stats --roh` alles zeigt.

Sage nichts, was du hier nicht liest. Vollständig steht es in
`landkarte vorstellen` und in der README des Werkzeugs.
"""
