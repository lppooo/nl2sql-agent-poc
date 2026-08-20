# Data Analysis Agent

An NL2SQL data-analysis Agent POC for portfolio and interview demos. It converts business questions into safe read-only SQL, executes the query, and returns tabular results, chart specs, and an auditable Agent trace.

The resume-facing target database is **PostgreSQL**. A SQLite fallback is included so the project can run locally without external services.

## Highlights

- NL2SQL workflow for business analytics
- Schema and metric dictionary recall
- Structured SQL planning with optional LLM mode
- Zhipu GLM support through `ZHIPU_API_KEY`
- SQL AST validation with `sqlglot`
- Raw SQL and dangerous-command input guard
- Read-only query execution and automatic `LIMIT`
- Chart selection for KPI, trend, comparison, and table outputs
- FastAPI backend and Streamlit demo UI
- Benchmark and pytest-based local verification

## Architecture

```mermaid
flowchart LR
    A["Business Question"] --> B["Input Guard"]
    B --> C["Schema / Metric Recall"]
    C --> D["SQL Planner"]
    D --> E["SQL AST Validation"]
    E --> F["Read-only Execution"]
    F --> G["Chart Spec"]
    G --> H["Answer + SQL + Trace"]
```

## Tech Stack

- Python 3.10
- FastAPI
- Streamlit
- SQLAlchemy
- PostgreSQL / SQLite
- sqlglot
- LangChain OpenAI-compatible chat model client
- Zhipu GLM via `ZHIPU_API_KEY`

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_db.py
python scripts/run_api.py
```

Run the UI in another terminal:

```powershell
.\.venv\Scripts\activate
python scripts/run_ui.py
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Streamlit UI: `http://localhost:8501`

## PostgreSQL Mode

PostgreSQL is the recommended target database for a resume-facing version:

```powershell
pip install -r requirements-postgres.txt
docker compose up --build
```

The Compose setup starts:

- PostgreSQL 16
- FastAPI backend
- Streamlit frontend

## LLM Mode

The project can run without an API key. To use your Zhipu model:

```env
USE_LLM=true
LLM_PROVIDER=zhipu
LLM_MODEL=glm-5-turbo
ZHIPU_API_KEY=
```

Keep the actual key in your system environment variable:

```powershell
$env:ZHIPU_API_KEY=<your-zhipu-api-key>
```

Do not commit `.env`.

## Example Questions

- 上个月各渠道GMV是多少？
- 近30天GMV趋势
- 上个月各渠道订单量是多少？
- 近30天各渠道客单价是多少？
- 2026年7月华东区GMV是多少？
- 上个月各品类销量是多少？

## Validation

```powershell
python -m unittest discover -s tests
python -m app.evaluate
python scripts/security_check.py
```

Current local benchmark:

```text
pass_rate=10/10=100.00%
```

## Documentation

- [Architecture](docs/architecture.md)
- [Usage](docs/USAGE.md)
- [Customization](docs/CUSTOMIZATION.md)
- [Security](SECURITY.md)

## Portfolio Notes

This project is designed to support the following resume claim:

> Built an NL2SQL data-analysis Agent with schema recall, SQL generation, SQL AST validation, read-only execution, automatic chart generation, and benchmark evaluation. Reduced repeated analyst query workflows from manual SQL/reporting to minute-level Agent interaction in a controlled POC.

For interview discussion, focus on:

- Why PostgreSQL is the target database
- How schema and metric dictionaries reduce SQL hallucination
- Why SQL must be validated with AST parsing instead of prompt rules only
- How dangerous user input is blocked
- How benchmark cases separate high-frequency, boundary, and abnormal scenarios
