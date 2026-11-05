"""Validate the patch's changed files and refuse symlinks or protected edits."""
from __future__ import annotations
from pathlib import Path
import subprocess
from automation.agent import ROOT, check_path


def verify(root: Path = ROOT) -> list[str]:
    result = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"],
                                     cwd=root, text=True)
    changed = []
    for row in result.splitlines():
        if len(row) < 4:
            raise ValueError("Unrecognized Git status entry")
        rel = row[3:]
        if " -> " in rel:
            raise ValueError("Renames are not allowed")
        path = check_path(rel, root)
        if path.is_symlink():
            raise ValueError("Symlink edits are not allowed")
        changed.append(rel)
    if not changed:
        raise ValueError("Empty feature patch")
    return changed

if __name__ == "__main__":
    print("Allowed changed files:", ", ".join(verify()))
