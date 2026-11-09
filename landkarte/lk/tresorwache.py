"""Zweck: Passwoerter im Gespraech erkennen, in den Tresor legen, aus dem
Verlauf entfernen.

Das ist die **einzige** Stelle im ganzen Werkzeug, die etwas aus dem
Sitzungsprotokoll loeschen darf. Sie loescht auch nichts, sondern ersetzt: aus
dem Geheimnis wird ein Verweis auf den Tresoreintrag. Der Satz drumherum
bleibt lesbar, die Sitzung bleibt nachvollziehbar, nur der Klartext ist weg.

Grenze, die man kennen muss: Ein `UserPromptSubmit`-Hook kann den Prompt nicht
umschreiben (das kann nur `PreToolUse` mit `updatedInput`). Das eine Mal, in
dem das Passwort getippt wird, sieht das Modell es also noch. Was der Waechter
verhindert, ist das Weiterleben: in der Protokolldatei, in der Chronik, in
jeder spaeteren Auswertung und in jedem Kontext, der daraus gebaut wird.

Vor jeder Aenderung wird eine Kopie in ~/.Papierkorb-Claude/tresorwache/
abgelegt - nach Jans Regel wird nichts dauerhaft geloescht.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path

from . import konfig, schwaerzen, tresor

PAPIERKORB = Path.home() / ".Papierkorb-Claude" / "tresorwache"
PROTOKOLL = konfig.LK_HEIM / "tresorwache.jsonl"
MIN_LAENGE = 8

# Woerter, die wie ein Geheimnis aussehen, aber keines sind.
UNVERDAECHTIG = {
    "passwort", "password", "geheim", "secret", "token", "changeme",
    "beispiel", "example", "platzhalter", "placeholder", "xxxxxxxx",
    "dein-passwort", "dein_passwort", "meinpasswort", "null", "none",
    "undefined", "true", "false", "redacted", "hidden",
}

# ---------------------------------------------------------------------------
# Was NIE ein Geheimnis ist.
#
# Der erste Entwurf nahm "mischt Ziffern und Buchstaben oder laenger als 20"
# als Kennzeichen. Beim Probelauf ueber ein Sitzungsprotokoll fand er damit
# 155 "Geheimnisse" und haette 12.788 Stellen ersetzt - lauter UUIDs,
# Zeitstempel, Pruefsummen und JSON-Feldnamen. Ein Waechter, der zu viel
# erkennt, zerstoert den Verlauf, den er schuetzen soll. Deshalb jetzt
# umgekehrt: erst ausschliessen, dann nur noch bei klarem Beleg zugreifen.
# ---------------------------------------------------------------------------
_UUID = re.compile(r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                   r"[0-9a-f]{4}-[0-9a-f]{12}$")
_NUR_HEX = re.compile(r"(?i)^[0-9a-f]{16,}$")       # Pruefsummen, Commit-Ids
_NUR_ZIFFERN = re.compile(r"^[0-9.,:+\-]+$")        # Zeitstempel, Zahlen
_PFAD = re.compile(r"[/\\]")                        # Dateipfade, URLs
_VERSION = re.compile(r"^v?\d+\.\d+")
_BEZEICHNER = re.compile(r"(?i)^(toolu|msg|req|run|sess|call)_")

_FELDNAMEN = {
    "uuid", "timestamp", "requestid", "sessionid", "parentuuid", "type",
    "stderr", "stdout", "status", "statuscode", "model", "role", "content",
    "name", "id", "index", "version", "usage", "stopreason", "isapierrormessage",
    "tooluseid", "toolusereuslt", "signature", "thinking", "cwd", "gitbranch",
}


# Wie Menschen im Gespraech ein Passwort nennen. Die Muster in schwaerzen.py
# sind fuer Befehlszeilen und Konfigurationsdateien gebaut ("PASSWORT=geheim").
# Im Chat steht aber "Das Passwort ist geheim" - und genau dort wird es getippt.
_SATZMUSTER = (
    re.compile(
        r"(?i)\b(?:pass(?:wor[dt])?|pw|kennwort|zugangscode|geheimcode|pin|"
        r"token|api[\-_ ]?key|schluessel|schlüssel)\b"
        r"[^\n\r]{0,30}?"
        r"(?:\bist\b|\blautet\b|\bwaere\b|\bwäre\b|[:=]|\bheisst\b|\bheißt\b)"
        r"\s*[\"'«»]?\s*([^\s\"'«»,;]{6,80})"),
    re.compile(
        r"(?i)\b(?:pass(?:wor[dt])?|pw|kennwort)\b\s+"
        r"[\"']?([A-Za-z0-9][^\s\"',;]{5,79})"),
    re.compile(r"(?i)\b(?:login|zugang|anmeldung)\b[^\n]{0,20}?"
               r"[\s:]([^\s:/]{3,40}):([^\s]{6,80})"),
)


def _aus_saetzen(text: str) -> set[str]:
    gefunden: set[str] = set()
    for muster in _SATZMUSTER:
        for treffer in muster.finditer(text):
            for wert in treffer.groups():
                if wert:
                    # '!' und '?' NICHT abschneiden: beides sind haeufige
                    # Zeichen in Passwoertern. Ein abgeschnittenes Zeichen
                    # waere schlimmer als ein Satzzeichen zu viel.
                    gefunden.add(wert.strip(".,;:\"'»«)("))
    return gefunden


def _ist_echtes_geheimnis(wert: str) -> bool:
    """Grobfilter. Im Zweifel NEIN - lieber ein Passwort uebersehen als den
    Verlauf mit falschen Ersetzungen unlesbar machen. Das Uebersehene faengt
    der naechste Lauf mit einem schaerferen Muster; eine falsche Ersetzung
    bleibt."""
    if not (MIN_LAENGE <= len(wert) <= 120):
        return False
    if wert.lower() in UNVERDAECHTIG or wert.lower() in _FELDNAMEN:
        return False
    if wert.startswith(("***", "<", "{", "$", "[Tresor:", "--", "#")):
        return False
    if " " in wert or "\t" in wert:
        return False
    if _UUID.match(wert) or _NUR_HEX.match(wert) or _NUR_ZIFFERN.match(wert):
        return False
    if _PFAD.search(wert) or _VERSION.match(wert) or _BEZEICHNER.match(wert):
        return False
    # Reine Woerter ohne Ziffern sind fast immer Satzteile, keine Passwoerter.
    if not any(z.isdigit() for z in wert) and not any(
            z in wert for z in "!@#$%^&*()_+=~?"):
        return False
    return True


# Fuellwoerter, die als Name nichts taugen.
_FUELLWORT = {
    "ist", "sind", "war", "lautet", "heisst", "heißt", "waere", "wäre",
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen",
    "und", "oder", "fuer", "für", "mit", "von", "zum", "zur", "auf", "in",
    "mein", "meine", "dein", "deine", "hier", "bitte", "noch", "auch",
    "nur", "als", "wie", "dann", "neue", "neues", "neuer", "alte", "altes",
}
# Die Art des Geheimnisses - taucht fast immer im Satz auf.
_ART = re.compile(r"(?i)\b(pass(?:wor[dt])?|pw|kennwort|token|api[\-_ ]?key|"
                  r"zugangscode|geheimcode|pin|schluessel|schlüssel|secret)\b")


def _namensvorschlag(text: str, wert: str, quelle: str) -> str:
    """Einen sprechenden Namen aus dem Satz rundherum ableiten.

    Reihenfolge: ein Schluesselname direkt vor dem Wert (ETM_LOGIN_PASSWORT=...)
    schlaegt alles. Sonst wird die Art des Geheimnisses mit dem naechsten
    sinntragenden Wort davor verbunden - aus "Das Passwort fuer Strato ist X"
    wird "strato-passwort". Fuellwoerter zaehlen nicht, sonst heisst jeder
    Eintrag "ist".
    """
    stelle = text.find(wert)
    davor = text[max(0, stelle - 160):stelle] if stelle >= 0 else text[:160]

    # 1. Schluessel=Wert: der Schluessel ist der beste Name, den es gibt.
    treffer = re.search(r"([A-Za-z][A-Za-z0-9_.\-]{2,48})\s*[\"']?\s*[:=]\s*[\"']?$",
                        davor)
    if treffer and not treffer.group(1).lower() in _FUELLWORT:
        return _saeubern(treffer.group(1))

    # 2. Art des Geheimnisses + naechstes sinntragendes Wort davor.
    art_treffer = list(_ART.finditer(davor))
    art = ""
    if art_treffer:
        roh = art_treffer[-1].group(1).lower()
        art = {"pass": "passwort", "passwort": "passwort", "password": "passwort",
               "passwort": "passwort", "pw": "passwort", "kennwort": "passwort",
               "schluessel": "schluessel", "schlüssel": "schluessel",
               "api key": "api-key", "api-key": "api-key", "apikey": "api-key",
               }.get(roh, roh)
    # Der Gegenstand steht mal vor, mal hinter dem Artwort ("Passwort fuer
    # Strato" gegen "Strato-Passwort"). Deshalb der ganze Satzanfang, nur
    # ohne Fuellwoerter und ohne die Artwoerter selbst.
    woerter = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_.\-]{2,}", davor)
               if w.lower() not in _FUELLWORT and not _ART.fullmatch(w)]
    gegenstand = woerter[-1] if woerter else ""
    teile = [t for t in (_saeubern(gegenstand), art) if t]
    if teile:
        return "-".join(dict.fromkeys(teile))[:40]
    return _saeubern(quelle) or "geheimnis"


def _saeubern(roh: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", (roh or "").lower()).strip("-")
    return name[:40]


# ---------------------------------------------------------------------------
# Zwei Scharfstellungen, und das ist der Kern der Sache.
#
# Im Chat tippt ein Mensch "Das Passwort ist X" - dort duerfen Satzmuster
# raten, denn ein Fehlgriff kostet einen ueberfluessigen Tresoreintrag.
#
# Beim Rundgang ueber Sitzungsprotokolle liegt derselbe Satz tausendfach in
# Code, Ausgaben und Beispielen - dieses Projekt ist auf Deutsch geschrieben,
# "passwort" steht in jeder zweiten Zeile. Ein Fehlgriff ersetzt dort echten
# Text. Deshalb greift der Rundgang nur bei Formen, die nichts anderes sein
# koennen, plus bei Werten, die schon im Tresor liegen.
# ---------------------------------------------------------------------------
_STARKE_MUSTER = (
    # sk-ant-… und Verwandte. Die alte Fassung "sk-" plus 18 Zeichen fing auch
    # "sk-ssh-ed25519@openssh.com" aus einer SSH-Zeile - daher jetzt die
    # Anbieter-Vorsilbe und eine Mindestlaenge, die echte Schluessel haben.
    re.compile(r"\bsk-(?:ant|proj|live|test)-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{14,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{14,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{6,}"),
    # Anmeldedaten in einer URL - der Teil zwischen ':' und '@'
    re.compile(r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s:/@]+:([^\s@/]{6,})@"),
    # Genau die Umgebungsvariablen, die nichts anderes als ein Geheimnis
    # enthalten koennen.
    re.compile(r"\b(?:PGPASSWORD|MYSQL_PWD|ANTHROPIC_API_KEY|OPENAI_API_KEY|"
               r"AWS_SECRET_ACCESS_KEY|SUPABASE_SERVICE_ROLE_KEY)="
               r"[\"']?([^\s\"'`;|&]{8,})"),
)

# Was nie der Wert eines Geheimnisses sein kann, auch wenn das Muster passt.
# Klammern, spitze Klammern und Satzzeichen kommen in Schluesseln nicht vor,
# in Code dafuer staendig: beim Probelauf fing die Umgebungsvariablen-Regel so
# das Bruchstueck ").replace(" aus einer Python-Zeile.
_KEIN_WERT = re.compile(r"[$`\"'\\(){}<>\[\],;]|\*\*\*|\$\{|%[A-Z_]+%")


def _aus_starken(text: str) -> set[str]:
    gefunden: set[str] = set()
    for muster in _STARKE_MUSTER:
        for treffer in muster.finditer(text):
            wert = treffer.group(1) if treffer.groups() else treffer.group(0)
            if not wert:
                continue
            # Umschliessende Anfuehrungszeichen gehoeren nicht zum Geheimnis.
            # Beim ersten Lauf landete PGPASSWORD='geheim!' samt Hochkommata
            # im Tresor - der Wert passte danach auf nichts mehr.
            wert = wert.strip("\"'")
            # Shell-Verweise ($VAR, ${VAR}) und schon Geschwaerztes sind keine
            # Geheimnisse, sondern Platzhalter.
            if not (MIN_LAENGE <= len(wert) <= 200) or _KEIN_WERT.search(wert):
                continue
            # Ein Schluessel enthaelt Ziffern oder ist lang. Ohne diese
            # Schranke fing die Umgebungsvariablen-Regel auch Woerter wie
            # "env.example" ein, die nur zufaellig hinter einem '=' standen.
            if not any(z.isdigit() for z in wert) and len(wert) < 20:
                continue
            gefunden.add(wert)
    return gefunden


def finden(text: str, streng: bool = False) -> list[str]:
    """Alle Werte, die wie ein Geheimnis aussehen - laengste zuerst."""
    if not text:
        return []
    # Starke Treffer sind durch ihre Form schon eindeutig - ein AWS-Schluessel
    # enthaelt '/' und '+', und genau daran haette der Grobfilter ihn als
    # Dateipfad verworfen. Sie gehen deshalb am Grobfilter vorbei; geprueft
    # wurden sie bereits in _aus_starken.
    stark = _aus_starken(text)
    if streng:
        return sorted(stark, key=len, reverse=True)
    schwach = {w for w in (schwaerzen._aus_text_ziehen(text) | _aus_saetzen(text))
               if _ist_echtes_geheimnis(w)}
    kandidaten = stark | schwach
    # Teilstuecke entfernen: steht "abc123" in "abc123xyz", reicht das laengere.
    aus = []
    for wert in sorted(kandidaten, key=len, reverse=True):
        if not any(wert in schon and wert != schon for schon in aus):
            aus.append(wert)
    return aus


# Felder eines Sitzungsprotokolls, in denen Menschen und Modell wirklich
# schreiben. Alles andere ist Geruest - und genau dort stecken die UUIDs und
# Pruefsummen, die beim ersten Entwurf als Geheimnis durchgingen.
_TEXTFELDER = ("text", "command", "content", "prompt", "description")


def texte_aus_zeile(zeile: str) -> list[str]:
    """Aus einer JSONL-Zeile nur das herausholen, was geschrieben wurde."""
    zeile = zeile.strip()
    if not zeile or not zeile.startswith("{"):
        return [zeile] if zeile else []
    try:
        satz = json.loads(zeile)
    except json.JSONDecodeError:
        return []
    aus: list[str] = []

    def sammeln(knoten, schluessel=""):
        if isinstance(knoten, str):
            if schluessel in _TEXTFELDER and len(knoten) < 200_000:
                aus.append(knoten)
        elif isinstance(knoten, dict):
            for k, v in knoten.items():
                sammeln(v, k)
        elif isinstance(knoten, list):
            for v in knoten:
                sammeln(v, schluessel)

    sammeln(satz)
    return aus


def aufnehmen(text: str, quelle: str = "") -> list[tuple[str, str]]:
    """Gefundene Geheimnisse in den Tresor legen. Gibt [(Name, Wert)] zurueck."""
    werte = finden(text)
    if not werte:
        return []
    abgelegt = []
    for wert in werte:
        name = _namensvorschlag(text, wert, quelle)
        try:
            vergeben, _neu = tresor.einlegen(name, wert, herkunft=quelle)
        except tresor.TresorFehler:
            continue
        abgelegt.append((vergeben, wert))
    return abgelegt


# --------------------------------------------------------------- Verlauf


def _sicherungskopie(datei: Path) -> Path:
    PAPIERKORB.mkdir(parents=True, exist_ok=True)
    ziel = PAPIERKORB / f"{datei.name}.{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(datei, ziel)
    os.chmod(ziel, 0o600)
    return ziel


def verlauf_saeubern(datei: Path, paare: list[tuple[str, str]],
                     trocken: bool = False) -> dict:
    """Geheimnisse im Sitzungsprotokoll durch ihren Tresornamen ersetzen.

    Zeilenweise, nicht am Stueck: Sitzungsprotokolle werden gross - auf diesem
    Rechner liegt eines mit 2,1 GB. Wer so eine Datei in einen String liest,
    braucht mehr Speicher als die Datei gross ist und haelt die Maschine an.
    `.jsonl` ist ohnehin zeilenweise aufgebaut.

    Ersetzt wird der Klartext und die JSON-escapete Fassung - ein Geheimnis
    steht in diesen Dateien in beiden Formen.
    """
    if not datei.exists() or not paare:
        return {"datei": str(datei), "ersetzt": 0, "geaendert": False}

    formen: list[tuple[str, str]] = []
    for name, wert in paare:
        verweis = f"[Tresor: {name}]"
        for form in (wert, json.dumps(wert)[1:-1]):
            if form and (form, verweis) not in formen:
                formen.append((form, verweis))

    anzahl = 0
    if trocken:
        with datei.open("r", encoding="utf-8", errors="replace") as f:
            for zeile in f:
                for form, _ in formen:
                    if form in zeile:
                        anzahl += zeile.count(form)
        return {"datei": str(datei), "ersetzt": anzahl, "geaendert": False,
                "trocken": True}

    vorlaeufig = datei.with_suffix(datei.suffix + ".tresorwache")
    with datei.open("r", encoding="utf-8", errors="replace") as quelle, \
            vorlaeufig.open("w", encoding="utf-8") as ziel:
        for zeile in quelle:
            for form, verweis in formen:
                if form in zeile:
                    anzahl += zeile.count(form)
                    zeile = zeile.replace(form, verweis)
            ziel.write(zeile)
    if anzahl == 0:
        vorlaeufig.unlink(missing_ok=True)
        return {"datei": str(datei), "ersetzt": 0, "geaendert": False}

    kopie = _sicherungskopie(datei)
    try:
        shutil.copystat(datei, vorlaeufig)
    except OSError:
        pass
    vorlaeufig.replace(datei)
    _merken({"zeit": int(time.time()), "datei": str(datei),
             "ersetzt": anzahl, "namen": [n for n, _ in paare],
             "sicherung": str(kopie)})
    return {"datei": str(datei), "ersetzt": anzahl, "geaendert": True,
            "sicherung": str(kopie)}


def _merken(eintrag: dict) -> None:
    try:
        konfig.LK_HEIM.mkdir(parents=True, exist_ok=True)
        with PROTOKOLL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        os.chmod(PROTOKOLL, 0o600)
    except OSError:
        pass


def protokoll(grenze: int = 20) -> list[dict]:
    if not PROTOKOLL.exists():
        return []
    zeilen = PROTOKOLL.read_text("utf-8", errors="replace").splitlines()
    aus = []
    for z in zeilen[-grenze:]:
        try:
            aus.append(json.loads(z))
        except json.JSONDecodeError:
            continue
    return aus


# --------------------------------------------------------------- Rundgang


def datei_pruefen(datei: Path, quelle: str = "", trocken: bool = False,
                  auch_laufende: bool = False, grenze_mb: int = 0) -> dict:
    """Eine Protokolldatei durchgehen: aufnehmen und ersetzen.

    Die **laufende** Sitzung wird beim Rundgang ausgelassen. Dort schreibt
    Claude Code staendig Zeilen an; wer die Datei einliest, ersetzt und
    zurueckschreibt, verliert alles, was in der Zwischenzeit dazukam. Im Hook
    ist das ungefaehrlich - er laeuft zwischen zwei Zuegen -, beim Rundgang
    nicht. Mit auch_laufende=True laesst es sich erzwingen.
    """
    if not datei.exists():
        return {"datei": str(datei), "gefunden": 0, "ersetzt": 0}
    if not auch_laufende and not trocken and ist_laufend(datei):
        return {"datei": str(datei), "gefunden": 0, "ersetzt": 0,
                "uebersprungen": "laeuft gerade"}
    groesse_mb = datei.stat().st_size / 1e6
    if grenze_mb and groesse_mb > grenze_mb:
        return {"datei": str(datei), "gefunden": 0, "ersetzt": 0,
                "uebersprungen": f"{groesse_mb:.0f} MB, ueber der Grenze"}

    # Suchen: zeilenweise, damit auch riesige Protokolle durchlaufen.
    # Bekannte Tresorwerte im selben Durchgang suchen - ersetzt wird spaeter
    # nur, was wirklich in der Datei steht. Alles andere einzusetzen hiesse,
    # eine Datei wegen eines Geheimnisses anzufassen, das gar nicht drin ist.
    try:
        bekannt = {e["geheimnis"]: name
                   for name, e in tresor.laden()["eintraege"].items()
                   if e.get("geheimnis")}
    except tresor.TresorFehler:
        bekannt = {}

    treffer: dict[str, str] = {}
    gesehen_bekannt: dict[str, str] = {}
    with datei.open("r", encoding="utf-8", errors="replace") as f:
        for zeile in f:
            for wert, name in bekannt.items():
                if wert not in gesehen_bekannt and wert in zeile:
                    gesehen_bekannt[wert] = name
            for stueck in texte_aus_zeile(zeile):
                for wert in finden(stueck, streng=True):
                    if wert not in treffer:
                        treffer[wert] = _namensvorschlag(stueck, wert,
                                                         quelle or datei.name)
    paare: list[tuple[str, str]] = []
    for wert, name in treffer.items():
        if trocken:
            paare.append((name, wert))
            continue
        try:
            vergeben, _neu = tresor.einlegen(name, wert,
                                             herkunft=quelle or datei.name)
        except tresor.TresorFehler:
            continue
        paare.append((vergeben, wert))

    # Dazu die schon bekannten Werte, die in dieser Datei auch wirklich
    # vorkommen: ein Passwort von gestern steht heute noch in alten Protokollen.
    alle = list(paare)
    schon = {w for _, w in alle}
    for wert, name in gesehen_bekannt.items():
        if wert not in schon:
            alle.append((name, wert))

    ergebnis = verlauf_saeubern(datei, alle, trocken=trocken)
    ergebnis["gefunden"] = len(paare)
    ergebnis["namen"] = sorted({n for n, _ in paare})
    return ergebnis


def laufende_sitzung() -> str | None:
    """Kennung der Sitzung, in der wir gerade stecken."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or None


def ist_laufend(datei: Path) -> bool:
    kennung = laufende_sitzung()
    return bool(kennung) and datei.stem == kennung


def sitzungen(projekt_slug: str | None = None) -> list[Path]:
    """Alle Sitzungsprotokolle von Claude Code."""
    wurzel = Path.home() / ".claude" / "projects"
    if not wurzel.is_dir():
        return []
    ordner = [wurzel / projekt_slug] if projekt_slug else list(wurzel.iterdir())
    aus: list[Path] = []
    for o in ordner:
        if o.is_dir():
            aus.extend(sorted(o.glob("*.jsonl")))
    return aus
