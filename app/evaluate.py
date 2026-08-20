from __future__ import annotations

import json
from pathlib import Path

from app.agent import NL2SQLAgent
from app.bootstrap import build_sample_database, write_metadata_files


def load_benchmark(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                items.append(json.loads(line))
    return items


def main() -> None:
    build_sample_database()
    agent = NL2SQLAgent()
    benchmark_path = Path(__file__).resolve().parents[1] / "data" / "benchmark.jsonl"
    cases = load_benchmark(benchmark_path)
    if not cases:
        print("benchmark.jsonl is empty. Create at least a few test cases first.")
        return

    passed = 0
    total = len(cases)
    for case in cases:
        resp = agent.run(case["question"], include_trace=False)
        if case.get("expected_blocked"):
            ok = not resp.safety_passed and resp.sql is None
        else:
            expected_sql_kw = case.get("expected_sql_contains", [])
            ok = all(kw.lower() in (resp.sql or "").lower() for kw in expected_sql_kw)
        passed += int(ok)
        print(json.dumps({
            "id": case.get("id"),
            "question": case["question"],
            "ok": ok,
            "sql": resp.sql,
            "latency_ms": resp.latency_ms,
            "row_count": len(resp.rows),
        }, ensure_ascii=False))

    print(f"pass_rate={passed}/{total}={passed/total:.2%}")


if __name__ == "__main__":
    main()
