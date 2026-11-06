"""One bounded, source-only repair attempt for AI-generated code.

This module is invoked in a secret-bearing step that NEVER executes generated
source or tests. A later, secret-free CI step verifies the candidate.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from automation.agent import MAX_BYTES, ROOT, check_path, generate, make_prompt
from automation.select_task import select


def changed_source_paths(root: Path = ROOT) -> set[str]:
    """Only source paths already changed by the original proposal are eligible."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "src", "app.py"],
        cwd=root, text=True, capture_output=True, check=True,
    )
    names = set()
    for name in result.stdout.splitlines():
        if name == "app.py" or (name.startswith("src/") and name.endswith(".py")):
            path = check_path(name, root)
            if path.is_symlink():
                raise ValueError("Symlink repairs are forbidden")
            names.add(name)
    if not names:
        raise ValueError("No previously modified source files to repair")
    return names


def apply_source_repair(proposal: dict, allowed: set[str], root: Path = ROOT) -> list[str]:
    """Validate entire repair before writing; prohibit test and workflow edits."""
    files = proposal.get("files") if isinstance(proposal, dict) else None
    if not isinstance(files, list) or not (1 <= len(files) <= 4):
        raise ValueError("Expected 1–4 source-only repair files")
    checked = []
    seen = set()
    total = 0
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("content"), str):
            raise ValueError("Malformed repair response")
        rel = item.get("path")
        if not isinstance(rel, str) or rel not in allowed or rel in seen:
            raise ValueError("Repair must target an already modified source file")
        seen.add(rel)
        destination = check_path(rel, root)
        if destination.is_symlink():
            raise ValueError("Symlink repairs are forbidden")
        content = item["content"]
        total += len(content.encode("utf-8"))
        if total > MAX_BYTES:
            raise ValueError("Repair exceeds output size limit")
        if not destination.is_file():
            # Supports new files with git add -N, but not deleted files.
            if not destination.parent.is_dir():
                raise ValueError("Repair directory does not exist")
            current = None
        else:
            current = destination.read_text(encoding="utf-8")
        if content != current:
            checked.append((destination, content))
    if not checked:
        raise ValueError("Repair contains no source changes")
    for destination, content in checked:
        destination.write_text(content, encoding="utf-8")
    return [path.relative_to(root).as_posix() for path, _ in checked]


def repair_prompt(root: Path, task: dict, log: str, allowed: set[str]) -> str:
    return (
        "A first implementation failed CI. Make ONE source-only repair. "
        "DO NOT change tests, documentation, workflows, dependencies, task files or AGENTS.md. "
        "The existing tests are fixed acceptance criteria. Fix implementation code "
        "instead of weakening assertions. Keep empirical forecast uncertainty "
        "clearly described as an estimate, not guaranteed calibrated coverage. "
        "Return JSON with a files array containing complete replacement file contents. "
        "Every path MUST be one of: " + ", ".join(sorted(allowed)) + ".\n"
        "Original task and CURRENT generated source/tests:\n"
        + make_prompt(root, task)
        + "\nCI failure output (latest lines):\n" + log[-10000:]
    )


def main() -> None:
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is required for repair")
    if not args.log.is_file():
        raise SystemExit("Missing failed-test report")
    task = select()
    if task is None:
        raise SystemExit("No pending approved task")
    allowed = changed_source_paths(ROOT)
    log = args.log.read_text(encoding="utf-8", errors="replace")
    models = tuple(x.strip() for x in os.environ.get(
        "GEMINI_MODELS", "gemini-3.5-flash-lite,gemini-2.5-flash-lite"
    ).split(",") if x.strip())
    result = generate(repair_prompt(ROOT, task, log, allowed), key, models)
    updated = apply_source_repair(result, allowed, ROOT)
    print("Source-only repair generated:", ", ".join(updated))


if __name__ == "__main__":
    main()
