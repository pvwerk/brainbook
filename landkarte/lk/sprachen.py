"""Zweck: Symbole, Zweckzeile, Markierungen und Verweise aus einer Datei ziehen.

Python wird exakt ueber das ast-Modul gelesen. Fuer die uebrigen Sprachen
arbeiten Regeln auf Textebene: sie finden Definitionen auf der obersten
Ebene zuverlaessig, verschachtelte oder dynamisch erzeugte nicht. Das ist
bewusst so, damit das Werkzeug ohne Fremdpakete auskommt; die Karte sagt
es an der betreffenden Stelle ausdruecklich.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

MARKIERUNG = re.compile(
    r"\b(TODO|FIXME|XXX|HACK|OFFEN|ACHTUNG|WICHTIG|BUG)\b[:\s-]*(.{0,140})",
    re.I,
)
GEHEIM_VERDACHT = re.compile(r"[A-Za-z0-9+/=_\-]{28,}")
KOMMENTAR_ZEICHEN = ("#", "//", "--", ";", "*", "/*", "<!--", "'''", '"""')

# ---------------------------------------------------------------- Zweckzeile

ZWECK_MARKER = re.compile(r"(?:zweck|purpose)\s*:\s*(.+)", re.I)


def _saubern(zeile: str) -> str:
    z = zeile.strip()
    for anfang in ("<!--", "/*", "*/", "-->", '"""', "'''"):
        z = z.replace(anfang, " ")
    z = z.strip()
    while z[:2] in ("//", "--") or z[:1] in ("#", ";", "*"):
        z = z[2:] if z[:2] in ("//", "--") else z[1:]
        z = z.strip()
    return z.strip().strip("=-_*").strip()


def zweck(text: str, pfad: Path) -> str:
    """Einzeiler, was die Datei tut. Leer, wenn die Datei es nicht sagt."""
    zeilen = text.splitlines()[:40]

    # 1. ausdrueckliche Markierung "zweck: ..."
    for z in zeilen:
        treffer = ZWECK_MARKER.search(z)
        if treffer:
            return _kuerzen(_saubern(treffer.group(1)))

    # 2. Python-Docstring
    if pfad.suffix == ".py":
        try:
            doku = ast.get_docstring(ast.parse(text))
            if doku:
                return _kuerzen(doku.strip().splitlines()[0])
        except (SyntaxError, ValueError):
            pass

    # 3. Markdown: erste Ueberschrift oder erster Absatz
    if pfad.suffix == ".md":
        for z in zeilen:
            s = z.strip()
            if s.startswith("#"):
                return _kuerzen(s.lstrip("# ").strip())
            if s and not s.startswith(("---", "<!--", "|", "`")):
                return _kuerzen(s)
        return ""

    # 4. HTML: Titel oder Front-Matter-Kommentar des Seitengenerators
    if pfad.suffix in (".html", ".htm"):
        t = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
        if t:
            return _kuerzen(t.group(1).strip())
        k = re.search(r"<!--\s*(.*?)\s*-->", text, re.S)
        if k:
            erste = [x.strip() for x in k.group(1).splitlines() if x.strip()]
            if erste:
                return _kuerzen(" / ".join(erste[:2]))
        h = re.search(r"<h[12][^>]*>(.*?)</h[12]>", text, re.S | re.I)
        if h:
            return _kuerzen(re.sub(r"<[^>]+>", "", h.group(1)).strip())
        return ""

    # 5. zusammenhaengender Kommentarblock am Dateianfang
    sammlung: list[str] = []
    for z in zeilen:
        s = z.strip()
        if not s:
            if sammlung:
                break
            continue
        if s.startswith("#!") or s.startswith("<?php"):
            continue
        if s.startswith(KOMMENTAR_ZEICHEN):
            rein = _saubern(s)
            if rein:
                sammlung.append(rein)
            if len(sammlung) >= 3:
                break
            continue
        break
    if sammlung:
        return _kuerzen(" ".join(sammlung))
    return ""


def _kuerzen(s: str, grenze: int = 150) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    # Zeichenketten, die wie ein Schluessel aussehen, nicht uebernehmen
    for wort in s.split():
        if len(wort) >= 28 and GEHEIM_VERDACHT.fullmatch(wort):
            return ""
    satz = re.split(r"(?<=[.!?])\s", s)[0]
    if len(satz) < 20 and len(s) > len(satz):
        satz = s
    return satz[:grenze].rstrip(" .,;:")


# ------------------------------------------------------------------- Symbole


def _py(text: str) -> list[dict]:
    try:
        baum = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    aus: list[dict] = []

    def sig(knoten) -> str:
        teile = []
        a = knoten.args
        for arg in a.posonlyargs + a.args:
            teile.append(arg.arg)
        if a.vararg:
            teile.append("*" + a.vararg.arg)
        for arg in a.kwonlyargs:
            teile.append(arg.arg + "=")
        if a.kwarg:
            teile.append("**" + a.kwarg.arg)
        return "(" + ", ".join(teile) + ")"

    for knoten in baum.body:
        if isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            art = "async def" if isinstance(knoten, ast.AsyncFunctionDef) else "def"
            aus.append({
                "zeile": knoten.lineno, "art": art,
                "name": knoten.name + sig(knoten),
                "doku": (ast.get_docstring(knoten) or "").strip().splitlines()[:1],
            })
        elif isinstance(knoten, ast.ClassDef):
            basen = [getattr(b, "id", getattr(b, "attr", "")) for b in knoten.bases]
            basen = [b for b in basen if b]
            name = knoten.name + (f"({', '.join(basen)})" if basen else "")
            aus.append({
                "zeile": knoten.lineno, "art": "class", "name": name,
                "doku": (ast.get_docstring(knoten) or "").strip().splitlines()[:1],
            })
            for unter in knoten.body:
                if isinstance(unter, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if unter.name.startswith("_") and unter.name != "__init__":
                        continue
                    aus.append({
                        "zeile": unter.lineno, "art": "  methode",
                        "name": f"{knoten.name}.{unter.name}{sig(unter)}", "doku": [],
                    })
        elif isinstance(knoten, ast.Assign):
            for ziel in knoten.targets:
                if isinstance(ziel, ast.Name) and ziel.id.isupper():
                    aus.append({"zeile": knoten.lineno, "art": "konstante",
                                "name": ziel.id, "doku": []})
    return aus


_REGELN: dict[str, list[tuple[str, str]]] = {
    "js": [
        ("funktion", r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)"),
        ("klasse", r"^\s*(?:export\s+)?class\s+(\w+)"),
        ("funktion", r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>"),
        ("wert", r"^\s*export\s+(?:const|let|var)\s+(\w+)\s*="),
        ("handler", r"^\s*(?:export\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{"),
    ],
    "php": [
        ("funktion", r"^\s*(?:public\s+|private\s+|protected\s+|static\s+)*function\s+(\w+)\s*\("),
        ("klasse", r"^\s*(?:abstract\s+|final\s+)?class\s+(\w+)"),
        ("konstante", r"^\s*(?:define\s*\(\s*['\"](\w+)|const\s+(\w+))"),
    ],
    "sh": [
        ("funktion", r"^\s*(?:function\s+)?([A-Za-z_][\w-]*)\s*\(\)\s*\{"),
        ("variable", r"^([A-Z][A-Z0-9_]{2,})="),
    ],
    "sql": [
        ("tabelle", r"create\s+(?:or\s+replace\s+)?table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)"),
        ("sicht", r"create\s+(?:or\s+replace\s+)?view\s+([\w.\"]+)"),
        ("funktion", r"create\s+(?:or\s+replace\s+)?function\s+([\w.\"]+)"),
        ("regel", r"create\s+policy\s+\"?([^\"\n]+)\"?"),
        ("ausloeser", r"create\s+trigger\s+([\w.\"]+)"),
        ("index", r"create\s+(?:unique\s+)?index\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)"),
        ("aenderung", r"alter\s+table\s+([\w.\"]+)"),
    ],
    "css": [
        ("abschnitt", r"^\s*/\*\s*[=\-]*\s*([^*\n]{3,60}?)\s*[=\-]*\s*\*/"),
        ("variable", r"^\s*(--[\w-]+)\s*:"),
    ],
    "md": [
        ("ueberschrift", r"^(#{1,3})\s+(.+)$"),
    ],
    "yaml": [
        ("block", r"^([a-zA-Z_][\w-]*):\s*$"),
    ],
    "ini": [
        ("abschnitt", r"^\s*\[([^\]]+)\]"),
    ],
    "make": [
        ("ziel", r"^([a-zA-Z_][\w.-]*):(?!=)"),
    ],
    "go": [
        ("funktion", r"^func\s+(?:\([^)]*\)\s*)?(\w+)\s*\("),
        ("typ", r"^type\s+(\w+)"),
    ],
    "rs": [
        ("funktion", r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)"),
        ("struktur", r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)"),
    ],
}

_ENDUNG_ZU_SPRACHE = {
    ".py": "py", ".js": "js", ".mjs": "js", ".cjs": "js", ".ts": "js",
    ".tsx": "js", ".jsx": "js", ".vue": "js", ".php": "php", ".sh": "sh",
    ".bash": "sh", ".zsh": "sh", ".sql": "sql", ".css": "css", ".scss": "css",
    ".md": "md", ".yml": "yaml", ".yaml": "yaml", ".ini": "ini", ".cfg": "ini",
    ".conf": "ini", ".service": "ini", ".timer": "ini", ".toml": "ini",
    ".go": "go", ".rs": "rs",
}


def sprache(pfad: Path) -> str:
    if pfad.name in ("Makefile", "makefile", "Justfile", "justfile"):
        return "make"
    return _ENDUNG_ZU_SPRACHE.get(pfad.suffix.lower(), "")


def symbole(text: str, pfad: Path) -> list[dict]:
    """Definitionen der obersten Ebene mit Zeilennummer."""
    spr = sprache(pfad)
    if spr == "py":
        return _py(text)
    regeln = _REGELN.get(spr)
    if not regeln:
        return []
    aus: list[dict] = []
    gesehen: set[tuple[str, str]] = set()
    mehrzeilig = spr == "sql"
    quelle = text if not mehrzeilig else text
    for nummer, zeile in enumerate(quelle.splitlines(), 1):
        if len(zeile) > 400:
            continue
        for art, muster in regeln:
            treffer = re.search(muster, zeile, re.I if spr == "sql" else 0)
            if not treffer:
                continue
            if spr == "md":
                ebene = len(treffer.group(1))
                name = treffer.group(2).strip()
                art = "ueberschrift" + str(ebene)
            else:
                gruppen = [g for g in treffer.groups() if g]
                if not gruppen:
                    continue
                name = gruppen[0].strip().strip('"')
            if not name or name in ("if", "for", "while", "switch", "catch",
                                    "function", "else", "return", "try"):
                continue
            if (art, name) in gesehen:
                continue
            gesehen.add((art, name))
            aus.append({"zeile": nummer, "art": art, "name": name, "doku": []})
            break
    return aus


# -------------------------------------------------------------- Markierungen


def markierungen(text: str) -> list[dict]:
    aus = []
    for nummer, zeile in enumerate(text.splitlines(), 1):
        if len(zeile) > 300:
            continue
        treffer = MARKIERUNG.search(zeile)
        if treffer:
            rest = _saubern(treffer.group(2)).strip()
            aus.append({"zeile": nummer, "art": treffer.group(1).upper(),
                        "text": rest[:140]})
        if len(aus) >= 40:
            break
    return aus


# ------------------------------------------------------------------ Verweise

_IMPORT_PY = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
_IMPORT_JS = re.compile(r"""(?:from|require\s*\(|import\s*\()\s*['"](\.{1,2}/[^'"]+|[\w./-]+)['"]""")
_IMPORT_PHP = re.compile(r"""(?:require|include)(?:_once)?\s*\(?\s*['"]([^'"]+)['"]""")


def rohverweise(text: str, pfad: Path) -> list[str]:
    """Textstellen, die auf andere Dateien zeigen - noch nicht aufgeloest."""
    spr = sprache(pfad)
    aus: list[str] = []
    if spr == "py":
        for a, b in _IMPORT_PY.findall(text):
            aus.append(a or b)
    elif spr == "js":
        aus += _IMPORT_JS.findall(text)
    elif spr == "php":
        aus += _IMPORT_PHP.findall(text)
    return aus
