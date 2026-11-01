"""03 pywinauto pur – führt die zentrale Testspezifikation OHNE Testframework aus.

Zeigt, was pytest und Robot Framework eigentlich übernehmen: Diese Datei
liest die YAML, führt jeden Testfall mit pywinauto aus, fängt Fehler ab
und schreibt selbst einen Bericht:

    reports/03_pywinauto/bericht.html   – für Menschen
    reports/03_pywinauto/ergebnis.json  – für den Vergleich (00_vergleich.html)

Aufruf: python 03_pywinauto/run_spezifikation.py
"""
import html
import json
import sys
import time
import traceback
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "09_gemeinsam"))

from sitzung import Sitzung  # noqa: E402
from spec import fuehre_testfall_aus, lade_spezifikation  # noqa: E402
from wavepro import REPORTS_DIR  # noqa: E402

BERICHT = REPORTS_DIR / "03_pywinauto"


def main() -> int:
    faelle = lade_spezifikation()
    sitzung = Sitzung(BERICHT)
    ergebnisse = []
    sitzung.beginne()
    try:
        for fall in faelle:
            print(f"{fall.name} ... ", end="", flush=True)
            t0 = time.monotonic()
            status, meldung = "PASS", ""
            try:
                kontext = sitzung.starte_test()
                fuehre_testfall_aus(kontext, fall)
            except AssertionError as e:
                status, meldung = "FAIL", str(e)
            except Exception as e:
                status, meldung = "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"
            screenshot = sitzung.beende_test(fall.id, status != "PASS")
            dauer = time.monotonic() - t0
            print(f"{status}  ({dauer:.1f} s)")
            if meldung:
                print("   " + meldung.splitlines()[0])
            ergebnisse.append({
                "id": fall.id, "titel": fall.titel, "status": status,
                "meldung": meldung, "dauer_s": round(dauer, 1),
                "screenshot": str(screenshot.relative_to(BERICHT)) if screenshot else ""})
    finally:
        sitzung.beende()

    (BERICHT / "ergebnis.json").write_text(
        json.dumps(ergebnisse, indent=2, ensure_ascii=False), encoding="utf-8")
    (BERICHT / "bericht.html").write_text(_html(ergebnisse), encoding="utf-8")

    bestanden = sum(e["status"] == "PASS" for e in ergebnisse)
    print(f"\n{bestanden}/{len(ergebnisse)} bestanden – Bericht: {BERICHT / 'bericht.html'}")
    return 0 if bestanden == len(ergebnisse) else 1


def _html(ergebnisse) -> str:
    zeilen = []
    for e in ergebnisse:
        farbe = "#1f7a3a" if e["status"] == "PASS" else "#b3261e"
        bild = (f'<br><a href="{html.escape(e["screenshot"])}">Screenshot</a>'
                if e["screenshot"] else "")
        zeilen.append(
            f"<tr><td>{e['id']}</td><td>{html.escape(e['titel'])}</td>"
            f"<td style='color:#fff;background:{farbe};text-align:center'>{e['status']}</td>"
            f"<td>{e['dauer_s']} s</td>"
            f"<td><pre>{html.escape(e['meldung'])}</pre>{bild}</td></tr>")
    bestanden = sum(e["status"] == "PASS" for e in ergebnisse)
    return f"""<!doctype html><html lang="de"><meta charset="utf-8">
<title>03 pywinauto – Bericht</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:24px}}
table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px 10px;vertical-align:top}}
th{{background:#eee}}pre{{margin:0;white-space:pre-wrap}}</style>
<h1>03 pywinauto – {bestanden}/{len(ergebnisse)} bestanden</h1>
<p>Erstellt {time.strftime('%d.%m.%Y %H:%M')} aus 00_spezifikation/testfaelle.yaml</p>
<table><tr><th>ID</th><th>Titel</th><th>Ergebnis</th><th>Dauer</th><th>Meldung</th></tr>
{''.join(zeilen)}</table></html>"""


if __name__ == "__main__":
    sys.exit(main())
