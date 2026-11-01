"""Vergleicht die Ergebnisse der drei Werkzeuge → reports/00_vergleich.html

Liest:
    reports/01_pytest/junit.xml
    reports/02_robot/output.xml
    reports/03_pywinauto/ergebnis.json
und zeigt pro Testfall PASS/FAIL je Werkzeug. Spalte "Gleich?" meldet, wenn
die Werkzeuge sich widersprechen (das darf nicht vorkommen).

Aufruf: python 09_gemeinsam/vergleiche_ergebnisse.py
"""
import html
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spec import lade_spezifikation  # noqa: E402
from wavepro import REPORTS_DIR  # noqa: E402

WERKZEUGE = [
    ("01 pytest", "01_pytest/report.html"),
    ("02 Robot", "02_robot/report.html"),
    ("03 pywinauto", "03_pywinauto/bericht.html"),
]


def _pytest() -> dict:
    datei = REPORTS_DIR / "01_pytest" / "junit.xml"
    if not datei.is_file():
        return {}
    out = {}
    for tc in ET.parse(datei).getroot().iter("testcase"):
        name = tc.get("name", "")
        tid = name[name.find("[") + 1:name.rfind("]")] if "[" in name else name
        fehler = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if tc.find("skipped") is not None:
            out[tid] = ("SKIP", "")
        elif fehler is not None:
            out[tid] = ("FAIL", (fehler.get("message") or "").strip())
        else:
            out[tid] = ("PASS", "")
    return out


def _robot() -> dict:
    datei = REPORTS_DIR / "02_robot" / "output.xml"
    if not datei.is_file():
        return {}
    out = {}
    for test in ET.parse(datei).getroot().iter("test"):
        tid = test.get("name", "").split(" ")[0]
        status = test.find("status")
        out[tid] = (status.get("status", "?"), (status.text or "").strip())
    return out


def _pywinauto() -> dict:
    datei = REPORTS_DIR / "03_pywinauto" / "ergebnis.json"
    if not datei.is_file():
        return {}
    return {e["id"]: (e["status"], e["meldung"])
            for e in json.loads(datei.read_text(encoding="utf-8"))}


def main() -> int:
    faelle = lade_spezifikation()
    quellen = [_pytest(), _robot(), _pywinauto()]
    zeilen, widersprueche = [], 0

    print(f"{'ID':7} {'01 pytest':10} {'02 Robot':10} {'03 pywinauto':13} Gleich?")
    for fall in faelle:
        werte = [q.get(fall.id, ("—", "nicht ausgeführt")) for q in quellen]
        ausgefuehrt = [w[0] for w in werte if w[0] != "—"]
        gleich = len(set(ausgefuehrt)) <= 1
        widersprueche += 0 if gleich else 1
        print(f"{fall.id:7} " + " ".join(f"{w[0]:10}" for w in werte[:2])
              + f" {werte[2][0]:13} {'ja' if gleich else 'NEIN'}")
        zellen = []
        for status, meldung in werte:
            farbe = {"PASS": "#1f7a3a", "FAIL": "#b3261e"}.get(status, "#777")
            tip = html.escape(meldung.splitlines()[0][:200]) if meldung else ""
            zellen.append(f"<td style='background:{farbe};color:#fff;text-align:center' "
                          f"title='{tip}'>{status}</td>")
        zeilen.append(
            f"<tr><td>{fall.id}</td><td>{html.escape(fall.titel)}</td>{''.join(zellen)}"
            f"<td style='text-align:center'>{'✔' if gleich else '<b style=color:#b3261e>✘ NEIN</b>'}</td></tr>")

    kopf = "".join(f"<th><a href='{link}'>{name}</a></th>" for name, link in WERKZEUGE)
    summen = []
    for q in quellen:
        summen.append(f"<td style='text-align:center'>{sum(v[0] == 'PASS' for v in q.values())}"
                      f"/{len(faelle)}</td>" if q else "<td>—</td>")
    seite = f"""<!doctype html><html lang="de"><meta charset="utf-8">
<title>00 Vergleich der Werkzeuge</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:24px}}
table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px 12px}}th{{background:#eee}}</style>
<h1>00 Vergleich: gleiche Testfälle, drei Werkzeuge</h1>
<p>Quelle: 00_spezifikation/testfaelle.yaml · erstellt {time.strftime('%d.%m.%Y %H:%M')} ·
Widersprüche: <b>{widersprueche}</b> (Soll: 0). Maus über ein Feld = Fehlermeldung.</p>
<table><tr><th>ID</th><th>Testfall</th>{kopf}<th>Gleich?</th></tr>
{''.join(zeilen)}
<tr><td></td><td><b>Bestanden</b></td>{''.join(summen)}<td></td></tr></table></html>"""
    ziel = REPORTS_DIR / "00_vergleich.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(seite, encoding="utf-8")
    print(f"\nWidersprüche: {widersprueche}  →  {ziel}")
    return 1 if widersprueche else 0


if __name__ == "__main__":
    sys.exit(main())
