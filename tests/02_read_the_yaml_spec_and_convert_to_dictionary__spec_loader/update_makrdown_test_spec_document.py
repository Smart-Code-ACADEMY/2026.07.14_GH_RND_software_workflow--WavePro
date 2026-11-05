"""STEP 02 – Write the test case table into test_specification.md

The part between AUTO-START and AUTO-END is generated from test_cases.yaml,
so the document always shows exactly what the tools execute.
Do not edit that part by hand – edit test_cases.yaml instead.

    python 02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader/update_makrdown_test_spec_document.py           update
    python 02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader/update_makrdown_test_spec_document.py --check   only check
"""
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "02_read_the_yaml_spec_and_convert_to_dictionary__spec_loader"))
import spec_loader  # noqa: E402,F401  – first: makes the files of steps 03–05 loadable

from spec_loader import SPEC_FILE, load_specification  # noqa: E402

DOCUMENT = SPEC_FILE.with_name("test_specification.md")
START = "<!-- AUTO-START: generated from test_cases.yaml – do not edit by hand -->"
END = "<!-- AUTO-END -->"


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def table() -> str:
    rows = [
        "| ID | Principle | Actions (what the test does) | Expected result (what is checked) |",
        "|---|---|---|---|",
    ]
    for case in load_specification():
        actions, checks = [], []
        for number, step in enumerate(case.steps, start=1):
            (checks if step.is_check else actions).append(f"{number}. {_cell(step.readable())}")
        rows.append(
            f"| **{case.id}** {_cell(case.title)} | {_cell(case.principle)} "
            f"| {'<br>'.join(actions) or '–'} | {'<br>'.join(checks)} |")
    return "\n".join(rows)


def new_content(old: str) -> str:
    if START not in old or END not in old:
        raise SystemExit(f"Markers are missing in {DOCUMENT.name}.")
    before, rest = old.split(START, 1)
    _, after = rest.split(END, 1)
    return f"{before}{START}\n{table()}\n{END}{after}"


def main() -> int:
    old = DOCUMENT.read_text(encoding="utf-8")
    new = new_content(old)
    if "--check" in sys.argv:
        if new != old:
            print("OUTDATED: run update_makrdown_test_spec_document.py")
            return 1
        print(f"OK: {DOCUMENT.name} matches {SPEC_FILE.name}")
        return 0
    DOCUMENT.write_text(new, encoding="utf-8")
    print(f"Updated: {DOCUMENT.name} (from {SPEC_FILE.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
