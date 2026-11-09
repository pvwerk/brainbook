#!/bin/sh
# Zweck: Erkennt Zugangsdaten im Gespraech, legt sie verschluesselt ab und
# ersetzt sie im Sitzungsprotokoll durch einen Verweis auf den Tresoreintrag.
#
# Dies ist die einzige Stelle im Werkzeug, die am Sitzungsprotokoll etwas
# aendern darf. Sie loescht nichts, sie ersetzt - und legt vorher eine Kopie
# in ~/.Papierkorb-Claude/tresorwache/.
#
# Schlaegt etwas fehl, wird durchgelassen: ein kaputter Waechter darf keine
# Sitzung lahmlegen.

[ -n "$LANDKARTE_OHNE_TRESORWACHE" ] && exit 0

EIGEN="${CLAUDE_PLUGIN_ROOT:-$HOME/brainbook/landkarte}/bin/tresorwache"
[ -x "$EIGEN" ] || EIGEN="$HOME/.local/bin/tresorwache"
[ -x "$EIGEN" ] || exit 0

exec "$EIGEN"
