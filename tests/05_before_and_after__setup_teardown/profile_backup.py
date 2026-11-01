"""STEP 05 – BEFORE AND AFTER: protection of your real Wave Pro data

Wave Pro stores data outside the music folder:
    Registry   HKCU\\Software\\WavePro\\Wave Pro - Music Studio   (settings)
    %APPDATA%\\WavePro\\Wave Pro - Music Studio\\changelog.csv      (change history)
    %APPDATA%\\WavePro\\Wave Pro - Music Studio\\pending_queue.json (unfinished tasks)

backup()            once before all tests: copy everything, verify the copies
prepare_for_test()  before every test: empty settings, point to the test library
restore()           once after all tests: put everything back exactly

Rule: nothing is changed until the backup is complete and verified
(file COMPLETE). If a run crashes, the next run restores the backup first.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from command_log import LOG, call

REG_KEY = r"HKCU\Software\WavePro\Wave Pro - Music Studio"
GUARDED_FILES = ("pending_queue.json", "changelog.csv")
DEFAULT_BACKUP_DIR = Path(__file__).resolve().parent / ".profile_backup"


_REG_EXPLAIN = {
    "query": "Registry: do Wave Pro settings exist?",
    "export": "Registry: BACK UP the Wave Pro settings to a file",
    "delete": "Registry: remove the Wave Pro settings (clean start)",
    "add": "Registry: tell Wave Pro to open the temporary test library",
    "import": "Registry: RESTORE your original Wave Pro settings",
}


def _reg(*args: str) -> subprocess.CompletedProcess:
    return call("subprocess", subprocess, "run", ["reg", *args], capture_output=True, text=True,
                explain=_REG_EXPLAIN.get(args[0], "Registry command"))


def _copy(src: Path, dst: Path, explain: str) -> None:
    call("shutil", shutil, "copy2", src, dst, explain=explain)


def _delete(path: Path, explain: str) -> None:
    call("Path", path, "unlink", explain=explain)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProfileGuard:

    def __init__(self, backup_dir: Optional[Path] = None,
                 appdata_dir: Optional[Path] = None):
        self.backup_dir = Path(backup_dir or DEFAULT_BACKUP_DIR)
        self.appdata_dir = Path(appdata_dir or (
            Path(os.environ.get("APPDATA", Path.home()))
            / "WavePro" / "Wave Pro - Music Studio"))

    @property
    def _complete(self) -> Path:
        return self.backup_dir / "COMPLETE"

    def backup(self) -> None:
        if self._complete.is_file():          # an earlier run crashed
            self.restore()
        elif self.backup_dir.exists():        # incomplete backup:
            shutil.rmtree(self.backup_dir)    # originals were never touched
        call("Path", self.backup_dir, "mkdir", parents=True,
             explain="Create the backup folder")

        had_key = _reg("query", REG_KEY).returncode == 0
        if had_key:
            reg_file = self.backup_dir / "settings.reg"
            r = _reg("export", REG_KEY, str(reg_file), "/y")
            if r.returncode != 0 or not reg_file.is_file():
                raise RuntimeError(f"Registry backup failed: {r.stderr}")

        saved = []
        for name in GUARDED_FILES:
            src = self.appdata_dir / name
            if src.is_file():
                dst = self.backup_dir / name
                _copy(src, dst, f"BACK UP your {name}")
                same = _sha256(src) == _sha256(dst)
                LOG.check(f"sha256(original {name}) == sha256(backup)",
                          "Is the backup an exact copy?", same)
                if not same:
                    raise RuntimeError(f"Backup of {name} is corrupt.")
                saved.append(name)

        self._complete.write_text(
            json.dumps({"had_key": had_key, "files": saved}), encoding="utf-8")
        LOG.command(f"write {self._complete}", "Mark the backup as complete and verified")

    def prepare_for_test(self, library: Path) -> None:
        """Clean start: empty settings, only the test library."""
        if not self._complete.is_file():
            raise RuntimeError("Safety stop: no complete backup.")
        _reg("delete", REG_KEY, "/f")
        r = _reg("add", REG_KEY, "/v", "root_path", "/t", "REG_SZ",
                 "/d", str(Path(library).resolve()), "/f")
        if r.returncode != 0:
            raise RuntimeError(f"Writing the registry failed: {r.stderr}")
        queue = self.appdata_dir / "pending_queue.json"
        if queue.is_file():       # the original is safely in the backup
            _delete(queue, "Remove unfinished tasks for the test (original is in the backup)")

    def forget_library_cache(self, library: Path) -> None:
        """Remove the cache file Wave Pro creates for the test library."""
        h = hashlib.md5(str(Path(library).resolve()).encode()).hexdigest()
        cache = self.appdata_dir / f"music_library_cache_{h}.json"
        if cache.is_file():
            _delete(cache, "Remove the cache file Wave Pro made for the test library")

    def restore(self) -> None:
        if not self._complete.is_file():
            return
        info = json.loads(self._complete.read_text(encoding="utf-8"))
        _reg("delete", REG_KEY, "/f")
        if info["had_key"]:
            r = _reg("import", str(self.backup_dir / "settings.reg"))
            if r.returncode != 0:
                raise RuntimeError(
                    f"Restoring the registry failed: {r.stderr}\n"
                    f"The backup is kept in: {self.backup_dir}")
        for name in GUARDED_FILES:
            dst = self.appdata_dir / name
            if name in info["files"]:
                self.appdata_dir.mkdir(parents=True, exist_ok=True)
                _copy(self.backup_dir / name, dst, f"RESTORE your original {name}")
            elif dst.is_file():       # did not exist before → created by a test
                _delete(dst, f"Remove {name} (it did not exist before the tests)")
        call("shutil", shutil, "rmtree", self.backup_dir,
             explain="Remove the temporary backup folder (everything is restored)")
