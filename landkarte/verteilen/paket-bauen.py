#!/usr/bin/env python3
"""Zweck: Aus dem Repository eine einzige Einrichtungsdatei bauen.

Ergebnis: `verteilen/brainbook-einrichten.py` - eine Datei, die das ganze
Werkzeug enthaelt, sich selbst auspackt, Claude Code erkennt und dann entweder
das Plugin mit den Hooks einrichtet oder die bestmoegliche Alternative.

Muss nach jeder Aenderung am Werkzeug neu laufen, sonst veraltet die Datei.
Normalerweise ruft `landkarte freigabe` den Bauer selbst auf; von Hand:

    python3 verteilen/paket-bauen.py              # die echte Einzeldatei
    python3 verteilen/paket-bauen.py --ziel X.py  # Probe, aendert nichts
"""

from __future__ import annotations

import base64
import io
import json
import sys
import textwrap
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent.parent     # Marktplatz-Wurzel
PLUGIN = WURZEL / "landkarte"
ZIEL = PLUGIN / "verteilen" / "brainbook-einrichten.py"
PLUGIN_JSON = PLUGIN / ".claude-plugin" / "plugin.json"


def fassung() -> str:
    """Die eine Fassungsnummer, aus plugin.json. Niemals hier doppelt pflegen."""
    return json.loads(PLUGIN_JSON.read_text("utf-8"))["version"]

MITNEHMEN = (
    ".claude-plugin/marketplace.json",
    "README.md",
    "landkarte/.claude-plugin/plugin.json",
    "landkarte/README.md",
    "landkarte/bin/landkarte",
    "landkarte/bin/brainbook",
    "landkarte/hooks/hooks.json",
    "landkarte/hooks/chronist.sh",
    "landkarte/hooks/sitzungsstart.sh",
    "landkarte/hooks/sitzungsende.sh",
    "landkarte/commands/brainbook.md",
    "landkarte/skills/landkarte/SKILL.md",
    "landkarte/dienste/de.jan.landkarte.regal.plist",
    "landkarte/dienste/de.jan.landkarte.aufsicht.plist",
    "landkarte/verteilen/START-HIER.md",
    "landkarte/verteilen/AGENTS.md",
    "landkarte/verteilen/RUECKMELDUNG.md",
    "landkarte/verteilen/fuer-claude-code.md",
    "landkarte/verteilen/fuer-chatgpt.md",
    "landkarte/verteilen/fuer-grok.md",
    "landkarte/verteilen/einrichten.sh",
)
MODULE = sorted(p.relative_to(WURZEL).as_posix()
                for p in (PLUGIN / "lk").glob("*.py"))

AUSFUEHRBAR = {"landkarte/bin/landkarte", "landkarte/bin/brainbook",
               "landkarte/hooks/chronist.sh", "landkarte/hooks/sitzungsstart.sh",
               "landkarte/hooks/sitzungsende.sh",
               "landkarte/verteilen/einrichten.sh"}


def paket_bauen() -> bytes:
    puffer = io.BytesIO()
    fehlt = []
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in list(MITNEHMEN) + MODULE:
            quelle = WURZEL / rel
            if not quelle.exists():
                fehlt.append(rel)
                continue
            eintrag = zipfile.ZipInfo(rel)
            eintrag.external_attr = (0o755 if rel in AUSFUEHRBAR else 0o644) << 16
            eintrag.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(eintrag, quelle.read_bytes())
    if fehlt:
        raise SystemExit("Diese Dateien fehlen:\n  " + "\n  ".join(fehlt))
    return puffer.getvalue()


KOPF = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brainbook & Landkarte — Einrichtung in einer einzigen Datei.

So benutzt du sie:

    python3 brainbook-einrichten.py

Sie packt das Werkzeug nach ~/brainbook aus, verknuepft die Befehle
`landkarte` und `brainbook`, fragt nach deinem Namen und deiner KI und baut
das erste Verzeichnis.

Erkennt sie Claude Code, richtet sie zusaetzlich das Plugin mit den Hooks ein:
dann schreibt ein Chronist jeden Werkzeugaufruf mit und am Sitzungsende
entstehen von selbst Buchkapitel. Findet sie kein Claude Code, legt sie die
Anweisungsdatei fuer deine KI bereit und sagt dir, wohin du sie einfuegst.

Es wird nichts ausserhalb von ~/brainbook, ~/.landkarte und ~/.local/bin
veraendert. Ohne --mit-plugin wird auch ~/.claude nicht angefasst.

Schalter:
    --ziel <ordner>     woanders auspacken (Standard: ~/brainbook)
    --name <name>       Name fuer das Selbstprotokoll, ohne Rueckfrage
    --ki <kennung>      claude-code | chatgpt | grok | codex | keine
    --ohne-plugin       Claude-Code-Plugin nicht einrichten
    --ohne-regal        kein erster Scan aller Projekte
    --nur-auspacken     nur entpacken, sonst nichts
    --fassung           nur die Fassungsnummer nennen
"""

from __future__ import annotations

import base64
import io
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

MINDESTENS = (3, 10)
FASSUNG = "{fassung}"
'''

RUMPF = r'''

def sage(*teile: object) -> None:
    print(*teile, flush=True)


def abschnitt(titel: str) -> None:
    sage("")
    sage(titel)
    sage("-" * len(titel))


def abbruch(text: str) -> None:
    sage("")
    sage("FEHLER: " + text)
    raise SystemExit(1)


def schalter(name: str, standard: str | None = None) -> str | None:
    if name in sys.argv:
        stelle = sys.argv.index(name)
        if stelle + 1 < len(sys.argv):
            return sys.argv[stelle + 1]
    return standard


def gesetzt(name: str) -> bool:
    return name in sys.argv


def auspacken(ziel: Path) -> list[Path]:
    rohdaten = base64.b64decode(PAKET.encode("ascii"))
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben = []
    with zipfile.ZipFile(io.BytesIO(rohdaten)) as z:
        for eintrag in z.infolist():
            # Pfade pruefen, nichts ausserhalb des Ziels schreiben
            pfad = (ziel / eintrag.filename).resolve()
            if not str(pfad).startswith(str(ziel.resolve())):
                abbruch(f"Paket enthaelt einen unerlaubten Pfad: {eintrag.filename}")
            pfad.parent.mkdir(parents=True, exist_ok=True)
            pfad.write_bytes(z.read(eintrag))
            rechte = (eintrag.external_attr >> 16) & 0o777
            if rechte:
                pfad.chmod(rechte)
            geschrieben.append(pfad)
    return geschrieben


def verknuepfen(werkzeug: Path) -> Path:
    bin_ordner = Path.home() / ".local" / "bin"
    bin_ordner.mkdir(parents=True, exist_ok=True)
    for name in ("landkarte", "brainbook"):
        quelle = werkzeug / "bin" / name
        ziel = bin_ordner / name
        if ziel.is_symlink() or ziel.exists():
            ziel.unlink()
        try:
            ziel.symlink_to(quelle)
        except OSError:
            # Windows ohne Entwicklermodus: kleine Weiterleitung schreiben
            ziel.write_text(
                f'#!/bin/sh\nexec "{sys.executable}" "{quelle}" "$@"\n', "utf-8")
            ziel.chmod(0o755)
    return bin_ordner


def pfad_hinweis(bin_ordner: Path) -> None:
    if str(bin_ordner) in os.environ.get("PATH", "").split(os.pathsep):
        return
    abschnitt("Noch ein Schritt: PATH")
    sage(f"{bin_ordner} steht nicht in deinem PATH. Fuege das ein und starte")
    sage("das Terminal neu:")
    schale = os.environ.get("SHELL", "")
    datei = "~/.zshrc" if schale.endswith("zsh") else "~/.bashrc"
    sage(f'  echo \'export PATH="$HOME/.local/bin:$PATH"\' >> {datei}')
    sage("")
    sage("Bis dahin erreichst du die Befehle so:")
    sage(f"  {bin_ordner}/landkarte status")


def claude_code_vorhanden() -> str | None:
    pfad = shutil.which("claude")
    if not pfad:
        return None
    if not (Path.home() / ".claude").is_dir():
        return None
    try:
        ergebnis = subprocess.run([pfad, "--version"], capture_output=True,
                                  text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return ergebnis.stdout.strip() if ergebnis.returncode == 0 else None


def plugin_einrichten(marktplatz: Path) -> bool:
    claude = shutil.which("claude")
    if not claude:
        return False
    schritte = (
        ([claude, "plugin", "marketplace", "add", str(marktplatz)],
         "Marktplatz eintragen"),
        ([claude, "plugin", "install", "landkarte@jan-werkzeuge"],
         "Plugin einrichten"),
    )
    for befehl, was in schritte:
        try:
            ergebnis = subprocess.run(befehl, capture_output=True, text=True,
                                      timeout=180)
        except (OSError, subprocess.SubprocessError) as fehler:
            sage(f"  {was}: fehlgeschlagen ({fehler})")
            return False
        ausgabe = (ergebnis.stdout + ergebnis.stderr).strip().splitlines()
        letzte = ausgabe[-1] if ausgabe else ""
        if ergebnis.returncode != 0 and "already" not in letzte.lower():
            sage(f"  {was}: fehlgeschlagen — {letzte[:160]}")
            sage(f"  Von Hand:  {' '.join(befehl)}")
            return False
        sage(f"  {was}: ok")
    return True


def frage(text: str, standard: str = "") -> str:
    if not sys.stdin.isatty():
        return standard
    try:
        antwort = input(text).strip()
    except (EOFError, KeyboardInterrupt):
        return standard
    return antwort or standard


def laufen(werkzeug: Path, *argumente: str) -> int:
    befehl = [sys.executable, str(werkzeug / "bin" / "landkarte"), *argumente]
    try:
        return subprocess.run(befehl).returncode
    except (OSError, subprocess.SubprocessError) as fehler:
        sage(f"  Aufruf fehlgeschlagen: {fehler}")
        return 1


BEKANNTE_SCHALTER = {
    "--ziel", "--name", "--ki", "--ohne-plugin", "--ohne-regal",
    "--nur-auspacken", "--hilfe", "--help", "-h",
    "--fassung", "--version", "-V",
}


def main() -> int:
    # Hilfe und unbekannte Schalter abfangen, BEVOR etwas angelegt wird.
    # Sonst installiert ein "--help" einfach los - das ist genau der Fehler,
    # den jemand beim ersten Ausprobieren macht.
    if {"--hilfe", "--help", "-h"} & set(sys.argv[1:]):
        sage(__doc__ or "")
        return 0
    if {"--fassung", "--version", "-V"} & set(sys.argv[1:]):
        sage(FASSUNG)
        return 0
    unbekannt = [a for a in sys.argv[1:]
                 if a.startswith("-") and a not in BEKANNTE_SCHALTER]
    if unbekannt:
        sage("Unbekannter Schalter: " + ", ".join(unbekannt))
        sage("")
        sage(__doc__ or "")
        return 2

    if sys.version_info < MINDESTENS:
        abbruch(
            f"Python {MINDESTENS[0]}.{MINDESTENS[1]} oder neuer wird gebraucht, "
            f"gefunden {sys.version_info.major}.{sys.version_info.minor}.\n"
            "  macOS:   brew install python\n"
            "  Ubuntu:  sudo apt install python3\n"
            "  Windows: python.org/downloads, dann in PowerShell ausfuehren")

    sage(f"Brainbook & Landkarte — Einrichtung, Fassung {FASSUNG}")
    sage(f"Python {sys.version_info.major}.{sys.version_info.minor} auf {sys.platform}")

    ziel = Path(schalter("--ziel", str(Path.home() / "brainbook"))).expanduser()
    abschnitt("1. Auspacken")
    dateien = auspacken(ziel)
    werkzeug = ziel / "landkarte"
    sage(f"{len(dateien)} Dateien nach {ziel}")

    if gesetzt("--nur-auspacken"):
        sage("")
        sage(f"Fertig. Weiter mit: {werkzeug}/verteilen/START-HIER.md")
        return 0

    abschnitt("2. Befehle verknuepfen")
    bin_ordner = verknuepfen(werkzeug)
    sage(f"landkarte und brainbook liegen in {bin_ordner}")

    abschnitt("3. Wer bist du")
    name = schalter("--name") or frage(
        "Dein Name fuer das Selbstprotokoll (z.B. andre): ")
    ki = schalter("--ki")
    fassung = claude_code_vorhanden()
    if not ki:
        if fassung:
            sage(f"Claude Code gefunden: {fassung}")
            ki = frage("Welche KI benutzt du? [claude-code]: ", "claude-code")
        else:
            ki = frage("Welche KI benutzt du? "
                       "[chatgpt / grok / codex / keine]: ", "unbekannt")

    argumente = ["einrichten", "--ki", ki or "unbekannt"]
    if name:
        argumente += ["--teilnehmer", name]
    laufen(werkzeug, *argumente)

    abschnitt("4. Deine KI anbinden")
    anweisung = werkzeug / "verteilen" / "AGENTS.md"
    if fassung and not gesetzt("--ohne-plugin"):
        sage("Claude Code ist da — ich richte das Plugin mit den Hooks ein.")
        sage("Damit schreibt ein Chronist jeden Werkzeugaufruf mit, und am")
        sage("Sitzungsende entstehen von selbst Buchkapitel.")
        sage("")
        if plugin_einrichten(ziel):
            sage("")
            sage("  Pruefen:  claude plugin list | grep -A3 landkarte")
            sage(f"  Lesen:    {werkzeug}/verteilen/fuer-claude-code.md")
        else:
            sage("")
            sage("  Das Plugin ging nicht automatisch. Von Hand:")
            sage(f"    claude plugin marketplace add {ziel}")
            sage("    claude plugin install landkarte@jan-werkzeuge")
    else:
        if fassung:
            sage("Claude Code ist da, aber --ohne-plugin war gesetzt.")
        else:
            sage("Kein Claude Code gefunden — also die beste Alternative:")
        sage("")
        sage("Deine KI kann auf diesem Rechner keine Befehle ausfuehren und")
        sage("nichts automatisch mitschreiben. Was voll funktioniert:")
        sage("Verzeichnis, Spickzettel, dreistufige Suche, Notizen, Brainbook.")
        sage("")
        sage("Fuege diese Datei einmal in deine KI ein:")
        sage(f"  {anweisung}")
        if ki == "chatgpt":
            sage("  ChatGPT: linke Spalte -> Projekte -> Neu -> Anweisungen")
            sage(f"  Anleitung: {werkzeug}/verteilen/fuer-chatgpt.md")
        elif ki == "grok":
            sage("  Grok: Einstellungen -> Custom Instructions")
            sage(f"  Anleitung: {werkzeug}/verteilen/fuer-grok.md")
        else:
            sage("  Codex, Cursor, Aider: AGENTS.md in den Projektordner legen")

    if not gesetzt("--ohne-regal"):
        abschnitt("5. Erstes Verzeichnis")
        sage("Das kann bei vielen Projekten einige Sekunden dauern.")
        laufen(werkzeug, "regal")

    abschnitt("Was hier eingerichtet wurde")
    if fassung and not gesetzt("--ohne-plugin"):
        sage("Beim ersten Start erklaert dir Claude Code selbst, was die")
        sage("Bibliothek kann, wie sie vorgeht und wie du eingreifst.")
        sage("Jederzeit nachlesen:  landkarte vorstellen")
    else:
        laufen(werkzeug, "vorstellen")

    abschnitt("Fertig")
    sage("Die wichtigsten Befehle:")
    sage('  landkarte wo "<begriff>"   suchen: Projekt -> Teil -> Datei:Zeile')
    sage("  landkarte zeig              Inhaltsverzeichnis des Projekts hier")
    sage('  landkarte notiz "..."       eine Falle festhalten')
    sage("  brainbook                   dein eigenes Buch")
    sage("")
    sage("Rueckmeldung an Jan — das Werkzeug protokolliert sich selbst:")
    sage("  brainbook stats             ansehen")
    sage("  brainbook stats --roh       jede Rohzeile einzeln pruefen")
    sage("  brainbook stats --export ~/Desktop")
    sage("")
    sage("Darin stehen Befehle, Dauern, Fehlerklassen und Groessenklassen.")
    sage("Nicht darin: Projektnamen, Pfade, Inhalte, Suchbegriffe.")
    sage("Abschalten:  landkarte einrichten --statistik-aus")
    sage("")
    pfad_hinweis(bin_ordner)
    sage("")
    sage(f"Alles Weitere: {werkzeug}/verteilen/START-HIER.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main(argv: list[str] | None = None) -> int:
    argumente = list(argv if argv is not None else sys.argv[1:])
    if {"--hilfe", "--help", "-h"} & set(argumente):
        print(__doc__ or "")
        return 0
    # --ziel: woanders hinbauen, damit ein Pruefen die verteilte Datei nicht
    # anfasst. Ohne --ziel wird die echte Einzeldatei neu geschrieben.
    ziel = ZIEL
    if "--ziel" in argumente:
        stelle = argumente.index("--ziel")
        if stelle + 1 >= len(argumente):
            print("--ziel braucht einen Pfad")
            return 2
        ziel = Path(argumente[stelle + 1]).expanduser()
        del argumente[stelle:stelle + 2]
    unbekannt = [a for a in argumente if a.startswith("-")]
    if unbekannt:
        print("Unbekannter Schalter: " + ", ".join(unbekannt))
        return 2

    rohdaten = paket_bauen()
    kodiert = base64.b64encode(rohdaten).decode("ascii")
    zeilen = textwrap.wrap(kodiert, 96)
    block = 'PAKET = (\n' + "\n".join(f'    "{z}"' for z in zeilen) + "\n)\n"
    kopf = KOPF.replace("{fassung}", fassung())
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(kopf + "\n" + block + RUMPF, "utf-8")
    ziel.chmod(0o755)
    wohin = ziel.relative_to(WURZEL) if ziel.is_relative_to(WURZEL) else ziel
    print(f"{wohin} gebaut, Fassung {fassung()}")
    print(f"  Paket:     {len(rohdaten) / 1024:.0f} KB in "
          f"{len(MITNEHMEN) + len(MODULE)} Dateien")
    print(f"  Datei:     {ziel.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
