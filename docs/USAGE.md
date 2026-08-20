# Usage

## Local SQLite demo

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_db.py
python scripts/run_api.py
```

In another terminal:

```powershell
.\.venv\Scripts\activate
python scripts/run_ui.py
```

Open:

- API: `http://127.0.0.1:8000/docs`
- UI: `http://localhost:8501`

## PostgreSQL demo

```powershell
pip install -r requirements-postgres.txt
$env:ZHIPU_API_KEY=$env:ZHIPU_API_KEY
docker compose up --build
```

The Compose setup starts PostgreSQL, the FastAPI backend, and the Streamlit UI.

## Example questions

- 上个月各渠道GMV是多少？
- 近30天GMV趋势
- 上个月各渠道订单量是多少？
- 近30天各渠道客单价是多少？
- 2026年7月华东区GMV是多少？
- 上个月各品类销量是多少？

## API call

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/query `
  -ContentType "application/json" `
  -Body '{"question":"上个月各渠道GMV是多少？","include_trace":true}'
```

## Local validation

```powershell
python -m unittest discover -s tests
python -m app.evaluate
python scripts/security_check.py
```
