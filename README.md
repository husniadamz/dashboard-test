# PACED Dashboard

PACED (Price, Admission & Clinical Electronic Datahub) is a FastAPI + Plotly dashboard. The Users page reads live data only from the MySQL database `casemix` (`users` and `user_2fa`). KPI figures on the home page still come from the sample database `paced_dashboard`.

## Setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Database

Settings are read from environment variables (nothing is stored in code):

| Variable | Default |
|---|---|
| `CASEMIXPAY_DB_USER` | required |
| `CASEMIXPAY_DB_PASSWORD` | empty |
| `CASEMIXPAY_DB_HOST` | `127.0.0.1` |
| `CASEMIXPAY_DB_PORT` | `3306` |
| `CASEMIXPAY_DB_NAME` | `casemix` (live data, read from `users` and `user_2fa`) |
| `PACED_SAMPLE_DB_NAME` | `paced_dashboard` (sample KPI tables) |

Check the connection at `/api/db/status`.

Create and fill the sample database (safe to re-run; it recreates the sample tables in `PACED_SAMPLE_DB_NAME` only):

```powershell
$env:CASEMIXPAY_DB_USER = 'root'
.\.venv\Scripts\python.exe -m app.seed
```

The seed never writes to `casemix`. The dashboard only reads from it.

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
