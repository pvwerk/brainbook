#!/bin/sh
# Zweck: Stoesst am Sitzungsende den Schreiber an - vollstaendig abgekoppelt,
# damit er das Ende der Sitzung ueberlebt. Er verarbeitet nur Sitzungen, in
# denen seit fuenf Minuten nichts mehr passiert ist, also nie die laufende.

[ -n "$LANDKARTE_SCHREIBER" ] && exit 0

LK="$HOME/.local/bin/landkarte"
[ -x "$LK" ] || LK="landkarte"
command -v "$LK" >/dev/null 2>&1 || exit 0

PROTOKOLL="$HOME/.landkarte/schreiber.log"
nohup sh -c '
  sleep 330
  "$0" kapitel --faellig --grenze 4 >> "$1" 2>&1
  "$0" regal --ohne-scan >> "$1" 2>&1
' "$LK" "$PROTOKOLL" >/dev/null 2>&1 &

exit 0
