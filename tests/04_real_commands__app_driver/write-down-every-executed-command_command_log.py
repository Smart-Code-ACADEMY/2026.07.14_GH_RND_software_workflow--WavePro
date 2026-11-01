"""STEP 04 – COMMAND LOG: every real command, with a plain-English explanation.

Every command that touches the app, the keyboard, the mouse, the screen,
the registry or the disk is executed through `call(...)`. That function
  1. runs the command,
  2. writes ONE line: the exact command + result + explanation + source
     (file and line number the command was executed from).

The same lines appear
  - live in the terminal,
  - in every tool's report folder: command_log.html / .txt / .json,
  - inside pytest's report.html and Robot Framework's log.html.

Polling loops ("check every 0.25 s until …") are written as ONE line with the
number of tries – otherwise a single wait could produce hundreds of lines.

SAFETY RULE: logging must never change or break a test. Results are shown
without touching pywinauto search objects (asking them anything starts a
window search), and every formatting step is protected by try/except.
"""
from __future__ import annotations

import html
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, List

TESTS_DIR = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()
LEFT_WIDTH = 92          # width of the command column in the terminal

KIND_INDENT = {"test": 0, "result": 0, "phase": 2, "step": 2, "command": 6, "check": 6}

# Small helper functions whose CALLER is the interesting source line.
HELPER_FUNCTIONS = {"call", "wait_until", "_sleep", "_key", "_check", "_reg", "_copy", "_delete",
                    "_add", "command", "check", "step", "phase", "begin_test", "end_test"}

# pywinauto objects that start a window search when you ask them anything.
SEARCH_OBJECT_TYPES = {"WindowSpecification", "Desktop", "Application"}


# ── Short, readable form of arguments and results ───────────────────────
def short(value) -> str:
    try:
        return _short(value)
    except Exception:
        return f"<{type(value).__name__}>"


def _short(value) -> str:
    type_name = type(value).__name__
    if type_name in SEARCH_OBJECT_TYPES:      # never touch: would search a window
        return "" if type_name == "WindowSpecification" else f"<{type_name}>"
    if value is None:
        return ""
    if isinstance(value, (bool, int, float)):
        return repr(value)
    if isinstance(value, str):
        return repr(value if len(value) <= 70 else value[:67] + "…")
    if isinstance(value, Path):
        return repr(str(value))
    if isinstance(value, (list, tuple)):
        return f"[{len(value)} items]"
    info = getattr(value, "element_info", None)
    if info is not None:
        return f"<{info.control_type} '{(info.name or '')[:40]}'>"
    if all(hasattr(value, a) for a in ("left", "top", "right", "bottom")):
        return (f"(left={int(value.left)}, top={int(value.top)}, "
                f"right={int(value.right)}, bottom={int(value.bottom)})")
    if hasattr(value, "returncode"):
        return f"exit code {value.returncode}"
    if hasattr(value, "pid"):
        return f"<process pid={value.pid}>"
    if hasattr(value, "size") and hasattr(value, "mode"):
        return f"<image {value.size[0]}x{value.size[1]}>"
    return f"<{type_name}>"


def format_args(args, kwargs) -> str:
    try:
        parts = [_arg(a) for a in args] + [f"{k}={_arg(v)}" for k, v in kwargs.items()]
        return ", ".join(parts)
    except Exception:
        return "…"


def _arg(value) -> str:
    if isinstance(value, (str, int, float, bool, type(None))):
        return repr(value)
    if isinstance(value, Path):
        return repr(str(value))
    if isinstance(value, tuple):
        return "(" + ", ".join(_arg(v) for v in value) + ")"
    if isinstance(value, list):
        return "[" + ", ".join(_arg(v) for v in value) + "]"
    return short(value) or type(value).__name__


# ── Where was the command executed? (file + line) ───────────────────────
def _source() -> tuple:
    """(path relative to tests/, line) of the line that ran the command.
    Frames of this file and of tiny helpers are skipped."""
    try:
        frame = sys._getframe(1)
        while frame is not None:
            file = Path(frame.f_code.co_filename).resolve()
            if file != THIS_FILE and frame.f_code.co_name not in HELPER_FUNCTIONS:
                try:
                    shown = file.relative_to(TESTS_DIR).as_posix()
                except ValueError:
                    shown = file.name
                return shown, frame.f_lineno
            frame = frame.f_back
    except Exception:
        pass
    return "", 0


# ── The log ─────────────────────────────────────────────────────────────
class CommandLog:
    def __init__(self):
        self.entries: List[dict] = []
        self.listeners: List[Callable[[dict], None]] = []
        self.echo = True
        self._quiet = 0
        self._number = 0
        self.test_id = "-"
        self.step_no = 0
        self.step_text = ""

    # ---- structure ------------------------------------------------------
    def begin_test(self, case_id: str, title: str) -> None:
        self.test_id, self.step_no, self.step_text = case_id, 0, ""
        self._add("test", f"TEST {case_id}  {title}", "A new test case starts")

    def phase(self, name: str, explanation: str) -> None:
        self.step_text = name
        self._add("phase", name.upper(), explanation)

    def step(self, readable: str, is_check: bool) -> None:
        self.step_no += 1
        self.step_text = readable
        self._add("step", f"STEP {self.step_no}: {readable}",
                  "CHECK – compares with the expected result" if is_check
                  else "ACTION – does something in the app")

    def end_test(self, status: str, message: str = "") -> None:
        self.step_text = ""
        first = message.splitlines()[0] if message else ""
        self._add("result", f"RESULT {self.test_id}: {status}",
                  first or "All steps passed", ok=(status == "PASS"))
        self.test_id = "-"

    # ---- lines ----------------------------------------------------------
    def command(self, command: str, explanation: str, result: str = "",
                ok: bool = True) -> None:
        if not self._quiet:
            self._add("command", command, explanation, result, ok)

    def check(self, expression: str, explanation: str, ok: bool) -> None:
        self._add("check", f"check: {expression}", explanation,
                  "OK" if ok else "FAILED", ok)

    @contextmanager
    def quiet(self):
        """Commands inside are not written (used for polling loops)."""
        self._quiet += 1
        try:
            yield
        finally:
            self._quiet -= 1

    def _add(self, kind, command, explanation, result="", ok=True) -> None:
        try:
            self._number += 1
            file, line = _source()
            entry = dict(no=self._number, time=time.strftime("%H:%M:%S"),
                         test=self.test_id, step=self.step_no, step_text=self.step_text,
                         kind=kind, command=command, result=result,
                         explanation=explanation, ok=ok, file=file, line=line)
            self.entries.append(entry)
            if self.echo:
                _print(terminal_line(entry))
            for listener in list(self.listeners):
                try:
                    listener(entry)
                except Exception:
                    pass
        except Exception:
            pass          # logging must never break a test

    # ---- output ---------------------------------------------------------
    def entries_for(self, case_id: str) -> List[dict]:
        return [e for e in self.entries if e["test"] == case_id]

    def save(self, folder: Path) -> None:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "command_log.json").write_text(
            json.dumps(self.entries, indent=1, ensure_ascii=False), encoding="utf-8")
        (folder / "command_log.txt").write_text(
            "\n".join(terminal_line(e) for e in self.entries) + "\n", encoding="utf-8")
        (folder / "command_log.html").write_text(
            html_page(self.entries, f"Command log – {folder.name}"), encoding="utf-8")


LOG = CommandLog()


# ── Run a command and log it ────────────────────────────────────────────
def call(owner: str, obj, method: str, *args, explain: str,
         show_result: bool = True, **kwargs):
    """Run `obj.method(*args, **kwargs)` and log it as `owner.method(...)`."""
    function = getattr(obj, method)
    if LOG._quiet:
        return function(*args, **kwargs)
    text = f"{owner}.{method}({format_args(args, kwargs)})"
    try:
        result = function(*args, **kwargs)
    except Exception as e:
        LOG.command(text, explain, f"ERROR {type(e).__name__}: {str(e)[:150]}", ok=False)
        raise
    LOG.command(text, explain, short(result) if show_result else "")
    return result


# ── Terminal ────────────────────────────────────────────────────────────
def terminal_line(e: dict) -> str:
    left = " " * KIND_INDENT.get(e["kind"], 6) + e["command"]
    if e["result"]:
        left += f"  -> {e['result']}"
    if e["kind"] == "test":
        left = "\n" + "=" * 20 + " " + left
    source = f"   [{Path(e['file']).name}:{e['line']}]" if e.get("file") else ""
    if len(left) <= LEFT_WIDTH:
        return f"{left.ljust(LEFT_WIDTH)} | {e['explanation']}{source}"
    return f"{left}\n{' ' * LEFT_WIDTH} | {e['explanation']}{source}"


def _print(text: str) -> None:
    stream = sys.__stdout__ or sys.stdout
    try:
        stream.write(text + "\n")
    except UnicodeEncodeError:
        enc = getattr(stream, "encoding", None) or "ascii"
        stream.write(text.encode(enc, "replace").decode(enc) + "\n")
    stream.flush()


# ── HTML ────────────────────────────────────────────────────────────────
# Fixed column widths: when you zoom in, the page becomes wider than the
# window and you can scroll sideways with ← → (see KEYS_SCRIPT).
_STYLE = """
body{font-family:Segoe UI,Arial,sans-serif;margin:20px}
.hint{color:#555;font-size:13px}
table.log{border-collapse:collapse;table-layout:fixed;width:1880px}
table.log td,table.log th{border-bottom:1px solid #ddd;padding:3px 8px;vertical-align:top;text-align:left;overflow-wrap:anywhere}
table.log th{background:#eee;position:sticky;top:0}
table.log col.no{width:50px} table.log col.time{width:75px} table.log col.cmd{width:640px}
table.log col.res{width:250px} table.log col.exp{width:430px} table.log col.src{width:435px}
td.cmd,td.res,td.src{font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap}
td.res{color:#555} td.src{color:#1a5fb4}
tr.test td{background:#263238;color:#fff;font-weight:600;font-size:14px}
tr.phase td{background:#e8eaf6;font-weight:600}
tr.step td{background:#f3f6fa;font-weight:600}
tr.fail td{background:#fde7e9}
tr.result.pass td{background:#d7f0dd;font-weight:600}
tr.result.fail td{background:#f6c8cc;font-weight:600}
"""

KEYS_SCRIPT = """<script>
// ← → scroll sideways (Shift = faster), Home/End = far left/right.
document.addEventListener('keydown', function (e) {
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
  var step = e.shiftKey ? 600 : 120;
  if (e.key === 'ArrowLeft')  { window.scrollBy({left: -step}); e.preventDefault(); }
  if (e.key === 'ArrowRight') { window.scrollBy({left:  step}); e.preventDefault(); }
  if (e.key === 'Home' && e.altKey) { window.scrollTo({left: 0}); e.preventDefault(); }
  if (e.key === 'End'  && e.altKey) { window.scrollTo({left: document.body.scrollWidth}); e.preventDefault(); }
});
</script>"""


def html_table(entries: List[dict]) -> str:
    rows = []
    for e in entries:
        classes = [e["kind"]]
        if not e["ok"]:
            classes.append("fail")
        if e["kind"] == "result":
            classes.append("pass" if e["ok"] else "fail")
        indent = "&nbsp;" * KIND_INDENT.get(e["kind"], 6)
        source = f"{e['file']}:{e['line']}" if e.get("file") else ""
        rows.append(
            f"<tr class='{' '.join(classes)}'><td>{e['no']}</td><td>{e['time']}</td>"
            f"<td class='cmd'>{indent}{html.escape(e['command'])}</td>"
            f"<td class='res'>{html.escape(e['result'])}</td>"
            f"<td class='exp'>{html.escape(e['explanation'])}</td>"
            f"<td class='src'>{html.escape(source)}</td></tr>")
    return ("<table class='log'><colgroup><col class='no'><col class='time'><col class='cmd'>"
            "<col class='res'><col class='exp'><col class='src'></colgroup>"
            "<tr><th>#</th><th>Time</th><th>Command (exactly as executed)</th>"
            "<th>Result</th><th>What it does (for people)</th>"
            "<th>Executed in (file:line)</th></tr>" + "".join(rows) + "</table>")


def html_page(entries: List[dict], title: str) -> str:
    return (f"<!doctype html><html lang='en'><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{_STYLE}</style><h1>{html.escape(title)}</h1>"
            f"<p class='hint'>{len(entries)} lines · left: the command exactly as executed · "
            f"then: what it does in plain words · right: file and line it was executed from.<br>"
            f"Zoomed in? Use ← → to scroll sideways (Shift + ← → = faster).</p>"
            f"{html_table(entries)}{KEYS_SCRIPT}</html>")


def inline_style() -> str:
    return f"<style>{_STYLE}</style>"
