"""Run pytest and report production functions it never reaches.

Optional arguments are passed to pytest, e.g. ``function_coverage_audit.py
tests/test_production_tools_tab.py`` for a fast focused reachability report.
"""

from __future__ import annotations

import ast
import os
import sys
import threading
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "backups",
    "build",
    "contracts",
    "data",
    "dist",
    "invoices",
    "logs",
    "qa_docx",
    "scratch",
    "temp",
    "tests",
}
EXCLUDED_FILES = {
    "daily_qa.py",
    "function_coverage_audit.py",
    "qa_accounting_stress.py",
    "qa_real_user_journey.py",
    "take_screenshot_qt_all.py",
    "test_backend.py",
    "test_exe.py",
    "test_startup.py",
    "test_startup_qt.py",
}
PRODUCTION_SCOPE_EXCLUSIONS = {
    "build_handover.py": "developer handoff generator; not imported by either app entrypoint",
    "build_project.py": "developer project/build helper; not imported by either app entrypoint",
    "clean_repo.py": "developer cleanup/archive utility; not part of either app entrypoint",
    "scratch_lbl.py": "scratch UI experiment; not imported by either app entrypoint",
    "business_lookup.py": "offline lookup placeholder; no production UI/service caller",
    "contract_gen.py": "unwired contract prototype; app documents use core.document_templates",
    "receipt_ai.py": "unwired OCR prototype; production tools use core.online_integrations",
    "core/compliance_loader.py": "legacy YAML loader; not imported by either app entrypoint",
}
INACTIVE_FUNCTION_SCOPES = {
    ("main.py", "App._build_trial_balance_panel"): "legacy panel referenced only by the shadowed reports builder",
    ("main.py", "App._refresh_trial_balance"): "legacy refresh referenced only by the shadowed reports builder",
    ("main.py", "App._build_invoice_main"): "legacy invoice builder referenced only by the shadowed invoice tab",
    ("main.py", "App._inv_log_del"): "unbound placeholder; no UI action exposes inventory-log deletion",
    ("main.py", "App.__init__._on_mousewheel"): "initial callback is replaced by the later App._on_mousewheel binding",
}


@dataclass(frozen=True)
class FunctionDef:
    path: Path
    name: str
    line: int
    first_code_line: int
    scope: str


def _source_files() -> list[Path]:
    files = []
    for current, directories, names in os.walk(ROOT):
        directories[:] = sorted(name for name in directories if name not in EXCLUDED_DIRS)
        for name in names:
            path = Path(current) / name
            relative = path.relative_to(ROOT).as_posix()
            if (
                name.endswith(".py")
                and name not in EXCLUDED_FILES
                and relative not in PRODUCTION_SCOPE_EXCLUSIONS
                and not name.startswith("test_")
            ):
                files.append(path)
    return sorted(files)


def _collect_functions() -> tuple[list[FunctionDef], list[str]]:
    functions: list[FunctionDef] = []
    errors: list[str] = []
    for path in _source_files():
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            compile(tree, str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue

        def visit(node, scope=()):
            next_scope = scope
            if isinstance(node, ast.ClassDef):
                next_scope = (*scope, node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                next_scope = (*scope, node.name)
                first_code_line = min(
                    [node.lineno, *(decorator.lineno for decorator in node.decorator_list)]
                )
                functions.append(FunctionDef(
                    path.resolve(), node.name, node.lineno, first_code_line,
                    ".".join(next_scope),
                ))
            for child in ast.iter_child_nodes(node):
                visit(child, next_scope)

        visit(tree)
    return functions, errors


def _inactive_function_reasons(functions: list[FunctionDef]) -> dict[FunctionDef, str]:
    reasons = {}
    definitions_by_scope = defaultdict(list)
    for function in functions:
        relative_path = function.path.relative_to(ROOT.resolve()).as_posix()
        if function.scope.count(".") == 1:
            definitions_by_scope[(relative_path, function.scope)].append(function)
        reason = INACTIVE_FUNCTION_SCOPES.get((relative_path, function.scope))
        if reason:
            reasons[function] = reason

    for (relative_path, scope), definitions in definitions_by_scope.items():
        if len(definitions) < 2:
            continue
        for function in sorted(definitions, key=lambda item: item.line)[:-1]:
            reasons[function] = "shadowed by a later definition of the same class method"
    return reasons


def _canonical_trace_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _run_coverage_probe(
    functions: list[FunctionDef], inactive: dict[FunctionDef, str]
) -> int:
    source_functions = [*functions, *inactive]
    lookup: dict[tuple[str, str], list[FunctionDef]] = defaultdict(list)
    for function in source_functions:
        lookup[(_canonical_trace_path(function.path), function.name)].append(function)

    reached: set[FunctionDef] = set()
    root_prefix = _canonical_trace_path(ROOT.resolve()) + os.sep

    def profiler(frame, event, _arg):
        if event != "call":
            return
        filename = _canonical_trace_path(frame.f_code.co_filename)
        if not filename.startswith(root_prefix):
            return
        key = (filename, frame.f_code.co_name)
        code_line = frame.f_code.co_firstlineno
        for candidate in lookup.get(key, ()):
            if candidate.first_code_line <= code_line <= candidate.line:
                reached.add(candidate)
                break

    previous_profiler = sys.getprofile()
    previous_thread_profiler = threading.getprofile()

    class TestPhaseProfiler:
        def _track_phase(self):
            self.previous_profiler = sys.getprofile()
            self.previous_thread_profiler = threading.getprofile()
            sys.setprofile(profiler)
            threading.setprofile(profiler)

        def _restore_phase(self):
            sys.setprofile(self.previous_profiler)
            threading.setprofile(self.previous_thread_profiler)

        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_runtest_setup(self, item):
            self._track_phase()
            try:
                yield
            finally:
                self._restore_phase()

        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_runtest_call(self, item):
            self._track_phase()
            try:
                yield
            finally:
                self._restore_phase()

        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_runtest_teardown(self, item):
            self._track_phase()
            try:
                yield
            finally:
                self._restore_phase()

    sys.setprofile(profiler)
    threading.setprofile(profiler)
    try:
        result = pytest.main(["-q", *sys.argv[1:]], plugins=[TestPhaseProfiler()])
    finally:
        sys.setprofile(previous_profiler)
        threading.setprofile(previous_thread_profiler)

    missing = [function for function in functions if function not in reached]
    active_total = len(functions)
    active_reached = active_total - len(missing)
    active_percentage = 100.0 * active_reached / active_total if active_total else 100.0
    source_reached = len(reached.intersection(source_functions))
    source_percentage = 100.0 * source_reached / len(source_functions) if source_functions else 100.0
    print(
        f"\nSource-function execution coverage: {source_reached}/{len(source_functions)} "
        f"({source_percentage:.1f}%) reached by this pytest run."
    )
    print(
        f"Active production-function reachability: {active_reached}/{active_total} "
        f"({active_percentage:.1f}%) reached by this pytest run."
    )
    print("A reached function is not necessarily fully asserted or behaviorally verified.")
    if inactive:
        print("Documented inactive/legacy definitions (excluded from the active denominator):")
        for function, reason in sorted(inactive.items(), key=lambda item: (str(item[0].path), item[0].line)):
            rel_path = function.path.relative_to(ROOT.resolve())
            print(f"- {rel_path}:{function.line} {function.scope}: {reason}")

    by_file: dict[Path, list[FunctionDef]] = defaultdict(list)
    for function in missing:
        by_file[function.path].append(function)
    totals_by_file: dict[Path, int] = defaultdict(int)
    for function in functions:
        totals_by_file[function.path] += 1

    ranked = sorted(
        by_file.items(),
        key=lambda entry: (
            len(entry[1]) / totals_by_file[entry[0]],
            -len(entry[1]),
            str(entry[0]),
        ),
        reverse=True,
    )
    verbose = os.environ.get("VN_SME_AUDIT_VERBOSE") == "1"
    if ranked:
        print("Largest unexercised function groups (add tests or document why unreachable):")
        for path, absent in ranked if verbose else ranked[:15]:
            rel_path = path.relative_to(ROOT.resolve())
            reached_in_file = totals_by_file[path] - len(absent)
            visible = absent if verbose else absent[:8]
            names = ", ".join(f"{fn.name}:{fn.line}" for fn in visible)
            more = f", +{len(absent) - len(visible)} more" if len(absent) > len(visible) else ""
            print(f"- {rel_path}: {reached_in_file}/{totals_by_file[path]} reached; {names}{more}")

    return int(result)


def main() -> int:
    functions, errors = _collect_functions()
    if errors:
        print("Static Python parse/compile audit failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print(
        f"Static Python audit compiled {len(_source_files())} production-scope files "
        "without writing bytecode."
    )
    print("Production-scope exclusions (unwired developer/prototype modules):")
    for path, reason in sorted(PRODUCTION_SCOPE_EXCLUSIONS.items()):
        print(f"- {path}: {reason}")
    inactive = _inactive_function_reasons(functions)
    active = [function for function in functions if function not in inactive]
    return _run_coverage_probe(active, inactive)


if __name__ == "__main__":
    raise SystemExit(main())
