"""Zweck: Eine Fassung bewusst freigeben - pruefen, stempeln, hochladen.

Entwickelt wird immer im Original auf dem Mac. Nach GitHub geht nichts
nebenbei, sondern als benannte Fassung, die vorher jede Pruefung bestanden
hat. Blindes Reinschreiben vermehrt Fehler bei allen, die das Werkzeug
installiert haben - und niemand kann hinterher sagen, welcher Stand bei wem
liegt.

Reihenfolge, die nie umgestellt wird:
    1. pruefen        - aendert nichts
    2. stempeln       - eine Fassungsnummer an genau zwei Stellen
    3. Paket bauen    - damit die verteilte Einzeldatei nicht veraltet
    4. Aenderungen    - was in dieser Fassung steckt
    5. hochladen      - nur mit --jetzt, nie von selbst
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
WURZEL = PLUGIN.parent
PLUGIN_JSON = PLUGIN / ".claude-plugin" / "plugin.json"
INIT_PY = PLUGIN / "lk" / "__init__.py"
PAKETBAUER = PLUGIN / "verteilen" / "paket-bauen.py"
INSTALLER = PLUGIN / "verteilen" / "brainbook-einrichten.py"
AENDERUNGEN = WURZEL / "AENDERUNGEN.md"

HERKUNFT = "pvwerk/brainbook"
ZWEIG = "main"
ROH = ("https://raw.githubusercontent.com/pvwerk/brainbook/main/"
       "landkarte/.claude-plugin/plugin.json")
MARKIERUNGEN = "https://api.github.com/repos/pvwerk/brainbook/tags?per_page=20"

# Dateien, die beim Freigeben neu entstehen und daher schmutzig sein duerfen
ERZEUGT = {
    "KARTE.md",
    ".landkarte/notizen.md",
    "landkarte/verteilen/brainbook-einrichten.py",
    "landkarte/.claude-plugin/plugin.json",
    "landkarte/lk/__init__.py",
    "AENDERUNGEN.md",
}

STUFEN = {"fehler": 2, "klein": 1, "gross": 0}


# --------------------------------------------------------------- Werkzeuge

def _git(*args: str, zeit: int = 30) -> tuple[int, str]:
    """git im Original aufrufen. Gibt (Code, Ausgabe) zurueck, wirft nie."""
    try:
        e = subprocess.run(["git", *args], cwd=str(WURZEL), text=True,
                           capture_output=True, timeout=zeit)
        # Nur hinten kuerzen: bei `status --porcelain` tragen die ersten zwei
        # Spalten Bedeutung, ein .strip() wuerde sie verschieben.
        return e.returncode, (e.stdout + e.stderr).rstrip()
    except Exception as fehler:                       # noqa: BLE001
        return 1, f"{type(fehler).__name__}: {fehler}"


def _lauf(befehl: list[str], heim: Path | None = None,
          zeit: int = 120) -> tuple[int, str]:
    umgebung = dict(os.environ)
    if heim is not None:
        umgebung["HOME"] = str(heim)
        umgebung.pop("XDG_CONFIG_HOME", None)
        umgebung.pop("CLAUDE_CONFIG_DIR", None)
    try:
        e = subprocess.run(befehl, text=True, capture_output=True,
                           timeout=zeit, env=umgebung)
        return e.returncode, (e.stdout + e.stderr).strip()
    except Exception as fehler:                       # noqa: BLE001
        return 1, f"{type(fehler).__name__}: {fehler}"


def _befund(name: str, ok: bool, hinweis: str = "", hart: bool = True) -> dict:
    return {"name": name, "ok": ok, "hinweis": hinweis, "hart": hart}


# ---------------------------------------------------------------- Fassungen

def fassung() -> str:
    """Die gueltige Fassung - plugin.json ist die Quelle."""
    return json.loads(PLUGIN_JSON.read_text("utf-8"))["version"]


def fassung_im_paket() -> str:
    """Welche Fassung im Modul steht (muss mit plugin.json uebereinstimmen)."""
    treffer = re.search(r'__version__\s*=\s*"([^"]+)"', INIT_PY.read_text("utf-8"))
    return treffer.group(1) if treffer else ""


def naechste(stufe: str) -> str:
    """gross -> 2.0.0, klein -> 1.2.0, fehler -> 1.1.1"""
    if stufe not in STUFEN:
        raise ValueError(f"Stufe muss gross, klein oder fehler sein, nicht {stufe!r}")
    teile = [int(z) for z in fassung().split(".")]
    while len(teile) < 3:
        teile.append(0)
    stelle = STUFEN[stufe]
    teile[stelle] += 1
    for weiter in range(stelle + 1, 3):
        teile[weiter] = 0
    return ".".join(str(z) for z in teile)


def fassung_setzen(neu: str) -> list[str]:
    """Die Nummer an beiden Stellen setzen. Gibt die geaenderten Dateien."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", neu):
        raise ValueError(f"Fassung muss wie 1.2.3 aussehen, nicht {neu!r}")
    geaendert = []

    text = PLUGIN_JSON.read_text("utf-8")
    ersetzt = re.sub(r'("version"\s*:\s*")[^"]+(")', rf'\g<1>{neu}\g<2>',
                     text, count=1)
    if ersetzt != text:
        PLUGIN_JSON.write_text(ersetzt, "utf-8")
        geaendert.append(str(PLUGIN_JSON.relative_to(WURZEL)))

    text = INIT_PY.read_text("utf-8")
    ersetzt = re.sub(r'(__version__\s*=\s*")[^"]+(")', rf'\g<1>{neu}\g<2>',
                     text, count=1)
    if ersetzt != text:
        INIT_PY.write_text(ersetzt, "utf-8")
        geaendert.append(str(INIT_PY.relative_to(WURZEL)))
    return geaendert


def als_zahlen(name: str) -> tuple[int, ...]:
    """1.2.10 -> (1, 2, 10). Fuer Vergleiche; "10" ist mehr als "9"."""
    teile = []
    for stueck in str(name).lstrip("v").split("."):
        ziffern = "".join(z for z in stueck if z.isdigit())
        teile.append(int(ziffern) if ziffern else 0)
    while len(teile) < 3:
        teile.append(0)
    return tuple(teile[:3])


def neueste_markierung(zeit: int = 8) -> tuple[str, str]:
    """Die hoechste veroeffentlichte Fassung laut Markierungen. (Fassung, Fehler)

    Ueber die Programmierschnittstelle, nicht ueber die Rohdatei: die kommt
    aus einem Zwischenspeicher und laeuft Minuten nach. Braucht kein git und
    laeuft daher auch in einer installierten Kopie.
    """
    try:
        bitte = urllib.request.Request(
            MARKIERUNGEN, headers={"Accept": "application/vnd.github+json",
                                   "User-Agent": "landkarte"})
        with urllib.request.urlopen(bitte, timeout=zeit) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
        namen = [str(e.get("name", "")) for e in daten if isinstance(e, dict)]
        gueltig = [n for n in namen if re.fullmatch(r"v?\d+\.\d+\.\d+", n)]
        if not gueltig:
            return "", "keine Markierungen"
        return max(gueltig, key=als_zahlen).lstrip("v"), ""
    except urllib.error.HTTPError as fehler:
        return "", f"HTTP {fehler.code}"
    except Exception as fehler:                       # noqa: BLE001
        return "", f"{type(fehler).__name__}"


def _markierung_draussen(name: str) -> tuple[bool, str]:
    """Liegt die Markierung v<name> im entfernten Repository?

    Das ist die verbindliche Auskunft. Die Rohdatei unten kommt aus einem
    Zwischenspeicher und ist direkt nach dem Schieben noch Minuten alt.
    """
    code, aus = _git("ls-remote", "--tags", "origin",
                     f"refs/tags/v{name}", zeit=25)
    if code != 0:
        return False, aus.splitlines()[-1][:80] if aus else "nicht erreichbar"
    return bool(aus.strip()), ""


def _fassung_auf_github(zeit: int = 8) -> tuple[str, str]:
    """Was ein Abholer in diesem Moment herunterlaedt. (Fassung, Fehlergrund)

    Kommt aus dem Zwischenspeicher von raw.githubusercontent.com und laeuft
    der Markierung um einige Minuten nach - das ist kein Fehler, sondern
    genau die Auskunft, die jemand braucht, der gerade herunterlaedt.
    """
    try:
        with urllib.request.urlopen(ROH, timeout=zeit) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
        return str(daten.get("version", "")), ""
    except urllib.error.HTTPError as fehler:
        return "", f"HTTP {fehler.code}"
    except Exception as fehler:                       # noqa: BLE001
        return "", f"{type(fehler).__name__}"


# ----------------------------------------------------------------- Pruefung

def _pruef_herkunft() -> list[dict]:
    befunde = []
    code, aus = _git("rev-parse", "--show-toplevel")
    ist_repo = code == 0 and Path(aus).resolve() == WURZEL.resolve()
    befunde.append(_befund(
        "Original", ist_repo,
        "" if ist_repo else f"{WURZEL} ist nicht die Wurzel eines Repositorys - "
                            "freigegeben wird nur aus dem Original, nie aus "
                            "einer installierten Kopie"))
    if not ist_repo:
        return befunde

    code, aus = _git("remote", "get-url", "origin")
    passt = code == 0 and HERKUNFT in aus
    befunde.append(_befund(
        "Ziel", passt,
        "" if passt else f"origin ist {aus or '(keines)'}, erwartet war {HERKUNFT}"))

    code, zweig = _git("rev-parse", "--abbrev-ref", "HEAD")
    befunde.append(_befund(
        "Zweig", zweig == ZWEIG,
        "" if zweig == ZWEIG else f"HEAD steht auf {zweig}, freigegeben wird {ZWEIG}"))
    return befunde


def _pruef_arbeitsbaum() -> dict:
    code, aus = _git("status", "--porcelain")
    if code != 0:
        return _befund("Arbeitsbaum", False, aus)
    offen = []
    for zeile in aus.splitlines():
        if len(zeile) < 4:
            continue
        pfad = zeile[2:].strip().strip('"')
        if " -> " in pfad:
            pfad = pfad.split(" -> ")[-1]
        if pfad in ERZEUGT:
            continue
        offen.append(pfad)
    return _befund(
        "Arbeitsbaum", not offen,
        "" if not offen else
        f"{len(offen)} nicht eingecheckte Datei(en): {', '.join(offen[:6])}"
        " - erst committen, dann freigeben")


def _pruef_fassungen() -> dict:
    a, b = fassung(), fassung_im_paket()
    return _befund("Fassungsnummern", a == b,
                   "" if a == b else f"plugin.json sagt {a}, lk/__init__.py sagt {b}")


def _pruef_syntax() -> dict:
    """Jede Quelldatei uebersetzen. Eine kaputte Datei darf nie hinausgehen."""
    import py_compile
    kaputt = []
    quellen = sorted((PLUGIN / "lk").glob("*.py"))
    quellen += [PAKETBAUER, INSTALLER]
    with tempfile.TemporaryDirectory(prefix="landkarte-syntax-") as ordner:
        abwurf = Path(ordner) / "weg.pyc"
        for quelle in quellen:
            try:
                py_compile.compile(str(quelle), cfile=str(abwurf), doraise=True)
            except py_compile.PyCompileError as fehler:
                kaputt.append(f"{quelle.name}: {str(fehler).splitlines()[-1][:80]}")
    return _befund(f"Syntax ({len(quellen)} Dateien)", not kaputt,
                   "; ".join(kaputt))


def _pruef_hilfe() -> dict:
    """Jeden Unterbefehl nach seiner Hilfe fragen. Faengt kaputtes argparse."""
    import argparse
    import contextlib
    import io as _io
    from . import cli
    zerleger = cli.zerleger()
    namen: list[str] = []
    for handlung in zerleger._subparsers._group_actions:      # noqa: SLF001
        if isinstance(handlung, argparse._SubParsersAction):  # noqa: SLF001
            namen = sorted(handlung.choices)
            break
    kaputt = []
    for name in namen:
        still = _io.StringIO()
        try:
            with contextlib.redirect_stdout(still), contextlib.redirect_stderr(still):
                cli.zerleger().parse_args([name, "--help"])
        except SystemExit as ende:
            if ende.code not in (0, None):
                kaputt.append(f"{name} -> Code {ende.code}")
        except Exception as fehler:                   # noqa: BLE001
            kaputt.append(f"{name} -> {type(fehler).__name__}")
        else:
            kaputt.append(f"{name} -> keine Hilfe")
    return _befund(f"Hilfe aller {len(namen)} Befehle", not kaputt,
                   "; ".join(kaputt))


def _pruef_geheimnisse() -> dict:
    """Das Repository ist oeffentlich. Hier darf nichts Vertrauliches liegen."""
    from . import pruefer, schwaerzen
    code, aus = _git("ls-files")
    if code != 0:
        return _befund("Keine Zugangsdaten", False, aus)
    woertlich = schwaerzen.bekannte_geheimnisse()
    treffer = []
    for rel in aus.splitlines():
        datei = WURZEL / rel
        if not datei.is_file():
            continue
        try:
            text = datei.read_text("utf-8", errors="replace")
        except OSError:
            continue
        # Die Einzeldatei enthaelt die Quellen base64-kodiert; geprueft werden
        # die Quellen selbst, sonst meldet der base64-Block nur Rauschen.
        nur_woertlich = rel.endswith("brainbook-einrichten.py")
        for nummer, zeile in enumerate(text.splitlines(), 1):
            for geheim in woertlich:
                if geheim and geheim in zeile:
                    treffer.append(f"{rel}:{nummer} bekanntes Geheimnis")
                    break
            else:
                if nur_woertlich:
                    continue
                verdacht = pruefer.geheimnisverdacht(zeile)
                if verdacht:
                    treffer.append(f"{rel}:{nummer} {verdacht}")
            if len(treffer) >= 12:
                break
        if len(treffer) >= 12:
            break
    return _befund("Keine Zugangsdaten", not treffer, "; ".join(treffer))


def _paket_nutzlast(datei: Path) -> str:
    """Den base64-Block aus einer Einzeldatei ziehen, ohne sie auszufuehren."""
    text = datei.read_text("utf-8", errors="replace")
    treffer = re.search(r"^PAKET = \(\n(.*?)\n\)\n", text, re.S | re.M)
    if not treffer:
        return ""
    return "".join(re.findall(r'"([^"]*)"', treffer.group(1)))


def paket_veraltet() -> tuple[bool, str]:
    """Stimmt die verteilte Einzeldatei noch mit den Quellen ueberein?

    Gebaut wird in einen Wegwerfordner, damit das Pruefen nichts aendert.
    """
    if not INSTALLER.exists():
        return True, "Einzeldatei fehlt ganz"
    with tempfile.TemporaryDirectory(prefix="landkarte-paket-") as ordner:
        probe = Path(ordner) / "probe.py"
        code, aus = _lauf([sys.executable, str(PAKETBAUER), "--ziel", str(probe)])
        if code != 0 or not probe.exists():
            # Aelterer Paketbauer ohne --ziel: dann in Ruhe neu bauen und
            # den Inhalt vergleichen, die Datei ist danach wieder aktuell.
            vorher = INSTALLER.read_bytes()
            code, aus = _lauf([sys.executable, str(PAKETBAUER)])
            if code != 0:
                return True, f"Paketbauer scheitert: {aus[:160]}"
            if INSTALLER.read_bytes() == vorher:
                return False, ""
            return True, "Einzeldatei war nicht auf dem Stand der Quellen"
        if _paket_nutzlast(probe) == _paket_nutzlast(INSTALLER):
            return False, ""
        return True, "Einzeldatei war nicht auf dem Stand der Quellen"


def _pruef_paket() -> dict:
    veraltet, grund = paket_veraltet()
    return _befund("Einzeldatei aktuell", not veraltet, grund, hart=False)


def _pruef_installation() -> dict:
    """Die Einzeldatei in einem Wegwerf-Heim wirklich ausfuehren.

    Drei Faelle, die bei mir schon schiefgingen:
      - `--help` hat installiert statt zu helfen
      - ein Tippfehler im Schalter hat installiert
      - die ausgepackte Fassung lief nicht
    """
    if not INSTALLER.exists():
        return _befund("Installation in Wegwerf-Heim", False, "Einzeldatei fehlt")
    with tempfile.TemporaryDirectory(prefix="landkarte-heim-") as ordner:
        o = Path(ordner)
        heim = o / "heim"
        heim.mkdir()
        ziel = o / "werkzeug"

        code, aus = _lauf([sys.executable, "-I", str(INSTALLER), "--help"], heim=heim)
        if code != 0:
            return _befund("Installation in Wegwerf-Heim", False,
                           f"--help endet mit Code {code}: {aus[:120]}")
        if list(heim.iterdir()):
            return _befund("Installation in Wegwerf-Heim", False,
                           "--help legt Dateien an statt nur zu helfen")

        code, aus = _lauf([sys.executable, "-I", str(INSTALLER), "--tipfehler"],
                          heim=heim)
        if code != 2:
            return _befund("Installation in Wegwerf-Heim", False,
                           f"unbekannter Schalter endet mit Code {code}, erwartet 2")
        if list(heim.iterdir()):
            return _befund("Installation in Wegwerf-Heim", False,
                           "ein Tippfehler im Schalter legt Dateien an")

        code, aus = _lauf([sys.executable, "-I", str(INSTALLER),
                           "--nur-auspacken", "--ziel", str(ziel)], heim=heim)
        if code != 0:
            return _befund("Installation in Wegwerf-Heim", False,
                           f"Auspacken endet mit Code {code}: {aus[-200:]}")
        werkzeug = ziel / "landkarte" / "bin" / "landkarte"
        if not werkzeug.exists():
            return _befund("Installation in Wegwerf-Heim", False,
                           "ausgepackt, aber bin/landkarte fehlt")
        if not os.access(werkzeug, os.X_OK):
            return _befund("Installation in Wegwerf-Heim", False,
                           "bin/landkarte ist nicht ausfuehrbar")

        anzahl = sum(1 for _ in ziel.rglob("*") if _.is_file())
        # Im frischen Heim ist das Brainbook zu Recht leer und meldet Code 1 -
        # das ist der richtige Zustand, kein Mangel der Installation.
        proben = ((["--help"], (0,)), (["status"], (0,)),
                  (["brainbook"], (0, 1)), (["wo", "probe"], (0, 1)))
        for argumente, erlaubt in proben:
            code, aus = _lauf([str(werkzeug), *argumente], heim=heim)
            if code not in erlaubt:
                return _befund("Installation in Wegwerf-Heim", False,
                               f"`landkarte {' '.join(argumente)}` endet mit "
                               f"Code {code}, erlaubt {erlaubt}: {aus[-200:]}")
        return _befund("Installation in Wegwerf-Heim", True,
                       f"{anzahl} Dateien ausgepackt, {len(proben)} Befehle laufen")


def _pruef_platzanweiser() -> dict:
    """Der Waechter muss anhalten, danach durchlassen - und nie abstuerzen.

    Gespielt wird mit einem Wegwerf-Projekt in einem Wegwerf-Heim: ein
    Ordner mit KARTE.md und karte.json, nichts Echtes.
    """
    einstieg = PLUGIN / "bin" / "platzanweiser"
    if not einstieg.exists():
        return _befund("Platzanweiser", False, "bin/platzanweiser fehlt")
    with tempfile.TemporaryDirectory(prefix="landkarte-wache-") as ordner:
        o = Path(ordner)
        heim = o / "heim"
        (heim / ".landkarte").mkdir(parents=True)
        projekt = o / "wegwerfprojekt"
        (projekt / ".landkarte").mkdir(parents=True)
        (projekt / "KARTE.md").write_text("# Wegwerfprojekt\n", "utf-8")
        (projekt / ".landkarte" / "karte.json").write_text(json.dumps({
            "name": "wegwerfprojekt", "wurzel": str(projekt), "zweck": "Probe",
            "dateien": [{"pfad": "a.py", "zweck": "Zweck von a",
                         "symbole": [{"name": "tu_was", "zeile": 7}]},
                        {"pfad": "b.py", "zweck": "Zweck von b",
                         "symbole": [{"name": "noch_was", "zeile": 3}]}],
        }), "utf-8")
        (projekt / "a.py").write_text("def tu_was():\n    pass\n", "utf-8")
        (projekt / "b.py").write_text("def noch_was():\n    pass\n", "utf-8")

        def frage(datei: str, sitzung: str = "pruefung",
                  befehl: str = "") -> tuple[int, str]:
            eingabe = json.dumps({
                "session_id": sitzung, "cwd": str(projekt),
                "tool_name": "Bash" if befehl else "Read",
                "tool_input": ({"command": befehl} if befehl
                               else {"file_path": str(projekt / datei)})})
            umgebung = dict(os.environ, HOME=str(heim))
            try:
                e = subprocess.run([sys.executable, "-I", str(einstieg)],
                                   input=eingabe, text=True,
                                   capture_output=True, timeout=30,
                                   env=umgebung)
                return e.returncode, e.stdout.strip()
            except Exception as fehler:               # noqa: BLE001
                return 1, f"{type(fehler).__name__}: {fehler}"

        code, erste = frage("a.py")
        if code != 0:
            return _befund("Platzanweiser", False,
                           f"erster Aufruf endet mit Code {code}")
        try:
            daten = json.loads(erste)["hookSpecificOutput"]
        except Exception:                             # noqa: BLE001
            return _befund("Platzanweiser", False,
                           f"erste Antwort ist kein Hook-JSON: {erste[:120]}")
        if daten.get("permissionDecision") != "deny":
            return _befund("Platzanweiser", False,
                           "haelt beim ersten Zugriff nicht an: "
                           f"{daten.get('permissionDecision')}")
        grund = daten.get("permissionDecisionReason", "")
        for erwartet in ("Zweck von a", "tu_was", "wegwerfprojekt"):
            if erwartet not in grund:
                return _befund("Platzanweiser", False,
                               f"die Auskunft nennt {erwartet!r} nicht")

        code, zweite = frage("b.py")
        if code != 0:
            return _befund("Platzanweiser", False,
                           f"zweiter Aufruf endet mit Code {code}")
        if '"deny"' in zweite:
            return _befund("Platzanweiser", False,
                           "haelt zweimal an - das gehoert sich nicht")
        if "Zweck von b" not in zweite:
            return _befund("Platzanweiser", False,
                           f"reicht den Eintrag nicht nach: {zweite[:120]}")

        # Die Tuer, die beim ersten Live-Test benutzt wurde: `cat datei.py`.
        # Ein Waechter, der nur die Lesewerkzeuge kennt, ist Zierde.
        code, dritte = frage("", sitzung="bash-probe",
                             befehl=f"cat -n {projekt / 'a.py'}")
        if code != 0 or '"deny"' not in dritte:
            return _befund("Platzanweiser", False,
                           "`cat datei.py` kommt am Waechter vorbei")
        # Was keine Quelldatei liest, muss durchgehen
        for harmlos in (f"ls -la {projekt}", "landkarte wo probe",
                        f"git -C {projekt} status"):
            code, antwort = frage("", sitzung="harmlos-probe", befehl=harmlos)
            if code != 0 or antwort.strip():
                return _befund("Platzanweiser", False,
                               f"haelt bei einem harmlosen Befehl an: {harmlos}")

        # Unsinn auf der Eingabe darf nichts kaputtmachen
        umgebung = dict(os.environ, HOME=str(heim))
        e = subprocess.run([sys.executable, "-I", str(einstieg)],
                           input="kein JSON", text=True, capture_output=True,
                           timeout=30, env=umgebung)
        if e.returncode != 0 or e.stdout.strip():
            return _befund("Platzanweiser", False,
                           "kaputte Eingabe wird nicht durchgelassen")
        return _befund("Platzanweiser", True,
                       "haelt einmal an mit Auskunft (auch bei `cat`), danach "
                       "nur noch Hinweise, harmlose Befehle gehen durch")


def _pruef_karte() -> dict:
    from . import pruefer
    try:
        maengel = pruefer.karte_zusicherungen(WURZEL)
    except Exception as fehler:                       # noqa: BLE001
        return _befund("Eigenes Inhaltsverzeichnis", False,
                       f"{type(fehler).__name__}: {fehler}", hart=False)
    schwer = [m for m in maengel if m.get("schwere") == "schwer"]
    return _befund("Eigenes Inhaltsverzeichnis", not schwer,
                   "; ".join(f"{m['befund']} ({m['ort']})" for m in schwer),
                   hart=False)


PRUEFUNGEN = (
    _pruef_arbeitsbaum,
    _pruef_fassungen,
    _pruef_syntax,
    _pruef_hilfe,
    _pruef_geheimnisse,
    _pruef_paket,
    _pruef_installation,
    _pruef_platzanweiser,
    _pruef_karte,
)


def pruefen() -> dict:
    """Alles pruefen, ohne irgendetwas zu aendern."""
    heim = Path.home()
    vorher = set(os.listdir(heim))
    beginn = time.time()
    befunde = list(_pruef_herkunft())
    if all(b["ok"] for b in befunde):
        for pruefung in PRUEFUNGEN:
            try:
                befunde.append(pruefung())
            except Exception as fehler:               # noqa: BLE001
                befunde.append(_befund(
                    pruefung.__name__.replace("_pruef_", ""), False,
                    f"Pruefung selbst gescheitert: {type(fehler).__name__}: {fehler}"))
    neu = sorted(set(os.listdir(heim)) - vorher)
    if neu:
        befunde.append(_befund(
            "Pruefen bleibt folgenlos", False,
            f"im echten Heimverzeichnis ist etwas entstanden: {', '.join(neu[:5])}"))
    return {
        "befunde": befunde,
        "dauer_s": round(time.time() - beginn, 1),
        "bestanden": all(b["ok"] or not b["hart"] for b in befunde),
        "warnungen": [b for b in befunde if not b["ok"] and not b["hart"]],
    }


# -------------------------------------------------------------------- Stand

def ist_original() -> bool:
    """Steht wir im Repository selbst oder in einer installierten Kopie?"""
    code, aus = _git("rev-parse", "--show-toplevel")
    return code == 0 and Path(aus).resolve() == WURZEL.resolve()


def stand() -> dict:
    """Was liegt hier, was liegt auf GitHub, was waere noch nicht draussen."""
    lokal = fassung()
    veroeffentlicht, grund = _fassung_auf_github()
    if not ist_original():
        # Installierte Kopie: kein git, nichts freizugeben. Gefragt wird nach
        # der hoechsten Markierung, nicht nach der Rohdatei - sonst raet eine
        # aktuelle Installation zum Rueckschritt auf eine aeltere Fassung.
        neuste, marke_fehler = neueste_markierung()
        return {"lokal": lokal, "veroeffentlicht": veroeffentlicht,
                "abruf_fehler": grund, "letzter_tag": "", "tags": [],
                "offene_commits": [], "ungeschoben": [], "kopie": True,
                "neuste": neuste, "marke_draussen": None,
                "marke_fehler": marke_fehler,
                "rueckstand": bool(neuste) and als_zahlen(neuste) > als_zahlen(lokal),
                "gleich": bool(neuste) and als_zahlen(neuste) <= als_zahlen(lokal)}
    code, letzter = _git("describe", "--tags", "--abbrev=0")
    tag = letzter if code == 0 else ""
    bereich = f"{tag}..HEAD" if tag else "HEAD"
    code, log = _git("log", "--oneline", "--no-decorate", bereich)
    offen = [z for z in log.splitlines() if z.strip()] if code == 0 else []
    code, nicht_geschoben = _git("log", "--oneline", "--no-decorate",
                                 f"origin/{ZWEIG}..HEAD")
    ungeschoben = ([z for z in nicht_geschoben.splitlines() if z.strip()]
                   if code == 0 else [])
    code, alle_tags = _git("tag", "--sort=-v:refname")
    draussen, marke_fehler = _markierung_draussen(lokal)
    return {
        "kopie": False,
        "marke_draussen": draussen,
        "marke_fehler": marke_fehler,
        "lokal": lokal,
        "veroeffentlicht": veroeffentlicht,
        "abruf_fehler": grund,
        "letzter_tag": tag,
        "tags": [z for z in alle_tags.splitlines() if z.strip()][:8],
        "offene_commits": offen,
        "ungeschoben": ungeschoben,
        "gleich": bool(veroeffentlicht) and veroeffentlicht == lokal,
    }


# ---------------------------------------------------------------- Freigeben

def _aenderungen_schreiben(neu: str, commits: list[str], text: str) -> None:
    """Den neuen Abschnitt oben einhaengen - aber unter das Vorwort."""
    vorhanden = (AENDERUNGEN.read_text("utf-8").splitlines()
                 if AENDERUNGEN.exists() else ["# Änderungen", ""])
    # Einfuegestelle: vor der ersten Fassungsueberschrift. Titel und Vorwort
    # stehen davor und bleiben, wo sie sind.
    stelle = len(vorhanden)
    for nummer, zeile in enumerate(vorhanden):
        if zeile.startswith("## "):
            stelle = nummer
            break
    abschnitt = [f"## {neu} — {time.strftime('%Y-%m-%d')}", ""]
    if text:
        abschnitt += [text, ""]
    for commit in commits:
        teile = commit.split(" ", 1)
        abschnitt.append(f"- {teile[1] if len(teile) > 1 else commit}")
    if not commits and not text:
        abschnitt.append("- (keine Commits seit der letzten Fassung)")
    abschnitt.append("")
    vorher = vorhanden[:stelle]
    while vorher and not vorher[-1].strip():
        vorher.pop()
    AENDERUNGEN.write_text(
        "\n".join(vorher + [""] + abschnitt + vorhanden[stelle:]).rstrip() + "\n",
        "utf-8")


def freigeben(stufe: str | None = None, genau: str | None = None,
              text: str = "", jetzt: bool = False,
              ohne_pruefung: bool = False) -> dict:
    """Eine Fassung vorbereiten und auf Wunsch hochladen.

    Ohne `jetzt` wird nichts geschrieben und nichts geschoben - es wird nur
    gezeigt, was passieren wuerde.
    """
    ergebnis: dict = {"jetzt": jetzt, "schritte": []}

    def schritt(was: str) -> None:
        ergebnis["schritte"].append(was)

    if genau:
        neu = genau
        if not re.fullmatch(r"\d+\.\d+\.\d+", neu):
            return {**ergebnis, "fehler": f"Fassung muss wie 1.2.3 aussehen, nicht {neu!r}"}
    else:
        try:
            neu = naechste(stufe or "fehler")
        except ValueError as fehler:
            return {**ergebnis, "fehler": str(fehler)}
    alt = fassung()
    ergebnis["alt"], ergebnis["neu"] = alt, neu

    if not ohne_pruefung:
        bericht = pruefen()
        ergebnis["pruefung"] = bericht
        if not bericht["bestanden"]:
            ergebnis["fehler"] = "Pruefung nicht bestanden - nichts geaendert"
            return ergebnis

    code, letzter = _git("describe", "--tags", "--abbrev=0")
    tag = letzter if code == 0 else ""
    code, log = _git("log", "--oneline", "--no-decorate",
                     f"{tag}..HEAD" if tag else "HEAD")
    commits = [z for z in log.splitlines() if z.strip()] if code == 0 else []
    ergebnis["commits"] = commits

    if not jetzt:
        schritt(f"Fassung {alt} -> {neu} in plugin.json und lk/__init__.py")
        schritt("Einzeldatei brainbook-einrichten.py neu bauen")
        schritt(f"AENDERUNGEN.md ergaenzen ({len(commits)} Commits)")
        schritt(f"commit \"Fassung {neu}\" und Markierung v{neu}")
        schritt(f"git push origin {ZWEIG} --follow-tags")
        ergebnis["probe"] = True
        return ergebnis

    if f"v{neu}" in (_git("tag")[1] or "").splitlines():
        ergebnis["fehler"] = f"Markierung v{neu} gibt es schon"
        return ergebnis

    geaendert = fassung_setzen(neu)
    schritt(f"Fassung {alt} -> {neu} ({', '.join(geaendert)})")

    code, aus = _lauf([sys.executable, str(PAKETBAUER)])
    if code != 0:
        ergebnis["fehler"] = f"Paketbauer scheitert: {aus[-300:]}"
        return ergebnis
    schritt("Einzeldatei neu gebaut")

    _aenderungen_schreiben(neu, commits, text)
    schritt("AENDERUNGEN.md ergaenzt")

    code, aus = _git("add", "-A")
    if code != 0:
        ergebnis["fehler"] = f"git add scheitert: {aus}"
        return ergebnis
    nachricht = f"Fassung {neu}" + (f" — {text}" if text else "")
    code, aus = _git("commit", "-m", nachricht)
    if code != 0 and "nothing to commit" not in aus:
        ergebnis["fehler"] = f"git commit scheitert: {aus}"
        return ergebnis
    schritt(f"commit: {nachricht}")

    code, aus = _git("tag", "-a", f"v{neu}", "-m", nachricht)
    if code != 0:
        ergebnis["fehler"] = f"git tag scheitert: {aus}"
        return ergebnis
    schritt(f"Markierung v{neu} gesetzt")

    code, aus = _git("push", "origin", ZWEIG, "--follow-tags", zeit=180)
    ergebnis["geschoben"] = code == 0
    if code != 0:
        ergebnis["fehler"] = ("Hochladen gescheitert - Fassung ist lokal fertig "
                              f"und kann mit `git push origin {ZWEIG} "
                              f"--follow-tags` nachgeholt werden: {aus[-300:]}")
        return ergebnis
    schritt(f"nach {HERKUNFT} geschoben")
    ergebnis["fertig"] = True
    return ergebnis
