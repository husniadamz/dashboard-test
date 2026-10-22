# Python KPI Dashboard

A FastAPI + Plotly KPI dashboard. It currently runs on sample data and does not connect to a database yet.

## Setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/.

## Endpoints

| Path | Description |
|------|-------------|
| `/` | HTML dashboard: KPI cards and charts |
| `/api/kpis` | JSON list of KPI values, targets, attainment, and status |
| `/health` | Health check |

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Structure

- `app/data.py`: KPI data provider (sample data). Replace `load_monthly_metrics` and `load_region_metrics` with database queries later; keep their return shapes.
- `app/charts.py`: Plotly chart builders.
- `app/main.py`: FastAPI routes.
- `app/templates/dashboard.html`, `app/static/style.css`: page template and styles.
- `tests/`: pytest suite.
