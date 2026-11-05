"""Small Gemini code editor: explicit scope, bounded output, no execution permissions.

Only works on reviewed tasks. All output is treated as untrusted code.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from automation.select_task import ROOT, select

ALLOWED_PREFIXES = ("src/", "tests/", "docs/")
MODELS = ("gemini-3.5-flash-lite", "gemini-2.5-flash-lite")
MAX_FILES = 7
MAX_BYTES = 110_000


def check_path(rel: str, root: Path = ROOT) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise ValueError("Unsafe path")
    if rel != "app.py" and not rel.startswith(ALLOWED_PREFIXES):
        raise ValueError("Proposed edit outside allowed source directories")
    parts = Path(rel).parts
    if any(p in {".", ".."} or p.startswith(".") for p in parts):
        raise ValueError("Proposed hidden/parent directory edit")
    if Path(rel).suffix not in {".py", ".md"}:
        raise ValueError("Unsupported extension")
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes project root")
    return path


def apply_files(data: dict, root: Path = ROOT) -> list[str]:
    entries = data.get("files")
    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
        raise ValueError("Expected 1–7 proposed files")
    pending: list[tuple[Path, str]] = []
    total = 0
    seen: set[str] = set()
    source_changed = False
    tests_changed = False
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("content"), str):
            raise ValueError("Invalid source entry")
        rel = entry.get("path")
        path = check_path(rel, root)
        if rel in seen:
            raise ValueError("Duplicate file")
        seen.add(rel)
        content = entry["content"]
        total += len(content.encode("utf-8"))
        if total > MAX_BYTES:
            raise ValueError("Too much generated code")
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        source_changed |= rel == "app.py" or rel.startswith("src/")
        tests_changed |= rel.startswith("tests/")
        pending.append((path, content))
    if not source_changed or not tests_changed:
        raise ValueError("A real source change AND tests are mandatory")
    for path, content in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return [p.relative_to(root).as_posix() for p, _ in pending]


def make_prompt(root: Path, task: dict) -> str:
    # Selected files, no secrets. Keep context small enough for free model tier.
    files = [root / "app.py", root / "src/rescueflow/demo.py",
             root / "src/rescueflow/forecast.py", root / "src/rescueflow/decisions.py",
             root / "src/rescueflow/validation.py", root / "AGENTS.md"]
    files += sorted((root / "tests").glob("test_*.py"))[:12]
    snapshot = {}
    for path in files:
        if path.is_file() and not path.is_symlink():
            snapshot[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")[:22000]
    return ("You are a careful ML engineer working on an evidence-based food rescue dashboard.\n"
            "Implement ONE approved backlog task, with substantive tested code.\n"
            f"Task: {json.dumps(task, ensure_ascii=False)}\n"
            "Mandatory restrictions: modify only app.py, src/*.py, tests/*.py, docs/*.md; "
            "no secrets, no shell commands, no workflow edits, no dependency edits, no network API code "
            "unless the task explicitly allows it. Do not fabricate real-world data, "
            "validation results, performance claims or scientific certainty.\n"
            "Update existing integration points rather than generating unused modules. "
            "Include substantive new or updated unit tests. Keep working public APIs stable. "
            "Return JSON with a files array, each element having path and FULL replacement content. "
            "No markdown fences.\nCurrent source snapshot:\n"
            + json.dumps(snapshot, ensure_ascii=False))


def _request(prompt: str, key: str, model: str) -> dict:
    if not re.fullmatch(r"[a-z0-9.-]+", model):
        raise ValueError("Invalid model identifier")
    schema = {"type": "OBJECT", "properties": {"files": {"type": "ARRAY", "items": {
        "type": "OBJECT", "properties": {"path": {"type": "STRING"},
                                        "content": {"type": "STRING"}},
        "required": ["path", "content"]}}}, "required": ["files"]}
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"responseMimeType": "application/json",
                                    "responseSchema": schema, "maxOutputTokens": 16000}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request = Request(url, data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json", "x-goog-api-key": key},
                      method="POST")
    for attempt in range(3):
        try:
            with urlopen(request, timeout=100) as stream:
                response = json.load(stream)
            content = "".join(p.get("text", "") for p in response["candidates"][0]["content"]["parts"])
            return json.loads(content)
        except HTTPError as exc:
            if exc.code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(8 * (2 ** attempt))
                continue
            if exc.code in (404, 500, 502, 503, 504):
                raise RuntimeError(f"Model {model} unavailable (HTTP {exc.code})") from exc
            if exc.code == 429:
                raise ValueError("Gemini free tier quota exhausted (HTTP 429); no changes made") from exc
            raise ValueError(f"Gemini access/request rejected (HTTP {exc.code}); check model and API key") from exc
        except (URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(8 * (2 ** attempt))
                continue
            raise RuntimeError(f"Model {model} network unavailable") from exc
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ValueError("Incomplete or malformed model response") from exc
    raise RuntimeError("Model request failed")


def generate(prompt: str, key: str, models: tuple[str, ...] = MODELS) -> dict:
    errors = []
    for model in models[:2]:
        try:
            print("Trying free Gemini model:", model, flush=True)
            return _request(prompt, key, model)
        except RuntimeError as exc:
            errors.append(str(exc))
    raise RuntimeError(" | ".join(errors))


def main() -> None:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("Missing GEMINI_API_KEY secret")
    task = select()
    if task is None:
        print("All reviewed tasks are complete")
        return
    models = tuple(x.strip() for x in os.getenv("GEMINI_MODELS", ",".join(MODELS)).split(",") if x.strip())
    changed = apply_files(generate(make_prompt(ROOT, task), key, models))
    print("Task", task["id"], "generated:", ", ".join(changed))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        print("Generation did not complete:", exc, file=sys.stderr)
        raise SystemExit(1)
