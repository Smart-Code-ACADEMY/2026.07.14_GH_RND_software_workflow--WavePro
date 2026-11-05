"""STEP 07 – CHOOSE WHICH TESTS TO RUN  (test selection popup)

The window opens ONCE per run:
  - run_6a/6b/6c_*.bat: the tool opens it itself when it starts
    (spec_loader.load_selected_test_cases → ask_user() below),
  - run_6_all_tools.bat: opens it once (this file with --out) and gives the
    same choice to all three tools through WAVEPRO_TESTS.

  - lists every test case of 01_what_to_test__test_specification/test_cases.yaml,
  - preselects your SAVED selection (saved_test_selection.json) – or all tests
    if nothing is saved,
  - "Save this selection for next time" stores the choice; without it the
    choice is used only for this run and the saved one stays as it was.

Command line:  --out FILE   write the chosen IDs (e.g. "TC-08") into FILE
               --no-popup   use the saved selection (or all) without a window
Exit code 1 = cancelled. Without a display (or tkinter) a text menu is shown.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import List, Optional

TESTS = Path(__file__).resolve().parents[1]
if "spec_loader" not in sys.modules:           # load step 02 by its professional name
    import importlib.util
    _found = sorted(TESTS.glob("02_*/*__spec_loader.py"))
    if len(_found) != 1:
        raise ImportError(f"Expected one file 02_*/*__spec_loader.py in {TESTS}, found {len(_found)}")
    _spec = importlib.util.spec_from_file_location("spec_loader", _found[0])
    sys.modules["spec_loader"] = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(sys.modules["spec_loader"])

from spec_loader import load_specification  # noqa: E402

HERE = Path(__file__).resolve().parent
SAVED_FILE = HERE / "saved_test_selection.json"


def say(text: str) -> None:
    """Messages go to stderr – stdout carries only the result line."""
    print(text, file=sys.stderr, flush=True)


def ask(prompt: str) -> str:
    """Like input(), but the prompt goes to stderr (stdout is read by the .bat)."""
    sys.stderr.write(prompt)
    sys.stderr.flush()
    line = sys.stdin.readline()
    return line.strip() if line else ""


# ── Saved selection ─────────────────────────────────────────────────────
def load_saved(all_ids: List[str]) -> Optional[dict]:
    try:
        data = json.loads(SAVED_FILE.read_text(encoding="utf-8"))
        chosen = [i for i in data.get("selected", []) if i in all_ids]
        if chosen:
            return {"selected": chosen, "saved_at": data.get("saved_at", "")}
    except (OSError, ValueError):
        pass
    return None


def save(selected: List[str]) -> None:
    SAVED_FILE.write_text(json.dumps(
        {"selected": selected, "saved_at": time.strftime("%Y-%m-%d %H:%M")},
        indent=2), encoding="utf-8")


def forget_saved() -> None:
    if SAVED_FILE.is_file():
        SAVED_FILE.unlink()


# ── Popup window (tkinter, part of Python on Windows) ───────────────────
def popup(cases, preselected: List[str], saved: Optional[dict]) -> Optional[List[str]]:
    import tkinter as tk
    from tkinter import ttk

    result: dict = {"ids": None}
    root = tk.Tk()
    root.title("Wave Pro tests – choose which test cases to run")
    root.attributes("-topmost", True)
    root.minsize(640, 420)

    frame = ttk.Frame(root, padding=14)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Which test cases should run?",
              font=("Segoe UI", 13, "bold")).pack(anchor="w")
    origin = (f"Preselected: your saved selection ({len(saved['selected'])} tests, saved "
              f"{saved['saved_at']})" if saved else
              "Preselected: all test cases (no selection saved)")
    origin_label = ttk.Label(frame, text=origin, foreground="#555")
    origin_label.pack(anchor="w", pady=(2, 10))

    list_frame = ttk.Frame(frame)
    list_frame.pack(fill="both", expand=True)
    variables = {}
    for case in cases:
        var = tk.BooleanVar(value=case.id in preselected)
        variables[case.id] = var
        ttk.Checkbutton(list_frame, variable=var, command=lambda: update(),
                        text=f"{case.id}   {case.title}   ({case.principle})").pack(anchor="w", pady=1)

    count_label = ttk.Label(frame)
    count_label.pack(anchor="w", pady=(8, 4))

    tools = ttk.Frame(frame)
    tools.pack(fill="x")

    def set_all(value: bool):
        for v in variables.values():
            v.set(value)
        update()

    def forget():
        forget_saved()
        origin_label.config(text="Saved selection deleted – all test cases preselected")
        set_all(True)

    ttk.Button(tools, text="Select all", command=lambda: set_all(True)).pack(side="left")
    ttk.Button(tools, text="Deselect all", command=lambda: set_all(False)).pack(side="left", padx=6)
    ttk.Button(tools, text="Forget saved selection", command=forget).pack(side="left")

    save_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(frame, text="Save this selection for next time",
                    variable=save_var).pack(anchor="w", pady=(12, 0))

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(12, 0))

    def chosen() -> List[str]:
        return [c.id for c in cases if variables[c.id].get()]

    def run():
        ids = chosen()
        if not ids:
            return
        if save_var.get():
            save(ids)
        result["ids"] = ids
        root.destroy()

    run_button = ttk.Button(buttons, text="Run selected tests", command=run)
    run_button.pack(side="right")
    ttk.Button(buttons, text="Cancel", command=root.destroy).pack(side="right", padx=6)

    def update():
        n = len(chosen())
        count_label.config(text=f"{n} of {len(cases)} test cases selected")
        run_button.state(["!disabled"] if n else ["disabled"])

    update()
    root.bind("<Return>", lambda _e: run())
    root.bind("<Escape>", lambda _e: root.destroy())
    root.lift()
    root.focus_force()
    root.mainloop()
    return result["ids"]


# ── Text menu (fallback without a display) ──────────────────────────────
def text_menu(cases, preselected: List[str], saved: Optional[dict]) -> Optional[List[str]]:
    say("\nWhich test cases should run?")
    for n, case in enumerate(cases, start=1):
        mark = "x" if case.id in preselected else " "
        say(f"  [{mark}] {n:2}. {case.id}  {case.title}")
    say("ENTER = run the marked tests · numbers like 1,4,7 = only those · q = cancel")
    answer = ask("> ").lower()
    if answer == "q":
        return None
    if not answer:
        return preselected
    picked = [cases[int(x) - 1].id for x in answer.replace(" ", "").split(",")
              if x.isdigit() and 1 <= int(x) <= len(cases)]
    if picked and ask("Save this selection for next time? (y/N) ").lower() == "y":
        save(picked)
    return picked or None


def ask_user(no_popup: bool = False) -> Optional[List[str]]:
    """Show the selection (window, or text menu without a display).
    Returns the chosen IDs, or None when cancelled."""
    cases = load_specification()
    all_ids = [c.id for c in cases]
    saved = load_saved(all_ids)
    preselected = saved["selected"] if saved else all_ids
    if no_popup:
        ids = preselected
    else:
        try:
            ids = popup(cases, preselected, saved)
        except Exception as e:          # no tkinter / no display
            say(f"(No window possible: {e}. Using the text menu.)")
            ids = text_menu(cases, preselected, saved)
    if not ids:
        say("Cancelled – no tests run.")
        return None
    say(f"Test selection: {len(ids)} of {len(all_ids)} test cases – {', '.join(ids)}")
    return ids


def main() -> int:
    ids = ask_user(no_popup="--no-popup" in sys.argv)
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if not ids:
        if out:
            Path(out).write_text("", encoding="utf-8")
        else:
            print("CANCEL")
        return 1
    if out:
        Path(out).write_text(",".join(ids) + "\n", encoding="utf-8")
    else:
        print(",".join(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
