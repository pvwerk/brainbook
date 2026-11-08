#!/bin/sh
# Zweck: Der Chronist. Haengt einen Werkzeugaufruf an die Tageschronik an.
# Laeuft bei jedem Aufruf, darf daher nichts kosten: ein jq-Durchlauf, kein Modell.
# Schreibt nur an, aendert nie - das Rohprotokoll ist die Wahrheitsquelle,
# an der der Schiedsrichter Streitfaelle entscheidet.

[ -n "$LANDKARTE_SCHREIBER" ] && exit 0

ABLAGE="$HOME/.landkarte/chronik"
[ -d "$ABLAGE" ] || mkdir -p "$ABLAGE" || exit 0

command -v jq >/dev/null 2>&1 || {
  exec landkarte chronik-eintrag
}

# Zugangsdaten werden hier schon beim Schreiben entfernt. Beim Lesen wird
# noch einmal geschwaerzt - das deckt auch Dateien ab, die vorher entstanden.
jq -c 'def schwaerzen:
    gsub("(?<s>[a-zA-Z][a-zA-Z0-9+.-]*://)(?<u>[^\\s:/@]+):(?<p>[^\\s@]+)@";
         "\(.s)\(.u):***@")
  | gsub("(?i)(?<k>([a-z0-9]+[_-])*(pass(wor[dt])?|pwd|secret|token|api[_-]?key|private[_-]?key)s?)(?<s>[\"'"'"']?\\s*[:=]\\s*[\"'"'"']?)(?<v>[^\\s\"'"'"'&;|,}]{6,})";
         "\(.k)\(.s)***")
  | gsub("(?i)(?<k>--?(password|pass|pwd|token|secret)[= ])(?<v>[^\\s\"'"'"'&;|]{6,})"; "\(.k)***")
  | gsub("(?i)(?<e>echo\\s+[\"'"'"']?)(?<v>[^\"'"'"'|\\s]{6,})(?<r>[\"'"'"']?\\s*\\|\\s*sudo\\s+-[^\\s]*S)";
         "\(.e)***\(.r)")
  | gsub("(?i)(?<b>bearer\\s+)(?<v>[A-Za-z0-9_.+/=-]{12,})"; "\(.b)***")
  | gsub("sk-[A-Za-z0-9][A-Za-z0-9_-]{14,}"; "***")
  | gsub("gh[pousr]_[A-Za-z0-9]{20,}"; "***")
  | gsub("(?<k>PGPASSWORD|MYSQL_PWD|ANTHROPIC_API_KEY|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY)(?<e>=)(?<v>\\S+)";
         "\(.k)\(.e)***");
{
  t: (now|floor),
  s: (.session_id // ""),
  i: (.tool_use_id // ""),
  p: (.cwd // ""),
  w: (.tool_name // ""),
  d: ((.tool_input.file_path // .tool_input.path // .tool_input.command
       // .tool_input.pattern // .tool_input.url // .tool_input.notebook_path
       // "") | tostring | schwaerzen | .[0:300]),
  ms: .duration_ms
} + (if .error then {f: (.error | tostring | schwaerzen | .[0:600])} else {} end)
  + (if .is_interrupt then {abbruch: true} else {} end)' \
  >> "$ABLAGE/$(date +%F).jsonl" 2>/dev/null

exit 0
