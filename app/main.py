"""FastAPI entry point for the KPI dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import charts, user_charts
from app.data import get_kpi_cards
from app.user_data import get_user_monitor_summary, load_sessions, load_users, NOW

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="KPI Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "cards": get_kpi_cards(),
        "charts": [
            charts.revenue_trend_chart(),
            charts.orders_and_customers_chart(),
            charts.churn_nps_chart(),
            charts.region_attainment_chart(),
        ],
    }
    return templates.TemplateResponse(request, "dashboard.html", context)


@app.get("/api/kpis")
def kpis() -> list[dict]:
    return [
        {
            "name": card.name,
            "value": card.value,
            "target": card.target,
            "unit": card.unit,
            "attainment_pct": round(card.attainment, 2),
            "change_pct": round(card.change_pct, 2),
            "status": card.status,
        }
        for card in get_kpi_cards()
    ]


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request) -> HTMLResponse:
    s = get_user_monitor_summary()
    cards = [
        {"label": "Total users", "value": s.total_users, "tone": "on-track",
         "note": f"{s.force_reset_count} must reset password"},
        {"label": "Active (7d)", "value": s.active_users_7d, "tone": "on-track",
         "note": f"{s.dormant_users} dormant · {s.inactive_users} inactive"},
        {"label": "Active sessions", "value": s.active_sessions, "tone": "on-track",
         "note": "activity in last 30 min"},
        {"label": "Logins (24h)", "value": s.logins_24h, "tone": "on-track",
         "note": "successful logins"},
        {"label": "2FA enabled", "value": f"{s.twofa_enabled_pct:.0f}%",
         "tone": "at-risk" if s.twofa_enabled_pct < 90 else "on-track",
         "note": "target 90%"},
        {"label": "API error rate (24h)", "value": f"{s.api_error_rate_24h:.2f}%",
         "tone": "at-risk" if s.api_error_rate_24h > 1 else "on-track",
         "note": "target below 1%"},
    ]
    sessions = load_sessions().to_dict("records")
    users = load_users().sort_values("last_login_at", ascending=False).to_dict("records")
    context = {
        "request": request,
        "as_of": NOW.strftime("%Y-%m-%d %H:%M"),
        "cards": cards,
        "charts": [
            user_charts.hourly_activity_chart(),
            user_charts.user_status_chart(),
            user_charts.group_breakdown_chart(),
        ],
        "sessions": sessions,
        "users": users,
    }
    return templates.TemplateResponse(request, "users.html", context)


@app.get("/api/users/summary")
def users_summary() -> dict:
    s = get_user_monitor_summary()
    return {
        "total_users": s.total_users,
        "active_users_7d": s.active_users_7d,
        "dormant_users": s.dormant_users,
        "inactive_users": s.inactive_users,
        "active_sessions": s.active_sessions,
        "logins_24h": s.logins_24h,
        "twofa_enabled_pct": s.twofa_enabled_pct,
        "force_reset_count": s.force_reset_count,
        "api_error_rate_24h": s.api_error_rate_24h,
        "tokens_never_used": s.tokens_never_used,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
