"""STEP 07 – RESULTS: compare the three tools → 00_comparison_of_all_tools.html

Reads:
    07_results__reports/6a_pytest/junit.xml
    07_results__reports/6b_robot_framework/output.xml
    07_results__reports/6c_pywinauto_only/results.json
and shows PASS/FAIL per test case and tool. The column "Same?" reports
when the tools disagree (this must never happen).

Call: python 07_results__reports/compare_results.py
"""
import html
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
for folder in sorted(TESTS.glob("0[2-5]_*")):
    sys.path.insert(0, str(folder))

from session import REPORTS_DIR  # noqa: E402
from spec_loader import load_specification  # noqa: E402

TOOLS = [
    ("6a pytest", "6a_pytest/report.html"),
    ("6b Robot Framework", "6b_robot_framework/report.html"),
    ("6c pywinauto only", "6c_pywinauto_only/report.html"),
]


def _pytest() -> dict:
    file = REPORTS_DIR / "6a_pytest" / "junit.xml"
    if not file.is_file():
        return {}
    out = {}
    for tc in ET.parse(file).getroot().iter("testcase"):
        name = tc.get("name", "")
        case_id = name[name.find("[") + 1:name.rfind("]")] if "[" in name else name
        error = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if tc.find("skipped") is not None:
            out[case_id] = ("SKIP", "")
        elif error is not None:
            out[case_id] = ("FAIL", (error.get("message") or "").strip())
        else:
            out[case_id] = ("PASS", "")
    return out


def _robot() -> dict:
    file = REPORTS_DIR / "6b_robot_framework" / "output.xml"
    if not file.is_file():
        return {}
    out = {}
    for test in ET.parse(file).getroot().iter("test"):
        case_id = test.get("name", "").split(" ")[0]
        status = test.find("status")
        out[case_id] = (status.get("status", "?"), (status.text or "").strip())
    return out


def _pywinauto() -> dict:
    file = REPORTS_DIR / "6c_pywinauto_only" / "results.json"
    if not file.is_file():
        return {}
    return {r["id"]: (r["status"], r["message"])
            for r in json.loads(file.read_text(encoding="utf-8"))}


def main() -> int:
    cases = load_specification()
    sources = [_pytest(), _robot(), _pywinauto()]
    rows, disagreements = [], 0

    print(f"{'ID':7} {'6a pytest':10} {'6b Robot':10} {'6c pywinauto':13} Same?")
    for case in cases:
        values = [s.get(case.id, ("—", "not run")) for s in sources]
        executed = [v[0] for v in values if v[0] != "—"]
        same = len(set(executed)) <= 1
        disagreements += 0 if same else 1
        print(f"{case.id:7} " + " ".join(f"{v[0]:10}" for v in values[:2])
              + f" {values[2][0]:13} {'yes' if same else 'NO'}")
        cells = []
        for status, message in values:
            colour = {"PASS": "#1f7a3a", "FAIL": "#b3261e"}.get(status, "#777")
            tip = html.escape(message.splitlines()[0][:200]) if message else ""
            cells.append(f"<td style='background:{colour};color:#fff;text-align:center' "
                         f"title='{tip}'>{status}</td>")
        rows.append(
            f"<tr><td>{case.id}</td><td>{html.escape(case.title)}</td>{''.join(cells)}"
            f"<td style='text-align:center'>{'✔' if same else '<b style=color:#b3261e>✘ NO</b>'}</td></tr>")

    head = "".join(f"<th><a href='{link}'>{name}</a></th>" for name, link in TOOLS)
    totals = [f"<td style='text-align:center'>{sum(v[0] == 'PASS' for v in s.values())}"
              f"/{len(cases)}</td>" if s else "<td>—</td>" for s in sources]
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Comparison of all tools</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:24px}}
table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px 12px}}th{{background:#eee}}</style>
<h1>Same test cases, three tools</h1>
<p>Source: 01_what_to_test__test_specification/test_cases.yaml · created {time.strftime('%Y-%m-%d %H:%M')} ·
Disagreements: <b>{disagreements}</b> (must be 0). Hover over a cell to see the failure message.</p>
<table><tr><th>ID</th><th>Test case</th>{head}<th>Same?</th></tr>
{''.join(rows)}
<tr><td></td><td><b>Passed</b></td>{''.join(totals)}<td></td></tr></table></html>"""
    target = REPORTS_DIR / "00_comparison_of_all_tools.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    print(f"\nDisagreements: {disagreements}  →  {target}")
    return 1 if disagreements else 0


if __name__ == "__main__":
    sys.exit(main())
