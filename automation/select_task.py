"""Choose the next manually curated, incomplete development task."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def select(root: Path = ROOT) -> dict | None:
    tasks = json.loads((root / "tasks/backlog.json").read_text(encoding="utf-8"))
    done = set(json.loads((root / "tasks/completed.json").read_text(encoding="utf-8")))
    for task in tasks:
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,78}", task["id"]):
            raise ValueError("Invalid task id")
        if task["id"] not in done:
            return task
    return None


def mark_complete(task_id: str, root: Path = ROOT) -> None:
    tasks = json.loads((root / "tasks/backlog.json").read_text(encoding="utf-8"))
    if task_id not in {t["id"] for t in tasks}:
        raise ValueError("Task is not in the approved backlog")
    file = root / "tasks/completed.json"
    done = json.loads(file.read_text(encoding="utf-8"))
    if task_id not in done:
        done.append(task_id)
    file.write_text(json.dumps(done, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    task = select()
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"has_task={'true' if task else 'false'}\n")
            if task:
                output.write(f"task_id={task['id']}\n")
    print(task["id"] if task else "Backlog completed; add reviewed tasks")
