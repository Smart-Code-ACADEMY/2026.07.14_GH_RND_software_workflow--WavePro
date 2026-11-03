"""STEP 06c – pywinauto only: runs the test specification WITHOUT a test framework.

Shows what pytest and Robot Framework normally do for you: this file reads
the YAML, runs every test case with pywinauto, catches failures and writes
its own report:

    08_results__reports/6c_pywinauto_only/report.html   – for people
    08_results__reports/6c_pywinauto_only/results.json  – for the comparison

Call: python 06_run_the_tests__test_runners/6c_pywinauto_only/run_yaml_tests_with_pywinauto__run_specification.py
"""
import html
import json
import sys
import time
import traceback
from pathlib import Path

TESTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS / "02_read_the_spec__spec_loader"))
import spec_loader  # noqa: E402,F401  – first: makes the files of steps 03–05 loadable

from command_log import KEYS_SCRIPT, LOG, html_table, inline_style  # noqa: E402
from session import REPORTS_DIR, TestSession  # noqa: E402
from spec_loader import load_selected_test_cases, run_test_case  # noqa: E402

REPORT_DIR = REPORTS_DIR / "6c_pywinauto_only"


def main() -> int:
    cases = load_selected_test_cases()        # step-07 selection applied
    session = TestSession(REPORT_DIR)
    results = []
    session.begin()
    try:
        for case in cases:
            t0 = time.monotonic()
            status, message = "PASS", ""
            try:
                context = session.start_test(case.id, case.title)
                run_test_case(context, case)
            except AssertionError as e:
                status, message = "FAIL", str(e)
            except Exception as e:
                status, message = "FAIL", f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"
            screenshot = session.end_test(case.id, status != "PASS", message)
            duration = time.monotonic() - t0
            results.append({
                "id": case.id, "title": case.title, "status": status,
                "message": message, "duration_s": round(duration, 1),
                "screenshot": screenshot.relative_to(REPORT_DIR).as_posix() if screenshot else ""})
    finally:
        session.end()

    (REPORT_DIR / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPORT_DIR / "report.html").write_text(_html(results), encoding="utf-8")

    passed = sum(r["status"] == "PASS" for r in results)
    print(f"\n{passed}/{len(results)} passed - report: {REPORT_DIR / 'report.html'}")
    return 0 if passed == len(results) else 1


def _html(results) -> str:
    rows = []
    for r in results:
        colour = "#1f7a3a" if r["status"] == "PASS" else "#b3261e"
        image = (f'<br><a href="{html.escape(r["screenshot"])}">screenshot</a>'
                 if r["screenshot"] else "")
        commands = LOG.entries_for(r["id"])
        rows.append(
            f"<tr><td>{r['id']}</td><td>{html.escape(r['title'])}</td>"
            f"<td style='color:#fff;background:{colour};text-align:center'>{r['status']}</td>"
            f"<td>{r['duration_s']} s</td>"
            f"<td><pre>{html.escape(r['message'])}</pre>{image}</td></tr>"
            f"<tr><td colspan='5'><details><summary>All {len(commands)} commands of "
            f"{r['id']} (left: command, right: what it does)</summary>"
            f"{html_table(commands)}</details></td></tr>")
    passed = sum(r["status"] == "PASS" for r in results)
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>6c pywinauto only – report</title>
{inline_style()}
<style>pre{{margin:0;white-space:pre-wrap}} table{{border-collapse:collapse}}
td,th{{border:1px solid #ccc;padding:6px 10px;vertical-align:top}} th{{background:#eee}}</style>
<h1>6c pywinauto only – {passed}/{len(results)} passed</h1>
<p>Created {time.strftime('%Y-%m-%d %H:%M')} from 01_what_to_test__test_specification/test_cases.yaml ·
<a href="command_log.html">Full command log of the whole run</a> ·
Zoomed in? Use ← → to scroll sideways.</p>
<table><tr><th>ID</th><th>Title</th><th>Result</th><th>Duration</th><th>Message</th></tr>
{''.join(rows)}</table>{KEYS_SCRIPT}</html>"""


if __name__ == "__main__":
    sys.exit(main())
