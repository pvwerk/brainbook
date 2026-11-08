"""Zweck: In Sekunden finden - Symbole, Dateien, Fallen, Kapitel, alle Projekte."""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import buch, konfig, notizen


def _projekte_laden() -> list[dict]:
    if not konfig.PROJEKT_CACHE.exists():
        return []
    bekannt: set[str] | None = None
    if konfig.REGISTER.exists():
        try:
            reg = json.loads(konfig.REGISTER.read_text("utf-8"))
            bekannt = {x["wurzel"] for x in reg.get("projekte", [])}
        except (OSError, json.JSONDecodeError, KeyError):
            bekannt = None
    aus = []
    for p in sorted(konfig.PROJEKT_CACHE.glob("*.json")):
        try:
            eintrag = json.loads(p.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        wurzel = eintrag.get("wurzel", "")
        if bekannt is not None and wurzel not in bekannt:
            continue                      # veralteter Zwischenspeicher
        if not Path(wurzel).is_dir():
            continue
        aus.append(eintrag)
    return aus


def finden(begriff: str, projekt: str | None = None,
           grenze: int = 60) -> list[dict]:
    """Treffer über alle gescannten Projekte, nach Genauigkeit sortiert."""
    muster = re.compile(re.escape(begriff), re.I)
    genau = re.compile(r"\b" + re.escape(begriff) + r"\b", re.I)
    treffer: list[dict] = []

    for pr in _projekte_laden():
        if projekt and projekt.lower() not in pr["name"].lower():
            continue
        wurzel = pr["wurzel"]
        name = pr["name"]

        if muster.search(name) or muster.search(pr.get("zweck", "")):
            treffer.append({"punkte": 90, "art": "Projekt", "projekt": name,
                            "ort": wurzel, "text": pr.get("zweck", "")})

        for d in pr.get("dateien", []):
            if muster.search(d["pfad"]):
                punkte = 70 if genau.search(Path(d["pfad"]).stem) else 55
                treffer.append({"punkte": punkte, "art": "Datei", "projekt": name,
                                "ort": f"{wurzel}/{d['pfad']}",
                                "text": d.get("zweck", "")})
            elif d.get("zweck") and muster.search(d["zweck"]):
                treffer.append({"punkte": 40, "art": "Zweck", "projekt": name,
                                "ort": f"{wurzel}/{d['pfad']}",
                                "text": d["zweck"]})
            for s in d.get("symbole", []):
                if genau.search(s["name"]):
                    treffer.append({"punkte": 85, "art": s["art"], "projekt": name,
                                    "ort": f"{wurzel}/{d['pfad']}:{s['zeile']}",
                                    "text": s["name"]})
                elif muster.search(s["name"]):
                    treffer.append({"punkte": 60, "art": s["art"], "projekt": name,
                                    "ort": f"{wurzel}/{d['pfad']}:{s['zeile']}",
                                    "text": s["name"]})

        for b in pr.get("befehle", []):
            if muster.search(b["wie"]) or muster.search(b["was"]):
                treffer.append({"punkte": 65, "art": "Befehl", "projekt": name,
                                "ort": wurzel, "text": f"{b['wie']}  ({b['was']})"})
        for a in pr.get("adressen", []):
            if muster.search(a):
                treffer.append({"punkte": 65, "art": "Adresse", "projekt": name,
                                "ort": wurzel, "text": a})

        w = Path(wurzel)
        if w.is_dir():
            notiz = notizen.laden(w)
            for abschnitt, punkte_liste in notiz.items():
                for eintrag in punkte_liste:
                    if muster.search(eintrag):
                        treffer.append({"punkte": 80, "art": "Notiz/" + abschnitt,
                                        "projekt": name,
                                        "ort": str(notizen.pfad(w)),
                                        "text": eintrag})
            for k in buch.kapitel_sammeln(w):
                kopf = k["kopf"]
                if muster.search(kopf.get("titel", "")):
                    treffer.append({"punkte": 75, "art": "Kapitel", "projekt": name,
                                    "ort": k["pfad"], "text": kopf.get("titel", "")})
                for art, schluessel in (("Falle", "fallen"), ("Regel", "regeln")):
                    for eintrag in k.get(schluessel, []):
                        if muster.search(eintrag):
                            treffer.append({"punkte": 82, "art": art,
                                            "projekt": name, "ort": k["pfad"],
                                            "text": eintrag})

    gesehen = set()
    eindeutig = []
    for t in sorted(treffer, key=lambda x: -x["punkte"]):
        schluessel = (t["art"], t["ort"], t["text"][:60])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        eindeutig.append(t)
    return eindeutig[:grenze]


def ausgeben(treffer: list[dict], begriff: str) -> str:
    if not treffer:
        return (f"Kein Treffer für \"{begriff}\".\n"
                "Ist das Regal aktuell? → landkarte regal")
    z = [f"{len(treffer)} Treffer für \"{begriff}\":", ""]
    projekt = None
    for t in treffer:
        if t["projekt"] != projekt:
            projekt = t["projekt"]
            z.append(f"── {projekt}")
        ort = t["ort"].replace(str(konfig.HEIM), "~")
        text = t["text"][:100]
        z.append(f"   {t['art']:<12} {ort}")
        if text and text not in ort:
            z.append(f"   {'':<12} {text}")
    return "\n".join(z)
