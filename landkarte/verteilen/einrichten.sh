#!/bin/sh
# Zweck: Landkarte und Brainbook auf einem neuen Rechner einrichten.
# Faellt nie durch, ohne zu sagen warum. Veraendert nichts ausserhalb von
# ~/.landkarte und ~/.local/bin.

set -u

WURZEL=$(cd "$(dirname "$0")/.." && pwd)
ZIEL="$HOME/.local/bin"

sage() { printf '%s\n' "$*"; }
fehler() { printf 'FEHLER: %s\n' "$*" >&2; exit 1; }

sage "Landkarte & Brainbook — Einrichtung"
sage "Werkzeug liegt in: $WURZEL"
sage ""

# ---------- 1. Python pruefen ----------
PY=""
for kandidat in python3 python3.13 python3.12 python3.11 python3.10 python; do
  if command -v "$kandidat" >/dev/null 2>&1; then
    if "$kandidat" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PY="$kandidat"
      break
    fi
  fi
done
[ -n "$PY" ] || fehler "Python 3.10 oder neuer wird gebraucht.
  macOS:  brew install python
  Ubuntu: sudo apt install python3
  Windows: https://www.python.org/downloads/ (dann in Git Bash oder WSL ausfuehren)"
sage "Python: $("$PY" -V) — in Ordnung"

# ---------- 2. git ist nett, aber nicht noetig ----------
if command -v git >/dev/null 2>&1; then
  sage "git: vorhanden (Verzeichnis zeigt dann Zweig und letzten Commit)"
else
  sage "git: nicht vorhanden — geht auch, nur ohne Commit-Angaben"
fi
if command -v jq >/dev/null 2>&1; then
  sage "jq: vorhanden"
else
  sage "jq: nicht vorhanden — nur fuer den automatischen Chronisten noetig"
fi
sage ""

# ---------- 3. verknuepfen ----------
mkdir -p "$ZIEL" || fehler "kann $ZIEL nicht anlegen"
for name in landkarte brainbook; do
  ln -sf "$WURZEL/bin/$name" "$ZIEL/$name" || fehler "kann $ZIEL/$name nicht anlegen"
  chmod +x "$WURZEL/bin/$name" 2>/dev/null || true
done
sage "Verknuepft: $ZIEL/landkarte und $ZIEL/brainbook"

case ":$PATH:" in
  *":$ZIEL:"*) ;;
  *)
    sage ""
    sage "ACHTUNG: $ZIEL steht nicht in deinem PATH."
    sage "Fuege diese Zeile in deine Shell-Datei ein und starte das Terminal neu:"
    case "${SHELL:-}" in
      *zsh)  sage "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc" ;;
      *bash) sage "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc" ;;
      *)     sage "  export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
    esac
    sage ""
    ;;
esac

# ---------- 4. Teilnehmer und KI ----------
NAME="${1:-}"
KI="${2:-}"
if [ -z "$NAME" ]; then
  printf 'Dein Name fuer das Protokoll (z.B. andre, christiane): '
  read -r NAME || NAME=""
fi
if [ -z "$KI" ]; then
  printf 'Welche KI benutzt du? [claude-code / chatgpt / grok / codex / keine]: '
  read -r KI || KI=""
fi
[ -n "$KI" ] || KI="unbekannt"

# ---------- 5. einrichten ----------
"$WURZEL/bin/landkarte" einrichten ${NAME:+--teilnehmer "$NAME"} --ki "$KI" \
  || fehler "landkarte einrichten ist fehlgeschlagen"

sage ""
sage "Erstes Verzeichnis bauen (kann bei vielen Projekten einige Sekunden dauern)…"
"$WURZEL/bin/landkarte" regal || sage "  Regalbau meldete einen Fehler — siehe oben."

sage ""
sage "Fertig. Die wichtigsten Befehle:"
sage "  landkarte wo \"<begriff>\"   suchen: Projekt -> Teil -> Datei:Zeile"
sage "  landkarte zeig              Inhaltsverzeichnis des Projekts hier"
sage "  landkarte notiz \"...\"       eine Falle festhalten"
sage "  brainbook                   dein eigenes Buch"
sage "  brainbook stats             Selbstprotokoll"
sage ""
case "$KI" in
  claude-code) sage "Weiter in verteilen/fuer-claude-code.md" ;;
  chatgpt)     sage "Weiter in verteilen/fuer-chatgpt.md" ;;
  grok)        sage "Weiter in verteilen/fuer-grok.md" ;;
  *)           sage "Weiter in verteilen/AGENTS.md" ;;
esac
