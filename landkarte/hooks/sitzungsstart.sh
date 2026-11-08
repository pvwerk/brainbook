#!/bin/sh
# Zweck: Legt beim Sitzungsstart den Auszug der Landkarte in den Kontext.
# Beim allerersten Mal steht die Vorstellung davor, damit die KI dem Menschen
# erklaert, was die Bibliothek kann und wie er eingreift. Danach nie wieder.
# Liest nur den Zwischenspeicher, damit der Start nicht wartet; der Neuscan
# und faellige Buchkapitel laufen abgekoppelt im Hintergrund weiter.

[ -n "$LANDKARTE_SCHREIBER" ] && exit 0

EINGABE=$(cat)
ORDNER=$(printf '%s' "$EINGABE" | jq -r '.cwd // ""' 2>/dev/null)
[ -z "$ORDNER" ] && ORDNER="$PWD"

LK="$HOME/.local/bin/landkarte"
[ -x "$LK" ] || LK="landkarte"
command -v "$LK" >/dev/null 2>&1 || exit 0

# im Hintergrund: Karte auffrischen und liegengebliebene Kapitel schreiben
(
  "$LK" scan "$ORDNER" >/dev/null 2>&1
  "$LK" kapitel --faellig --grenze 3 >/dev/null 2>&1
) >/dev/null 2>&1 &

AUSZUG=$("$LK" digest --mit-vorstellung "$ORDNER" 2>/dev/null)
[ -z "$AUSZUG" ] && exit 0

if command -v jq >/dev/null 2>&1; then
  jq -nc --arg a "$AUSZUG" '{hookSpecificOutput: {
    hookEventName: "SessionStart", additionalContext: $a}}'
else
  printf '%s\n' "$AUSZUG"
fi
exit 0
