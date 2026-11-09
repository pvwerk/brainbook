#!/bin/sh
# Zweck: Haelt eine KI an, die Code liest, ohne vorher nachzuschlagen.
# Laeuft vor jedem Lesezugriff, deshalb der schlanke eigene Einstieg.
# Schlaegt irgendetwas fehl, wird durchgelassen - ein kaputter Waechter darf
# keine Sitzung lahmlegen.

[ -n "$LANDKARTE_SCHREIBER" ] && exit 0
[ -n "$LANDKARTE_OHNE_WACHE" ] && exit 0

EIGEN="${CLAUDE_PLUGIN_ROOT:-$HOME/brainbook/landkarte}/bin/platzanweiser"
[ -x "$EIGEN" ] || EIGEN="$HOME/.local/bin/platzanweiser"
[ -x "$EIGEN" ] || exit 0

exec "$EIGEN"
