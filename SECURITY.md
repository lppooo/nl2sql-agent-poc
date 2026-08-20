# Security

This project is a portfolio POC, but it implements several production-oriented guardrails:

- User input guard blocks raw SQL and dangerous commands before planning.
- SQL is parsed by `sqlglot` before execution.
- Only single-statement `SELECT` queries are allowed.
- `SELECT *`, DDL, DML, and unknown tables are rejected.
- A row limit is appended automatically.
- The demo database contains generated sample data only.
- API keys are read from environment variables and must not be committed.

For a real enterprise deployment, use a dedicated read-only database account, query views instead of raw tables, add row-level permissions, audit every query, and require human approval for high-impact actions.
