"""Run TatamiFit's complete local, CI, and release acceptance gate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import cast
from zipfile import ZipFile

ROOT = Path(__file__).parents[1]
REPAIR = ROOT / "examples" / "repair-room.json"
NARROW = ROOT / "examples" / "narrow-room.json"
NO_LAYOUT = ROOT / "examples" / "no-layout.json"
INVALID = ROOT / "examples" / "invalid-fixed-overlap.json"
COMMITTED_DEMO = ROOT / "docs" / "demo"
ENVIRONMENT = os.environ.copy()
ENVIRONMENT["PYTHONUTF8"] = "1"
ENVIRONMENT["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
ENVIRONMENT.setdefault("UV_CACHE_DIR", str(ROOT / ".uv-cache"))


def run(
    command: Sequence[str], *, expected: int = 0, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}", flush=True)
    result = subprocess.run(
        list(command),
        cwd=ROOT,
        env=ENVIRONMENT,
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode != expected:
        if capture:
            print(result.stdout, end="", file=sys.stdout)
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(
            f"command exited {result.returncode}; expected {expected}: {' '.join(command)}"
        )
    return result


def check_runtime_dependencies() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    dependencies = cast(list[object], project["dependencies"])
    if dependencies:
        raise SystemExit(f"runtime dependencies must remain empty: {dependencies}")


def exercise_examples(temporary: Path) -> None:
    repair_output = temporary / "repair"
    narrow_output = temporary / "narrow"
    no_layout_output = temporary / "no-layout"
    invalid_output = temporary / "invalid"
    demo_output = temporary / "demo"
    python = sys.executable

    run([python, "-m", "tatamifit", "plan", str(REPAIR), "--out", str(repair_output)])
    repair = load_layout(repair_output)
    summary = cast(dict[str, object], repair["summary"])
    if summary["mat_count"] != 8 or summary["retained_count"] != 4:
        raise SystemExit(f"repair example has unexpected summary: {summary}")
    assert_artifact_set(repair_output)

    run([python, "-m", "tatamifit", "plan", str(NARROW), "--out", str(narrow_output)])
    narrow = load_layout(narrow_output)
    narrow_summary = cast(dict[str, object], narrow["summary"])
    if narrow_summary["mat_count"] != 4:
        raise SystemExit(f"narrow boundary example has unexpected summary: {narrow_summary}")

    no_layout = run(
        [python, "-m", "tatamifit", "plan", str(NO_LAYOUT), "--out", str(no_layout_output)],
        expected=1,
        capture=True,
    )
    if (
        no_layout_output.exists()
        or "NO_LAYOUT" not in no_layout.stderr
        or "Repair:" not in no_layout.stderr
    ):
        raise SystemExit("valid no-layout example did not preserve its failure contract")

    invalid = run(
        [python, "-m", "tatamifit", "plan", str(INVALID), "--out", str(invalid_output)],
        expected=2,
        capture=True,
    )
    if invalid_output.exists() or "FIXED_MATS_OVERLAP" not in invalid.stderr:
        raise SystemExit("invalid fixed-overlap example did not preserve its failure contract")

    run([python, "-m", "tatamifit", "demo", "--out", str(demo_output)])
    assert_artifact_set(demo_output)
    compare_artifacts(demo_output, COMMITTED_DEMO)


def exercise_package(temporary: Path) -> None:
    assets = temporary / "assets"
    run(
        [
            "uv",
            "build",
            "--no-sources",
            "--clear",
            "--no-create-gitignore",
            "--out-dir",
            str(assets),
        ]
    )
    expected_assets = {"tatamifit-0.1.0-py3-none-any.whl", "tatamifit-0.1.0.tar.gz"}
    actual_assets = {path.name for path in assets.iterdir()}
    if actual_assets != expected_assets:
        raise SystemExit(f"unexpected release assets: {sorted(actual_assets)}")

    wheel = assets / "tatamifit-0.1.0-py3-none-any.whl"
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required_modules = {
            "tatamifit/__init__.py",
            "tatamifit/__main__.py",
            "tatamifit/cli.py",
            "tatamifit/model.py",
            "tatamifit/render.py",
            "tatamifit/solver.py",
        }
        if not required_modules.issubset(names):
            raise SystemExit(f"wheel is missing modules: {sorted(required_modules - names)}")

    clean_environment = temporary / "clean-environment"
    run([sys.executable, "-m", "venv", str(clean_environment)])
    clean_python = python_in(clean_environment)
    run([str(clean_python), "-m", "pip", "install", "--no-deps", str(wheel)])
    executable = executable_in(clean_environment, "tatamifit")
    version = run([str(executable), "--version"], capture=True)
    if version.stdout.strip() != "tatamifit 0.1.0":
        raise SystemExit(f"unexpected installed version output: {version.stdout!r}")

    installed_output = temporary / "installed-repair"
    run([str(executable), "plan", str(REPAIR), "--out", str(installed_output)])
    installed_layout = load_layout(installed_output)
    installed_summary = cast(dict[str, object], installed_layout["summary"])
    if installed_summary["retained_count"] != 4:
        raise SystemExit("installed CLI did not solve the real repair example")

    installed_demo = temporary / "installed-demo"
    run([str(executable), "demo", "--out", str(installed_demo)])
    compare_artifacts(installed_demo, COMMITTED_DEMO)

    installed_failure = run(
        [str(executable), "plan", str(NO_LAYOUT), "--out", str(temporary / "installed-fail")],
        expected=1,
        capture=True,
    )
    if "NO_LAYOUT" not in installed_failure.stderr or "Repair:" not in installed_failure.stderr:
        raise SystemExit("installed CLI did not preserve the no-layout failure contract")


def load_layout(output: Path) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((output / "layout.json").read_text(encoding="utf-8")),
    )


def assert_artifact_set(output: Path) -> None:
    actual = {path.name for path in output.iterdir()}
    expected = {"layout.json", "layout.svg", "layout.txt"}
    if actual != expected:
        raise SystemExit(f"unexpected artifacts in {output}: {sorted(actual)}")


def compare_artifacts(actual: Path, expected: Path) -> None:
    assert_artifact_set(actual)
    assert_artifact_set(expected)
    for name in ("layout.json", "layout.svg", "layout.txt"):
        if (actual / name).read_bytes() != (expected / name).read_bytes():
            raise SystemExit(f"generated {name} differs from the committed README demo")


def executable_in(virtual_environment: Path, name: str) -> Path:
    if os.name == "nt":
        return virtual_environment / "Scripts" / f"{name}.exe"
    return virtual_environment / "bin" / name


def python_in(virtual_environment: Path) -> Path:
    if os.name == "nt":
        return virtual_environment / "Scripts" / "python.exe"
    return virtual_environment / "bin" / "python"


def main() -> int:
    run(["uv", "lock", "--check"])
    run(["uv", "run", "--no-sync", "ruff", "format", "--check", "."])
    run(["uv", "run", "--no-sync", "ruff", "check", "."])
    run(["uv", "run", "--no-sync", "mypy", "src", "tests", "scripts"])
    run(
        [
            "uv",
            "run",
            "--no-sync",
            "pytest",
            "--basetemp",
            str(ROOT / ".test-tmp"),
            "--cov=tatamifit",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ]
    )
    check_runtime_dependencies()
    with tempfile.TemporaryDirectory(prefix="tatamifit-check-") as directory:
        temporary = Path(directory)
        exercise_examples(temporary)
        exercise_package(temporary)
    print("TatamiFit release gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
