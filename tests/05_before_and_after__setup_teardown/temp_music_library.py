"""STEP 05 – BEFORE AND AFTER: temporary music library (test data)

Before every test a fresh library is created in %TEMP%:
    Pop/   Artist 01 - Song 01.wav, Artist 03 - Song 03.wav, …   (odd numbers)
    Rock/  Artist 02 - Song 02.wav, Artist 04 - Song 04.wav, …   (even numbers)
    To-Do/ (empty)
Every file is 0.5 s of silence. Your real music is never touched.
After the test the library is deleted – but ONLY if three checks pass.
"""
from __future__ import annotations

import shutil
import tempfile
import wave
from pathlib import Path

from app_driver import SONG_COUNT
from command_log import LOG, call

LIBRARY_PREFIX = "wavepro_testlib_"          # folder name of every test library
LIBRARY_MARKER = ".wavepro_test_library"     # marker file: "created by the tests"


def song_title(number: int) -> str:
    return f"Artist {number:02d} - Song {number:02d}"


def create_test_library(count: int = SONG_COUNT) -> Path:
    root = Path(call("tempfile", tempfile, "mkdtemp", prefix=LIBRARY_PREFIX,
                     explain="Create a new empty folder in %TEMP% for the test music")).resolve()
    (root / LIBRARY_MARKER).write_text(
        "Created by the Wave Pro tests. Safe to delete.\n", encoding="utf-8")
    LOG.command(f"write {LIBRARY_MARKER}", "Mark the folder as 'created by the tests'")
    for category in ("Pop", "Rock", "To-Do"):
        call("Path", root / category, "mkdir", explain=f"Create the category folder {category}/")
    for i in range(1, count + 1):
        category = "Pop" if i % 2 else "Rock"
        with wave.open(str(root / category / f"{song_title(i)}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(8000)
            w.writeframes(b"\x00\x00" * 4000)
    LOG.command(f"for i in 1..{count}: wave.open(f'{{Pop|Rock}}/Artist {{i:02d}} - Song {{i:02d}}.wav', 'wb')"
                f".writeframes(silence)",
                f"Write {count} silent WAV files (odd numbers → Pop, even → Rock)",
                f"{count} files")
    return root


def remove_test_library(root: Path) -> None:
    """Delete ONLY a library created by the tests (checked three times)."""
    root = Path(root).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    checks = [
        (root.name.startswith(LIBRARY_PREFIX), f"{root.name!r}.startswith({LIBRARY_PREFIX!r})",
         "Safety check 1: does the folder have the test-library name?"),
        (root.parent == temp, f"parent folder == {str(temp)!r}",
         "Safety check 2: is the folder directly in %TEMP%?"),
        ((root / LIBRARY_MARKER).is_file(), f"({LIBRARY_MARKER!r}).is_file()",
         "Safety check 3: does the marker file exist?"),
    ]
    for ok, expression, explanation in checks:
        LOG.check(expression, explanation, ok)
    if not all(ok for ok, _, _ in checks):
        raise RuntimeError(f"Safety stop: {root} is not a test library.")
    call("shutil", shutil, "rmtree", root, ignore_errors=True,
         explain="DELETE the temporary test library (all 3 safety checks passed)")
