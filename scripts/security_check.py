from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
SKIP_FILES = {"agent_demo.db"}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"\n]{8,}['\"]"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password):\s*['\"][^'\"\n]{8,}['\"]"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.name not in SKIP_FILES:
            files.append(path)
    return files


def main() -> int:
    findings: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))

    if findings:
        print("Potential secrets found:")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        return 1

    print("security_check=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
