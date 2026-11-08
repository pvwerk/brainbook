"""Zweck: Ein Projekt einlesen und als Datenmodell zurueckgeben."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections import deque
from pathlib import Path

from . import konfig, sprachen

URL_MUSTER = re.compile(r"https?://[\w.\-]+(?:/[\w.\-/%?=&~+#]*)?")
# Bezeichner im Text - einmal je Datei gesammelt, statt jede Datei gegen
# jeden Dateinamen zu pruefen (das war quadratisch und dauerte Minuten).
TOKEN_MUSTER = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]{3,}")
MAX_TOKEN = 8000
IP_MUSTER = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SSH_MUSTER = re.compile(r"\bssh\s+(?:-\w+\s+\S+\s+)*([\w.\-]+@?[\w.\-]+)")
URL_MUELL = ("shields.io", "img.shields", "badge", "schema.org", "w3.org",
             "github.com/anthropics", "localhost", "127.0.0.1", "example.com",
             "fonts.googleapis", "googleapis.com", "licenses/", "spdx.org")

BEFEHL_ANFANG = re.compile(
    r"^\s*(?:\$\s*)?((?:\./|~/|/)?[\w.\-/]*(?:python3?|pip3?|pytest|uv|uvicorn|"
    r"node|npm|npx|pnpm|yarn|bun|make|docker|git|ssh|scp|rsync|lftp|bash|sh|"
    r"caddy|systemctl|psql|supabase|php|composer|gunicorn|flask|django-admin|"
    r"manage\.py|bauen\.py|ausliefern|deploy)\b.*)$"
)


def _lesen(p: Path) -> str | None:
    try:
        if p.stat().st_size > konfig.MAX_DATEI:
            return None
        rohdaten = p.read_bytes()
    except OSError:
        return None
    if b"\x00" in rohdaten[:2048]:
        return None
    try:
        return rohdaten.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return rohdaten.decode("latin-1")
        except UnicodeDecodeError:
            return None


def _git_stand(wurzel: Path) -> dict:
    aus = {"zweig": "", "commit": "", "schmutzig": 0, "letzter": ""}
    if not (wurzel / ".git").exists():
        return aus
    def lauf(*args: str) -> str:
        try:
            e = subprocess.run(("git", "-C", str(wurzel)) + args,
                               capture_output=True, text=True, timeout=10)
            return e.stdout.strip() if e.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    aus["zweig"] = lauf("rev-parse", "--abbrev-ref", "HEAD")
    aus["commit"] = lauf("rev-parse", "--short", "HEAD")
    aus["letzter"] = lauf("log", "-1", "--format=%cs %s")
    schmutz = lauf("status", "--porcelain")
    aus["schmutzig"] = len([z for z in schmutz.splitlines() if z.strip()])
    return aus


def _git_ignoriert(wurzel: Path) -> set[str]:
    """Pfade, die Git ignoriert - also Erzeugnisse, keine Quellen.

    Ein Ordner wie site/ oder dist/ ist Bauausgabe. Nimmt man ihn in die
    Karte, verdraengt er die echten Quellen in der Rangfolge. Statt eine
    Namensliste zu pflegen, wird gefragt, was das Projekt selbst ignoriert.
    """
    if not (wurzel / ".git").exists():
        return set()
    try:
        ergebnis = subprocess.run(
            ("git", "-C", str(wurzel), "ls-files", "--others", "--ignored",
             "--exclude-standard", "--directory"),
            capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return set()
    if ergebnis.returncode != 0:
        return set()
    aus = set()
    for zeile in ergebnis.stdout.splitlines()[:4000]:
        zeile = zeile.strip().rstrip("/")
        if zeile:
            aus.add(zeile)
    return aus


def _eigene_ignorierliste(wurzel: Path) -> set[str]:
    """Zusaetzliche Ausnahmen, die nur dieses Projekt kennt."""
    datei = wurzel / ".landkarte" / "ignorieren.txt"
    if not datei.exists():
        return set()
    try:
        return {z.strip().rstrip("/") for z in datei.read_text("utf-8").splitlines()
                if z.strip() and not z.lstrip().startswith("#")}
    except OSError:
        return set()


def _dateien_sammeln(wurzel: Path, ignorieren: set[str],
                     ausnahmen: set[str] | None = None) -> list[Path]:
    """Dateien in Breitensuche sammeln: flach vor tief.

    Breitensuche, damit eine Obergrenze zuerst die tiefen Nebensachen
    abschneidet und nicht die Hauptsachen an der Wurzel. Punktordner werden
    uebersprungen - sonst frisst zum Beispiel .claude mit seinen
    Sitzungsprotokollen das ganze Budget.
    """
    ausnahmen = ausnahmen or set()
    gefunden: list[Path] = []
    schlange: deque[tuple[Path, tuple[str, ...]]] = deque([(wurzel, ())])
    while schlange and len(gefunden) < konfig.MAX_DATEIEN:
        ordner, rel = schlange.popleft()
        try:
            eintraege = sorted(os.scandir(ordner), key=lambda e: e.name)
        except OSError:
            continue
        unterordner: list[tuple[Path, tuple[str, ...]]] = []
        for eintrag in eintraege:
            name = eintrag.name
            try:
                ist_ordner = eintrag.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if ist_ordner:
                if name in ignorieren:
                    continue
                if name.startswith(".") and name not in konfig.PUNKTORDNER_ERLAUBT:
                    continue
                if rel == (".claude",) and name not in konfig.CLAUDE_ERLAUBT:
                    continue
                relpfad = "/".join(rel + (name,))
                if relpfad in ausnahmen or name in ausnahmen:
                    continue
                unterordner.append((Path(eintrag.path), rel + (name,)))
            else:
                if name == ".DS_Store":
                    continue
                if "/".join(rel + (name,)) in ausnahmen:
                    continue
                gefunden.append(Path(eintrag.path))
                if len(gefunden) >= konfig.MAX_DATEIEN:
                    break
        schlange.extend(unterordner)
    return gefunden


def _befehle_sammeln(wurzel: Path, dateien: list[dict]) -> list[dict]:
    befehle: list[dict] = []

    def hinzu(was: str, wie: str, quelle: str) -> None:
        wie = wie.strip()
        if not wie or len(wie) > 200:
            return
        for b in befehle:
            if b["wie"] == wie:
                return
        befehle.append({"was": was, "wie": wie, "quelle": quelle})

    namen = {d["pfad"] for d in dateien}

    # package.json
    pj = wurzel / "package.json"
    if pj.exists():
        text = _lesen(pj) or "{}"
        try:
            daten = json.loads(text)
            for name, wert in (daten.get("scripts") or {}).items():
                hinzu(name, f"npm run {name}", "package.json")
        except json.JSONDecodeError:
            pass

    # Python-Umgebung
    if (wurzel / ".venv/bin/python").exists():
        hinzu("python (Projektumgebung)", "./.venv/bin/python", ".venv")
        if (wurzel / ".venv/bin/pytest").exists():
            hinzu("testen", "./.venv/bin/python -m pytest -q", ".venv")
        if (wurzel / ".venv/bin/uvicorn").exists():
            hinzu("starten", "./.venv/bin/uvicorn app.main:app --reload", ".venv")
    elif (wurzel / "requirements.txt").exists() or (wurzel / "pyproject.toml").exists():
        hinzu("Umgebung anlegen", "python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt", "requirements.txt")

    # Makefile
    mk = wurzel / "Makefile"
    if mk.exists():
        text = _lesen(mk) or ""
        vorher = ""
        for zeile in text.splitlines():
            t = re.match(r"^([a-zA-Z_][\w.-]*):(?!=)", zeile)
            if t and not t.group(1).startswith("."):
                hinzu(vorher or t.group(1), f"make {t.group(1)}", "Makefile")
                vorher = ""
            elif zeile.startswith("#"):
                vorher = zeile.lstrip("# ").strip()[:60]

    # Skripte
    for d in dateien:
        p = Path(d["pfad"])
        if p.suffix == ".sh" and (len(p.parts) == 1 or p.parts[0] in ("scripts", "bin", "deploy", "tools")):
            hinzu(d.get("zweck") or p.stem.replace("_", " "), f"./{d['pfad']}", "Skript")

    # docker-compose
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        if (wurzel / name).exists():
            hinzu("Dienste starten", "docker compose up -d", name)
            hinzu("Protokoll", "docker compose logs -f", name)
            break

    # Einstiegs-Python
    for d in dateien:
        p = Path(d["pfad"])
        if p.suffix == ".py" and len(p.parts) == 1 and d.get("einstieg"):
            hinzu(d.get("zweck") or p.stem, f"python3 {d['pfad']}", "Einstiegspunkt")

    # Befehlszeilen aus README-Codebloecken
    for name in ("README.md", "readme.md", "NOTES.md", "docs/BETRIEB.md"):
        p = wurzel / name
        if not p.exists():
            continue
        text = _lesen(p) or ""
        in_block = False
        for zeile in text.splitlines():
            if zeile.strip().startswith("```"):
                in_block = not in_block
                continue
            if not in_block:
                continue
            kandidat = re.split(r"\s+#", zeile.strip(), maxsplit=1)[0].strip()
            if "  " in kandidat:
                continue          # Spaltenlayout, kein Befehl
            t = BEFEHL_ANFANG.match(kandidat)
            if t:
                hinzu("aus " + name, t.group(1).strip(), name)
            if len(befehle) > 28:
                break
    return befehle[:28]


def _adressen_sammeln(wurzel: Path, dateien: list[dict]) -> list[str]:
    zaehler: dict[str, int] = {}
    kandidaten = [d for d in dateien
                  if Path(d["pfad"]).suffix in (".md", ".txt", ".service",
                                                ".conf", ".json", ".yml",
                                                ".yaml")
                  or Path(d["pfad"]).name in ("Caddyfile", "README")]
    for d in kandidaten[:60]:
        text = _lesen(wurzel / d["pfad"])
        if not text:
            continue
        for treffer in URL_MUSTER.findall(text)[:120]:
            if any(m in treffer for m in URL_MUELL):
                continue
            treffer = treffer.rstrip(".,;:)\"'")
            zaehler[treffer] = zaehler.get(treffer, 0) + 1
        for treffer in SSH_MUSTER.findall(text)[:40]:
            zaehler["ssh " + treffer] = zaehler.get("ssh " + treffer, 0) + 1
        for treffer in IP_MUSTER.findall(text)[:40]:
            if treffer.startswith(("127.", "0.", "255.", "192.168.", "10.0.0.0")):
                continue
            zaehler[treffer] = zaehler.get(treffer, 0) + 1
    geordnet = sorted(zaehler.items(), key=lambda x: (-x[1], x[0]))
    return [a for a, _ in geordnet[:14]]


def _graph_bauen(dateien: list[dict], wurzel: Path) -> dict[str, list[str]]:
    """Verweise zwischen Dateien des Projekts.

    Statt jede Datei gegen jeden Dateinamen zu pruefen, wird je Datei einmal
    die Menge ihrer Bezeichner gebildet und mit der Menge der Dateinamen
    geschnitten. Das ist der Unterschied zwischen Minuten und Sekunden.
    """
    nach_modul: dict[str, str] = {}
    nach_stamm: dict[str, list[str]] = {}
    for d in dateien:
        pf = Path(d["pfad"])
        modul = ".".join(pf.with_suffix("").parts)
        nach_modul[modul] = d["pfad"]
        nach_modul.setdefault(pf.stem, d["pfad"])
        nach_stamm.setdefault(pf.stem, []).append(d["pfad"])
    staemme = {s for s in nach_stamm if len(s) >= 4}

    kanten: dict[str, list[str]] = {}
    for d in dateien:
        roh = d.pop("_roh_verweise", [])
        tokens = d.pop("_tokens", None) or set()
        ziele: list[str] = []

        for verweis in roh:                      # echte Importe zuerst
            name = verweis.strip("./").replace("/", ".")
            name = re.sub(r"\.(js|mjs|ts|php|py|html)$", "", name)
            for schluessel in (name, name.split(".")[-1]):
                if schluessel in nach_modul and nach_modul[schluessel] != d["pfad"]:
                    ziele.append(nach_modul[schluessel])
                    break

        eigener = Path(d["pfad"]).stem
        for stamm in tokens & staemme:           # Mengenschnitt statt Schleife
            if stamm == eigener:
                continue
            for ziel in nach_stamm[stamm]:
                if ziel != d["pfad"]:
                    ziele.append(ziel)

        eindeutig: list[str] = []
        for z in ziele:
            if z not in eindeutig:
                eindeutig.append(z)
        if eindeutig:
            kanten[d["pfad"]] = eindeutig[:konfig.MAX_EDGES_JE_DATEI]
    return kanten


EINSTIEG_NAMEN = {
    "main.py", "app.py", "cli.py", "manage.py", "__main__.py", "bauen.py",
    "index.html", "index.js", "index.ts", "server.js", "wsgi.py", "asgi.py",
    "main.js", "main.ts", "setup.py", "formular.php", "index.php",
}


def projekt_scannen(wurzel: Path, konf: dict | None = None) -> dict:
    """Vollstaendiges Datenmodell eines Projekts."""
    konf = konf or konfig.laden()
    wurzel = wurzel.resolve()
    ignorieren = set(konf.get("ignorieren", []))
    beginn = time.time()

    ausnahmen = _git_ignoriert(wurzel) | _eigene_ignorierliste(wurzel)
    rohdateien = _dateien_sammeln(wurzel, ignorieren, ausnahmen)
    dateien: list[dict] = []
    gesamt_zeilen = 0
    alle_markierungen: list[dict] = []
    neuste_aenderung = 0.0

    for p in rohdateien:
        rel = p.relative_to(wurzel).as_posix()
        if rel == "KARTE.md" or rel.startswith(".landkarte/"):
            continue      # eigene Erzeugnisse gehoeren nicht in die Karte
        try:
            stat = p.stat()
        except OSError:
            continue
        neuste_aenderung = max(neuste_aenderung, stat.st_mtime)
        eintrag: dict = {
            "pfad": rel,
            "groesse": stat.st_size,
            "geaendert": int(stat.st_mtime),
            "zeilen": 0,
            "zweck": "",
            "symbole": [],
            "einstieg": p.name in EINSTIEG_NAMEN,
        }
        if konfig.ist_text(p):
            text = _lesen(p)
            if text is not None:
                eintrag["zeilen"] = text.count("\n") + 1
                gesamt_zeilen += eintrag["zeilen"]
                eintrag["zweck"] = sprachen.zweck(text, p)
                eintrag["symbole"] = sprachen.symbole(text, p)
                eintrag["_roh_verweise"] = sprachen.rohverweise(text, p)
                treffer = TOKEN_MUSTER.findall(text)
                eintrag["_tokens"] = set(treffer[:MAX_TOKEN])
                for m in sprachen.markierungen(text):
                    alle_markierungen.append({**m, "pfad": rel})
        dateien.append(eintrag)

    kanten = _graph_bauen(dateien, wurzel)

    # Rang: wie oft wird eine Datei von anderen erwaehnt
    eingehend: dict[str, int] = {}
    for quelle, ziele in kanten.items():
        for z in ziele:
            eingehend[z] = eingehend.get(z, 0) + 1
    for d in dateien:
        rang = eingehend.get(d["pfad"], 0) * 2
        if d["einstieg"]:
            rang += 8
        if len(Path(d["pfad"]).parts) == 1:
            rang += 2
        rang += min(len(d["symbole"]), 10) / 4
        endung = Path(d["pfad"]).suffix.lower()
        if endung in (".md", ".txt", ".json", ".csv"):
            rang -= 2
        if Path(d["pfad"]).name.startswith("."):
            rang -= 2
        if endung in (".svg", ".png", ".jpg", ".jpeg", ".gif",
                      ".webp", ".ico", ".woff", ".woff2", ".ttf",
                      ".otf", ".pdf", ".map"):
            rang -= 6
        d["rang"] = round(rang, 2)
        d["eingehend"] = eingehend.get(d["pfad"], 0)

    befehle = _befehle_sammeln(wurzel, dateien)
    adressen = _adressen_sammeln(wurzel, dateien)

    for d in dateien:
        d.pop("_tokens", None)
        d.pop("_roh_verweise", None)

    zweck_projekt = ""
    # KARTE.md ist unsere eigene Ausgabe - daraus den Zweck zu lesen waere
    # ein Zirkelbezug und ergibt die "Stand"-Zeile.
    for name in ("README.md", "NOTES.md", "docs/PLAN.md", "docs/README.md"):
        p = wurzel / name
        if p.exists():
            text = _lesen(p) or ""
            for zeile in text.splitlines()[:30]:
                s = zeile.strip()
                if s.startswith("#"):
                    continue
                if s.startswith(">"):
                    s = s.lstrip("> ").strip()
                if s and not s.startswith(("---", "|", "`", "<!--", "*", "-", "=")):
                    zweck_projekt = sprachen._kuerzen(s, 200)
                    break
        if zweck_projekt:
            break

    return {
        "name": wurzel.name,
        "wurzel": str(wurzel),
        "zweck": zweck_projekt,
        "gescannt": int(time.time()),
        "dauer_ms": int((time.time() - beginn) * 1000),
        "neuste_aenderung": int(neuste_aenderung),
        "git": _git_stand(wurzel),
        "anzahl_dateien": len(dateien),
        "anzahl_zeilen": gesamt_zeilen,
        "dateien": dateien,
        "kanten": kanten,
        "befehle": befehle,
        "adressen": adressen,
        "markierungen": alle_markierungen[:60],
        "ausgelassen": sorted(ausnahmen)[:40],
    }
