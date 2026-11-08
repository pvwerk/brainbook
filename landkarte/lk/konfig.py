"""Zweck: Einstellungen und Pfade der Landkarte, plus Projekterkennung."""

from __future__ import annotations

import json
import os
from pathlib import Path

HEIM = Path.home()
LK_HEIM = HEIM / ".landkarte"
REGISTER = LK_HEIM / "register.json"
PROJEKT_CACHE = LK_HEIM / "projekte"
KONFIG_DATEI = LK_HEIM / "konfig.json"

STANDARD = {
    "wurzeln": [
        {"pfad": "~/Projekte", "tiefe": 1},
        {"pfad": "~/Desktop", "tiefe": 1},
        {"pfad": "~", "tiefe": 1},
    ],
    "ignorieren": [
        ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "dist", "build", ".next", ".nuxt", ".parcel-cache", "coverage",
        ".landkarte", ".Papierkorb-Claude", ".Trash", ".DS_Store",
        "Library", "Applications", "Pictures", "Movies", "Music",
        "Public", "Downloads", "whisper-models", ".claude-browser",
        ".cache", ".local", ".npm", ".nvm", ".cargo", ".rustup",
        "site-packages", "vendor", ".cm4all", "SynologyDrive",
        ".Spotlight-V100", ".fseventsd", ".cloudflared", ".ssh", ".gnupg",
    ],
    "nicht_scannen": [],
    "register_ausgabe": "~/Projekte/LANDKARTE.md",
    "schreiber_modell": "sonnet",
    "schreiber_doppelt": True,
    "aufseher_modell": "sonnet",
    "aufseher_doppelt": True,
    "kapitel_min_aufrufe": 8,
    # Selbstprotokoll: nur lokal, verlaesst den Rechner nur per Export
    "statistik": True,
    "teilnehmer": "",
    "ki": "unbekannt",
    # Wie ein Sprachmodell gerufen wird. {modell} wird ersetzt. So laeuft das
    # Werkzeug auch mit codex, llm, ollama oder einem eigenen Skript.
    "modell_befehl": [
        "claude", "-p", "--model", "{modell}",
        "--restricted", "--strict-mcp-config",
        "--disallowed-tools", "Read", "Edit", "Write", "Glob", "Grep",
        "Task", "WebSearch", "WebFetch", "NotebookEdit", "TodoWrite",
    ],
}

# Dateiendungen, die als Inhalt gelesen werden
TEXT_ENDUNGEN = {
    ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue",
    ".php", ".sh", ".bash", ".zsh", ".sql", ".html", ".htm", ".css", ".scss",
    ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
    ".service", ".timer", ".socket", ".plist", ".env", ".htaccess", ".rules",
    ".xml", ".svg", ".c", ".h", ".rs", ".go", ".rb", ".java", ".kt", ".swift",
    ".tf", ".hcl", ".lua", ".pl", ".r", ".jinja", ".j2", ".tmpl", ".csv",
}

# Dateien ohne Endung, die trotzdem Text sind
TEXT_NAMEN = {
    "Makefile", "makefile", "Dockerfile", "Caddyfile", "Procfile", "Vagrantfile",
    "Justfile", "justfile", "CNAME", "LICENSE", "README", "NOTES", "TODO",
    ".htaccess", ".htpasswd", ".gitignore", ".dockerignore", ".editorconfig",
    ".env", ".env.example", "crontab", "requirements.txt",
}

MAX_DATEI = 400_000          # groessere Dateien werden nur gezaehlt
MAX_DATEIEN = 12000          # Obergrenze je Projekt
MAX_EDGES_JE_DATEI = 15

# Sammelordner sind selbst kein Projekt - nur ihre Unterordner.
NIEMALS_PROJEKT = {
    HEIM, HEIM / "Desktop", HEIM / "Documents", HEIM / "Downloads",
    HEIM / "Public", HEIM / "Movies", HEIM / "Music", HEIM / "Pictures",
    HEIM / "Library", HEIM / "Applications", HEIM / "Projekte",
    HEIM / "SynologyDrive", Path("/"), Path("/Users"),
}

# Punktordner werden uebersprungen, diese beiden aber nicht: dort steht
# Projektinhalt (Arbeitsablaeufe, eigene Skills).
PUNKTORDNER_ERLAUBT = {".github", ".claude"}

# Innerhalb von .claude ist fast alles Sitzungsmuell - nur das hier ist Inhalt.
CLAUDE_ERLAUBT = {"skills", "agents", "commands", "hooks", "output-styles",
                  "workflows", "monitors", "themes"}

PROJEKT_MARKER = (
    ".git", "pyproject.toml", "package.json", "requirements.txt", "Cargo.toml",
    "go.mod", "Gemfile", "composer.json", "Makefile", "docker-compose.yml",
    "docker-compose.yaml", "KARTE.md", "pom.xml", "build.gradle",
)


def laden() -> dict:
    """Konfiguration lesen, fehlende Schluessel aus STANDARD ergaenzen."""
    konf = dict(STANDARD)
    if KONFIG_DATEI.exists():
        try:
            eigen = json.loads(KONFIG_DATEI.read_text("utf-8"))
            if isinstance(eigen, dict):
                konf.update(eigen)
        except (json.JSONDecodeError, OSError):
            pass
    return konf


def schreiben(konf: dict) -> None:
    LK_HEIM.mkdir(parents=True, exist_ok=True)
    KONFIG_DATEI.write_text(json.dumps(konf, indent=2, ensure_ascii=False), "utf-8")


def ausklappen(pfad: str) -> Path:
    return Path(os.path.expanduser(pfad)).resolve()


def ist_text(p: Path) -> bool:
    if p.suffix.lower() in TEXT_ENDUNGEN:
        return True
    return p.name in TEXT_NAMEN


def ist_projekt(ordner: Path) -> bool:
    if ordner.resolve() in NIEMALS_PROJEKT:
        return False
    for marker in PROJEKT_MARKER:
        if (ordner / marker).exists():
            return True
    # Ordner mit Quelldateien direkt darin gilt auch als Projekt
    try:
        for eintrag in os.scandir(ordner):
            if eintrag.is_file() and Path(eintrag.name).suffix in (
                ".py", ".js", ".ts", ".php", ".sh", ".sql", ".go", ".rs"
            ):
                return True
    except OSError:
        return False
    return False


def slug(pfad: Path) -> str:
    text = str(pfad).replace(str(HEIM), "~")
    erlaubt = []
    for z in text:
        erlaubt.append(z if z.isalnum() or z in "-_" else "_")
    return "".join(erlaubt).strip("_")
