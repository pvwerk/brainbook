"""Zweck: Wissen zwischen mehreren Brainbooks austauschen - freiwillig.

Mehrere Menschen und mehrere KIs arbeiten an denselben Dingen, jede
Installation hat aber ihren eigenen Stand in `~/.landkarte`. Eine Falle, die
auf dem einen Rechner gefunden wurde, kennt der andere nicht.

Dieses Modul legt einen gemeinsamen Ort an - ein Git-Repo. Drei Grundsaetze:

**Freiwillig.** Ohne hinterlegtes Repo tut dieser Befehl nichts. Wer Brainbook
benutzt, wird dadurch mit niemandem verbunden. Es gibt keine Voreinstellung,
keinen Dienst und keinen Haken, der das von selbst anschaltet.

**Nur von Hand.** Ausgetauscht wird, wenn jemand `landkarte abgleich --jetzt`
aufruft. Kein Hintergrundlauf, kein Autostart-Eintrag.

**Nur Wissen.** Ausgetauscht werden genau drei Dateien: das Brainbook, die
Notizen und die offenen Punkte. Der Tresor (`tresor.enc`), die
Sitzungsprotokolle (`sitzungen/`), die Statistik und das Regal bleiben liegen.
Das Regal waere ohnehin unbrauchbar - es enthaelt Pfade dieses Rechners.

Jeder Rechner schreibt ausschliesslich in seinen eigenen Unterordner unter
`beitraege/`. Dadurch kann es keine Konflikte geben: niemand aendert die Datei
eines anderen.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import konfig, tresorwache

ARBEIT = konfig.LK_HEIM / "abgleich"        # Git-Arbeitskopie
GETEILT = konfig.LK_HEIM / "geteilt"        # zusammengefuehrte Fremdstaende
BEITRAEGE = "beitraege"

# Genau diese drei Dateien werden ausgetauscht. Die Liste ist absichtlich kurz
# und steht an einer Stelle: alles, was nicht hier steht, verlaesst den
# Rechner nicht.
DATEIEN = ("brainbook.md", "notizen.md", "aufgaben.jsonl")

LIESMICH = """# Gemeinsames Brainbook-Wissen

Dieses Repo wird von `landkarte abgleich` gepflegt. Es enthaelt nur Wissen,
keine Zugangsdaten und keine Sitzungsprotokolle.

Jeder Rechner schreibt nur in seinen eigenen Ordner unter `beitraege/`.
Deshalb gibt es hier keine Konflikte.

Austauschen:

    landkarte abgleich --jetzt

Mitmachen ist freiwillig. Ohne hinterlegtes Repo tut der Befehl nichts.
"""


# ------------------------------------------------------------- Einstellungen

def einstellung() -> dict:
    konf = konfig.laden()
    a = konf.get("abgleich") or {}
    return {"repo": (a.get("repo") or "").strip(),
            "zweig": (a.get("zweig") or "main").strip(),
            "zuletzt": int(a.get("zuletzt") or 0)}


def _einstellung_sichern(neu: dict) -> None:
    konf = konfig.laden()
    a = dict(konf.get("abgleich") or {})
    a.update(neu)
    konf["abgleich"] = a
    konfig.schreiben(konf)


def angeschlossen() -> bool:
    return bool(einstellung()["repo"])


def ich() -> str:
    """Ordnername dieses Rechners im Repo."""
    konf = konfig.laden()
    name = (konf.get("teilnehmer") or "").strip() or os.environ.get("USER", "unbekannt")
    rechner = platform.node().split(".")[0]
    rohform = f"{name}-{rechner}" if rechner and rechner.lower() not in name.lower() else name
    return re.sub(r"[^A-Za-z0-9._-]+", "-", rohform).strip("-").lower() or "unbekannt"


# -------------------------------------------------------------------- Git

def _git(*args: str, zeit: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ARBEIT), *args],
                          capture_output=True, timeout=zeit)


def _git_text(*args: str) -> str:
    p = _git(*args)
    if p.returncode != 0:
        raise RuntimeError("git " + " ".join(args) + ": "
                           + p.stderr.decode("utf-8", "replace").strip()[:300])
    return p.stdout.decode("utf-8", "replace")


# --------------------------------------------------------------- Einrichten

def hinterlegen(repo: str, zweig: str = "main") -> str:
    """Ein Repo als gemeinsamen Ort merken und die Arbeitskopie herstellen."""
    repo = repo.strip()
    if not repo:
        raise ValueError("kein Repo angegeben")
    if ARBEIT.exists() and (ARBEIT / ".git").exists():
        vorher = _git("remote", "set-url", "origin", repo)
        if vorher.returncode != 0:
            _git("remote", "add", "origin", repo)
    else:
        ARBEIT.parent.mkdir(parents=True, exist_ok=True)
        if ARBEIT.exists():
            # Liegt dort etwas, das kein Git-Repo ist, wird es nicht geloescht,
            # sondern beiseitegelegt. Nichts dauerhaft entfernen, was jemand
            # vielleicht noch braucht.
            beiseite = (Path.home() / ".Papierkorb-Claude" /
                        f"landkarte-abgleich-{int(time.time())}")
            beiseite.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ARBEIT), str(beiseite))
        p = subprocess.run(["git", "clone", "--depth", "50", "-q", repo, str(ARBEIT)],
                           capture_output=True, timeout=300)
        if p.returncode != 0:
            # Leeres Repo: klonen scheitert, also von Hand anlegen.
            ARBEIT.mkdir(parents=True, exist_ok=True)
            _git_text("init", "-q", "-b", zweig)
            _git_text("remote", "add", "origin", repo)
    _einstellung_sichern({"repo": repo, "zweig": zweig})
    (ARBEIT / BEITRAEGE).mkdir(parents=True, exist_ok=True)
    liesmich = ARBEIT / "README.md"
    if not liesmich.exists():
        liesmich.write_text(LIESMICH, "utf-8")
    return f"Gemeinsamer Ort hinterlegt: {repo} (Zweig {zweig})"


def loesen() -> str:
    """Verknuepfung aufheben. Die Arbeitskopie bleibt liegen."""
    _einstellung_sichern({"repo": ""})
    return ("Verknuepfung geloest. Es wird nichts mehr ausgetauscht.\n"
            f"Die Arbeitskopie liegt noch in {ARBEIT} - von Hand loeschbar.")


# ----------------------------------------------------------------- Senden

def _quelle(name: str) -> Path:
    return konfig.LK_HEIM / name


def pruefen() -> list[tuple[str, int]]:
    """Was wuerde gesendet - und steckt ein Geheimnis darin?

    Rueckgabe: je Datei (Name, Zahl der gefundenen Geheimnisse).
    """
    aus = []
    for name in DATEIEN:
        p = _quelle(name)
        if not p.exists():
            continue
        text = p.read_text("utf-8", errors="replace")
        try:
            gefunden = tresorwache.finden(text, streng=True)
        except Exception:
            gefunden = []
        aus.append((name, len(gefunden)))
    return aus


def senden(trocken: bool = False) -> str:
    # --probe geht auch ohne hinterlegtes Repo: man soll sehen koennen, was
    # den Rechner verlassen wuerde, BEVOR man sich anschliesst.
    if trocken:
        zeilen = [f"Es wuerde gesendet nach {BEITRAEGE}/{ich()}/:"]
        for name in DATEIEN:
            p = _quelle(name)
            zeilen.append(f"  {name}: "
                          + (f"{p.stat().st_size} Bytes" if p.exists() else "fehlt"))
        for name, z in pruefen():
            if z:
                zeilen.append(f"  ACHTUNG {name}: {z} moegliche(s) Geheimnis(se) - "
                              "so wird nicht gesendet")
        zeilen.append("Nicht gesendet wird: tresor.enc, sitzungen/, statistik, "
                      "regale.json, register.json")
        if not angeschlossen():
            zeilen += ["", "(Noch kein gemeinsamer Ort hinterlegt - es wird nichts "
                       "gesendet, solange keiner hinterlegt ist.)"]
        return "\n".join(zeilen)
    if not angeschlossen():
        return _kein_repo()
    st = einstellung()
    meiner = ARBEIT / BEITRAEGE / ich()

    verdacht = [(n, z) for n, z in pruefen() if z]
    if verdacht:
        teile = ", ".join(f"{n} ({z})" for n, z in verdacht)
        return ("ABGEBROCHEN: In diesen Dateien steckt etwas, das nach einem "
                f"Zugang aussieht: {teile}.\n"
                "Nichts gesendet. Erst mit `landkarte tresor saeubern` bzw. von "
                "Hand bereinigen, die Geheimnisse gehoeren in den Tresor.")

    zeilen = []
    meiner.mkdir(parents=True, exist_ok=True)
    for name in DATEIEN:
        p = _quelle(name)
        if p.exists():
            shutil.copy2(p, meiner / name)
    (meiner / "stand.json").write_text(json.dumps({
        "teilnehmer": (konfig.laden().get("teilnehmer") or ""),
        "ki": (konfig.laden().get("ki") or "unbekannt"),
        "rechner": platform.node().split(".")[0],
        "zeit": int(time.time()),
        "zeit_lesbar": time.strftime("%d.%m.%Y %H:%M"),
    }, ensure_ascii=False, indent=1), "utf-8")

    _git("add", "--", f"{BEITRAEGE}/{ich()}", "README.md")
    p = _git("diff", "--cached", "--quiet")
    if p.returncode == 0:
        zeilen.append("Nichts Neues zu senden.")
    else:
        _git_text("-c", "user.name=landkarte", "-c", "user.email=landkarte@localhost",
                  "commit", "-q", "-m", f"{ich()}: Stand {time.strftime('%d.%m.%Y %H:%M')}")
        schub = _git("push", "-u", "origin", st["zweig"], zeit=300)
        if schub.returncode != 0:
            return ("Gesichert, aber nicht gesendet: "
                    + schub.stderr.decode("utf-8", "replace").strip()[:300])
        zeilen.append(f"Gesendet als {BEITRAEGE}/{ich()}/.")
    return "\n".join(zeilen)


# ------------------------------------------------------------------ Holen

def holen() -> str:
    if not angeschlossen():
        return _kein_repo()
    st = einstellung()
    hol = _git("pull", "--ff-only", "-q", "origin", st["zweig"], zeit=300)
    if hol.returncode != 0:
        fehler = hol.stderr.decode("utf-8", "replace").strip()[:200]
        if "couldn't find remote ref" not in fehler and "no such ref" not in fehler:
            return f"Nicht geholt: {fehler}"
    anzahl = zusammenfuehren()
    _einstellung_sichern({"zuletzt": int(time.time())})
    return (f"Geholt. {anzahl} fremde(r) Stand/Staende zusammengefuehrt in {GETEILT}."
            if anzahl else "Geholt. Es gibt noch keine fremden Staende.")


def fremde_staende() -> list[tuple[str, Path]]:
    wurzel = ARBEIT / BEITRAEGE
    if not wurzel.is_dir():
        return []
    return sorted((d.name, d) for d in wurzel.iterdir()
                  if d.is_dir() and d.name != ich())


def zusammenfuehren() -> int:
    """Fremde Staende zu einer lesbaren Fassung in ~/.landkarte/geteilt bauen."""
    fremde = fremde_staende()
    GETEILT.mkdir(parents=True, exist_ok=True)

    notizen = ["# Notizen der anderen Brainbooks", "",
               "_Von `landkarte abgleich` zusammengetragen. Nur zum Lesen - "
               "Aenderungen hier werden beim naechsten Abgleich ueberschrieben._", ""]
    buch = ["# Brainbooks der anderen", ""]
    punkte: list[dict] = []

    for name, ordner in fremde:
        n = ordner / "notizen.md"
        if n.exists():
            notizen += [f"## Von {name}", "", n.read_text("utf-8", errors="replace").strip(), ""]
        b = ordner / "brainbook.md"
        if b.exists():
            buch += [f"## Von {name}", "", b.read_text("utf-8", errors="replace").strip(), ""]
        a = ordner / "aufgaben.jsonl"
        if a.exists():
            for z in a.read_text("utf-8", errors="replace").splitlines():
                z = z.strip()
                if not z:
                    continue
                try:
                    e = json.loads(z)
                except ValueError:
                    continue
                if e.get("erledigt_am"):
                    continue
                e["teilnehmer"] = name
                punkte.append(e)

    (GETEILT / "notizen.md").write_text("\n".join(notizen) + "\n", "utf-8")
    (GETEILT / "brainbook.md").write_text("\n".join(buch) + "\n", "utf-8")
    with (GETEILT / "aufgaben.jsonl").open("w", encoding="utf-8") as f:
        for e in punkte:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(fremde)


# ------------------------------------------------------------------ Stand

def _kein_repo() -> str:
    return ("Kein gemeinsamer Ort hinterlegt - es wird nichts ausgetauscht.\n"
            "Mitmachen ist freiwillig. Einen Ort hinterlegen:\n"
            "    landkarte abgleich --repo <Git-URL>")


def stand() -> str:
    st = einstellung()
    if not st["repo"]:
        return _kein_repo()
    zeilen = [f"Gemeinsamer Ort: {st['repo']}  (Zweig {st['zweig']})",
              f"Dieser Rechner schreibt nach: {BEITRAEGE}/{ich()}/",
              "Zuletzt geholt: " + (time.strftime("%d.%m.%Y %H:%M",
                                                  time.localtime(st["zuletzt"]))
                                    if st["zuletzt"] else "noch nie"), ""]
    fremde = fremde_staende()
    if fremde:
        zeilen.append("Fremde Staende:")
        for name, ordner in fremde:
            wann = ""
            s = ordner / "stand.json"
            if s.exists():
                try:
                    wann = json.loads(s.read_text("utf-8")).get("zeit_lesbar", "")
                except ValueError:
                    pass
            zeilen.append(f"  {name}" + (f"  (Stand {wann})" if wann else ""))
    else:
        zeilen.append("Fremde Staende: keine")
    zeilen += ["", "Ausgetauscht werden nur: " + ", ".join(DATEIEN),
               "Nie ausgetauscht: tresor.enc, sitzungen/, statistik, regale.json, "
               "register.json"]
    return "\n".join(zeilen)
