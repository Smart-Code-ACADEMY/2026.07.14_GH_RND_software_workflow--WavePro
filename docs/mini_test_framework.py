"""
mini_test_framework.py - ALL principles of our big test suite in ONE file.

Only the Python standard library. No Wave Pro, no pywinauto:
the "app" here is a tiny shopping list, so you can focus on the principles.

Run all tests:   python mini_test_framework.py          (asks which tests)
Run one test:    set MINI_TESTS=TC-02   (Windows cmd)  then  python mini_test_framework.py

Where each PART lives in the big suite:
  PART 1  test specification    -> 01_.../test_cases.yaml
  PART 2  app under test        -> the real Wave Pro EXE
  PART 3  command log           -> 04_.../*_command_log.py
  PART 4  app driver            -> 04_.../*_app_driver.py
  PART 5  keyword library       -> 03_.../*__keyword_library.py
  PART 6  spec loader           -> 02_.../*__spec_loader.py
  PART 7  setup / teardown      -> 05_.../*__session.py, *__profile_guard.py, *__temp_music_library.py
  PART 8  test selection        -> 07_.../*__test_selection_popup.py
  PART 9  test runner + report  -> 06_.../6c_pywinauto_only + 08_results__reports
"""
import functools
import inspect
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# ════ PART 1 - TEST SPECIFICATION: WHAT to test (data, not code) ═══════════
# Written in plain words. People can read and change it without knowing Python.
# The big suite uses YAML; JSON is the same idea and is in the standard library.
SPEC_TEXT = """
{"test_cases": [
  {"id": "TC-01", "title": "Add one item",
   "steps": [{"Add Item": ["Milk"]},
             {"Item Count Should Be": ["1"]}]},

  {"id": "TC-02", "title": "Add two items, remove one",
   "steps": [{"Add Item": ["Milk"]},
             {"Add Item": ["Bread"]},
             {"Remove Item": ["Milk"]},
             {"List Should Contain": ["Bread"]},
             {"Item Count Should Be": ["1"]}]},

  {"id": "TC-03", "title": "List is saved to a file",
   "steps": [{"Add Item": ["Eggs"]},
             {"Save List": []},
             {"Saved File Should Contain": ["Eggs"]}]}
]}
"""


# ════ PART 2 - APP UNDER TEST: the program we test ═════════════════════════
class ShoppingList:
    def __init__(self, folder: Path):
        self.folder = folder
        self.items = []

    def add(self, name):
        self.items.append(name)

    def remove(self, name):
        self.items.remove(name)

    def save(self) -> Path:
        file = self.folder / "list.txt"
        file.write_text("\n".join(self.items), encoding="utf-8")
        return file


# ════ PART 3 - COMMAND LOG: write down EVERY executed command ══════════════
LOG = []   # one entry per command: (command, result, what it does, file:line)


def logged(explanation):
    """Decorator WITH an argument -> 3 nested functions:
    logged("...") returns `decorator`, decorator(func) returns `wrapper`,
    and `wrapper` runs instead of func every time func is called."""
    def decorator(func):
        @functools.wraps(func)                    # wrapper keeps func's name and docstring
        def wrapper(self, *args):
            caller = inspect.stack()[1]           # [0] = wrapper, [1] = who called it
            where = f"{Path(caller.filename).name}:{caller.lineno}"
            command = f"{func.__name__}({', '.join(map(repr, args))})"
            try:
                result = func(self, *args)        # run the REAL function
            except Exception as error:
                LOG.append((command, f"ERROR: {error}", explanation, where))
                raise                             # log it, then let the error continue
            LOG.append((command, repr(result), explanation, where))
            return result
        return wrapper
    return decorator


# ════ PART 4 - APP DRIVER: the ONLY code that touches the app ══════════════
# If the app changes (new button name...), only this class changes.
class Driver:
    def __init__(self, app: ShoppingList):
        self.app = app

    @logged("put an item on the list")            # same as: add_item = logged("...")(add_item)
    def add_item(self, name):
        self.app.add(name)

    @logged("take an item off the list")
    def remove_item(self, name):
        self.app.remove(name)

    @logged("read all items of the list")
    def items(self):
        return list(self.app.items)

    @logged("write the list into list.txt")
    def save(self):
        return self.app.save()


@dataclass
class Context:
    """Everything one test needs. Given to EVERY keyword as first argument."""
    driver: Driver
    folder: Path
    notes: dict = field(default_factory=dict)     # a step can leave info for later steps


# ════ PART 5 - KEYWORD LIBRARY: map step TEXT -> Python FUNCTION ═══════════
@dataclass(frozen=True)                           # frozen = cannot be changed after creation
class Keyword:
    name: str
    func: object
    value_count: int

    @property                                     # used like a field: kw.is_check
    def is_check(self) -> bool:
        return "Should" in self.name              # "... Should ..." = a check (assert)


KEYWORDS = {}                                     # "Add Item" -> Keyword(...)


def keyword(name):
    """Decorator that REGISTERS a function under its step text.
    It returns the function unchanged - it only writes it into KEYWORDS."""
    def register(func):
        value_count = len(inspect.signature(func).parameters) - 1   # minus `ctx`
        KEYWORDS[name] = Keyword(name, func, value_count)
        return func
    return register


@keyword("Add Item")
def add_item(ctx, name):
    ctx.driver.add_item(name)


@keyword("Remove Item")
def remove_item(ctx, name):
    ctx.driver.remove_item(name)


@keyword("Save List")
def save_list(ctx):
    ctx.notes["saved_file"] = ctx.driver.save()


@keyword("Item Count Should Be")
def item_count_should_be(ctx, expected):
    actual = len(ctx.driver.items())
    assert actual == int(expected), f"expected {expected} item(s), found {actual}"


@keyword("List Should Contain")
def list_should_contain(ctx, name):
    items = ctx.driver.items()
    assert name in items, f"'{name}' not in {items}"


@keyword("Saved File Should Contain")
def saved_file_should_contain(ctx, text):
    content = ctx.notes["saved_file"].read_text(encoding="utf-8")
    assert text in content, f"'{text}' not in saved file: {content!r}"


# ════ PART 6 - SPEC LOADER: read + CHECK the spec BEFORE anything runs ═════
class SpecificationError(Exception):
    """A mistake in the specification (typo in a step name, wrong values...)."""


@dataclass(frozen=True)
class Step:
    name: str
    values: tuple


@dataclass(frozen=True)
class TestCase:
    id: str
    title: str
    steps: tuple


def load_specification(text=SPEC_TEXT) -> list:
    data = json.loads(text)                       # text -> Python dict / list
    cases, seen_ids = [], set()
    for raw in data["test_cases"]:
        if raw["id"] in seen_ids:
            raise SpecificationError(f"ID {raw['id']} is used twice")
        seen_ids.add(raw["id"])
        steps = []
        for number, step in enumerate(raw["steps"], start=1):
            (name, values), = step.items()        # exactly ONE "name: values" pair
            where = f"{raw['id']} step {number}"
            if name not in KEYWORDS:
                raise SpecificationError(f"{where}: unknown step '{name}'")
            if len(values) != KEYWORDS[name].value_count:
                raise SpecificationError(f"{where}: '{name}' needs "
                                         f"{KEYWORDS[name].value_count} value(s)")
            steps.append(Step(name, tuple(values)))
        if not any(KEYWORDS[s.name].is_check for s in steps):
            raise SpecificationError(f"{raw['id']}: no check ('... Should ...')")
        cases.append(TestCase(raw["id"], raw["title"], tuple(steps)))
    return cases


def run_test_case(ctx, case):
    """Run the steps in order. A failure message names the step."""
    for number, step in enumerate(case.steps, start=1):
        try:
            KEYWORDS[step.name].func(ctx, *step.values)   # text -> function call
        except AssertionError as error:
            raise AssertionError(f"step {number} '{step.name}' "
                                 f"{list(step.values)}: {error}") from None


# ════ PART 7 - SETUP / TEARDOWN: same start + clean end for EVERY test ═════
SETTINGS = {"theme": "dark"}   # stands for the user's real settings (registry in big suite)


@contextmanager                                   # decorator: makes a `with` block from a generator
def protect_user_settings():
    """Session begin/end (profile guard): backup -> tests run -> ALWAYS restore."""
    backup = dict(SETTINGS)
    try:
        yield                                     # here the `with` block runs (all tests)
    finally:                                      # runs even after an error or Ctrl+C
        SETTINGS.clear()
        SETTINGS.update(backup)


def start_test(case) -> Context:
    """Fresh app + fresh test data -> every test is independent of the others."""
    print(f"\n▶ {case.id} {case.title}")
    LOG.clear()
    folder = Path(tempfile.mkdtemp(prefix="minitest_"))   # new temp folder per test
    SETTINGS["theme"] = "test"                    # tests may change settings...
    return Context(Driver(ShoppingList(folder)), folder)


def end_test(ctx):
    """...and are cleaned up. Safety: delete ONLY our own temp folder."""
    if (ctx.folder.parent == Path(tempfile.gettempdir())
            and ctx.folder.name.startswith("minitest_")):
        shutil.rmtree(ctx.folder)


# ════ PART 8 - TEST SELECTION: run one test, some tests or all ═════════════
def select_test_cases(cases) -> list:
    ids = [c.id for c in cases]
    raw = os.environ.get("MINI_TESTS") or input(f"Which tests? {ids}  e.g. TC-02  (Enter = all): ")
    raw = raw.strip()
    if not raw or raw.upper() == "ALL":
        return cases
    wanted = {x.strip() for x in raw.split(",")}
    unknown = wanted - set(ids)
    if unknown:
        raise SpecificationError(f"not in the specification: {sorted(unknown)}")
    return [c for c in cases if c.id in wanted]


# ════ PART 9 - TEST RUNNER + REPORT ════════════════════════════════════════
def print_command_log():
    for number, (command, result, explanation, where) in enumerate(LOG, start=1):
        print(f"   {number:>2}  {command:<22} -> {result:<28} {explanation:<30} [{where}]")


def main() -> int:
    cases = select_test_cases(load_specification())   # spec errors stop us HERE
    results = []
    with protect_user_settings():                 # session: begin ... end
        for case in cases:
            ctx = start_test(case)                # setup
            try:
                run_test_case(ctx, case)          # the test itself
                status, message = "PASS", ""
            except AssertionError as error:
                status, message = "FAIL", str(error)
            finally:
                end_test(ctx)                     # teardown - ALWAYS, pass or fail
            print_command_log()
            print(f"   {status} {message}")
            results.append((case.id, status))

    print("\n══ REPORT ══")
    for case_id, status in results:
        print(f"   {case_id}: {status}")
    passed = sum(status == "PASS" for _, status in results)
    print(f"   {passed}/{len(results)} passed   (settings restored: {SETTINGS})")
    return 0 if passed == len(results) else 1     # exit code 0 = all good (for CI)


if __name__ == "__main__":                        # only when started directly, not on import
    raise SystemExit(main())
