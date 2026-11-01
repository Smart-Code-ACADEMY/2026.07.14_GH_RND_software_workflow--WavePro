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

LIBRARY_PREFIX = "wavepro_testlib_"          # folder name of every test library
LIBRARY_MARKER = ".wavepro_test_library"     # marker file: "created by the tests"


def song_title(number: int) -> str:
    return f"Artist {number:02d} - Song {number:02d}"


def create_test_library(count: int = SONG_COUNT) -> Path:
    root = Path(tempfile.mkdtemp(prefix=LIBRARY_PREFIX)).resolve()
    (root / LIBRARY_MARKER).write_text(
        "Created by the Wave Pro tests. Safe to delete.\n", encoding="utf-8")
    for category in ("Pop", "Rock", "To-Do"):
        (root / category).mkdir()
    for i in range(1, count + 1):
        category = "Pop" if i % 2 else "Rock"
        with wave.open(str(root / category / f"{song_title(i)}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(8000)
            w.writeframes(b"\x00\x00" * 4000)
    return root


def remove_test_library(root: Path) -> None:
    """Delete ONLY a library created by the tests (checked three times)."""
    root = Path(root).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if not (root.name.startswith(LIBRARY_PREFIX)        # 1. correct name
            and root.parent == temp                      # 2. directly in %TEMP%
            and (root / LIBRARY_MARKER).is_file()):      # 3. marker file present
        raise RuntimeError(f"Safety stop: {root} is not a test library.")
    shutil.rmtree(root, ignore_errors=True)
