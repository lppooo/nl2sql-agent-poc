# Customization

## Change the database

Use PostgreSQL for a resume-facing deployment:

```env
DATABASE_URL=postgresql+pg8000://user:password@localhost:5432/agent_demo
SQL_DIALECT=postgres
```

Use SQLite for a zero-dependency local demo:

```env
DATABASE_URL=sqlite:///data/agent_demo.db
SQL_DIALECT=sqlite
```

## Change the model

This project reads `ZHIPU_API_KEY` directly from the environment.

```env
USE_LLM=true
LLM_PROVIDER=zhipu
LLM_MODEL=glm-5-turbo
ZHIPU_API_KEY=
```

For another OpenAI-compatible provider:

```env
USE_LLM=true
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## Add a metric

Edit `app/bootstrap.py` in `write_metadata_files()`:

```python
"refund_rate": {
    "definition": "退款订单数 / 支付订单数",
    "expression": "COUNT(refunded_orders) / COUNT(paid_orders)",
    "filters": [],
}
```

Then update `app/planner.py` so the planner can map user wording to the metric.

## Add a table

1. Add the SQLAlchemy table in `app/bootstrap.py`.
2. Add the table description to `schema_dictionary.json` generation.
3. Add the table name to `allowed_tables` in `app/config.py`.
4. Add at least one benchmark case in `data/benchmark.jsonl`.
5. Run `python -m app.evaluate` and `pytest`.

## About SKILL.md

This repository is a portfolio application, not a Codex Skill package. A Codex Skill requires a dedicated `SKILL.md` with YAML frontmatter and procedural instructions for another agent. Adding one here would make the repository look like an installable agent skill, which is not the goal. The appropriate artifacts for this project are `README.md`, `docs/USAGE.md`, `docs/CUSTOMIZATION.md`, and `SECURITY.md`.
