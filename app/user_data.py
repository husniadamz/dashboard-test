"""User-system monitoring data provider.

Serves deterministic sample data shaped like the casemix schema
(users, sessions, model_trails, api_requests, api_errors,
personal_access_tokens, user_2fa). Replace the `load_*` functions with
database queries later; keep their return shapes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pandas as pd

# Fixed reference time keeps sample data and tests deterministic.
NOW = pd.Timestamp("2026-10-22 19:00:00")
ACTIVE_SESSION_WINDOW = pd.Timedelta(minutes=30)
ACTIVE_USER_WINDOW = pd.Timedelta(days=7)
DORMANT_USER_WINDOW = pd.Timedelta(days=30)

USER_NAMES = [
    "Aisyah Rahman", "Daniel Tan", "Nur Hidayah", "Ravi Kumar", "Siti Zainab",
    "Lim Wei Jie", "Farah Izzati", "Kevin Ong", "Priya Nair", "Hafiz Aziz",
    "Mei Ling", "Ahmad Faiz", "Chong Yi Xuan", "Nadia Yusof", "Ben Carter",
]
GROUPS = ["admin", "coder", "clinician", "auditor"]
PROVIDERS = [101, 102, 103]
USER_AGENTS = {
    "Chrome / Windows": "Mozilla/5.0 (Windows NT 10.0) Chrome/130.0",
    "Edge / Windows": "Mozilla/5.0 (Windows NT 10.0) Edg/130.0",
    "Safari / macOS": "Mozilla/5.0 (Macintosh) Safari/605.1",
    "Chrome / Android": "Mozilla/5.0 (Linux; Android 14) Chrome/130.0 Mobile",
}


@dataclass(frozen=True)
class UserMonitorSummary:
    total_users: int
    active_users_7d: int
    dormant_users: int
    inactive_users: int
    active_sessions: int
    logins_24h: int
    twofa_enabled_pct: float
    force_reset_count: int
    api_error_rate_24h: float
    tokens_never_used: int


def _status(last_login: pd.Timestamp) -> str:
    age = NOW - last_login
    if age <= ACTIVE_USER_WINDOW:
        return "active"
    if age <= DORMANT_USER_WINDOW:
        return "dormant"
    return "inactive"


def load_users() -> pd.DataFrame:
    """One row per user account."""
    rng = random.Random(42)
    rows = []
    for i, name in enumerate(USER_NAMES):
        # Spread last logins from minutes to ~80 days ago so every status appears.
        hours_ago = rng.choice([0.2, 1, 3, 8, 20, 30, 60, 90, 150, 400, 1200, 1900])
        last_login = NOW - pd.Timedelta(hours=hours_ago)
        rows.append(
            {
                "user_id": 1000 + i,
                "name": name,
                "email": name.lower().replace(" ", ".") + "@example.com",
                "group_code": GROUPS[i % len(GROUPS)],
                "provider_id": PROVIDERS[i % len(PROVIDERS)],
                "last_login_at": last_login,
                "two_factor_enabled": i % 3 != 2,
                "force_password_reset": i % 7 == 6,
                "status": _status(last_login),
            }
        )
    return pd.DataFrame(rows)


def load_sessions() -> pd.DataFrame:
    """Sessions table view: one row per session that is still on record."""
    users = load_users()
    rng = random.Random(7)
    agents = list(USER_AGENTS)
    rows = []
    for _, u in users.head(10).iterrows():
        minutes_ago = rng.choice([2, 5, 12, 25, 45, 120, 600])
        rows.append(
            {
                "user_id": u.user_id,
                "name": u["name"],
                "ip_address": f"10.20.{rng.randint(0, 3)}.{rng.randint(2, 250)}",
                "user_agent": rng.choice(agents),
                "last_activity": NOW - pd.Timedelta(minutes=minutes_ago),
            }
        )
    df = pd.DataFrame(rows)
    df["is_active"] = (NOW - df["last_activity"]) <= ACTIVE_SESSION_WINDOW
    return df.sort_values("last_activity", ascending=False).reset_index(drop=True)


def load_hourly_activity() -> pd.DataFrame:
    """Last 24 hours, one row per hour, across the user system."""
    rng = random.Random(99)
    hours = pd.date_range(end=NOW.floor("h"), periods=24, freq="h")
    rows = []
    for ts in hours:
        business = 1.0 if 7 <= ts.hour <= 18 else 0.25
        rows.append(
            {
                "hour": ts,
                "logins": int(rng.randint(3, 18) * business),
                "model_changes": int(rng.randint(20, 90) * business),
                "api_requests": int(rng.randint(60, 240) * business),
                "api_errors": int(rng.randint(0, 6) * business),
            }
        )
    return pd.DataFrame(rows)


def load_token_stats() -> pd.DataFrame:
    """Personal access tokens: one row per token."""
    return pd.DataFrame(
        {
            "name": ["ci-sync", "reporting", "mobile-app", "old-script", "bi-export"],
            "last_used_at": [
                NOW - pd.Timedelta(hours=2),
                NOW - pd.Timedelta(days=1),
                None,
                NOW - pd.Timedelta(days=120),
                None,
            ],
            "expires_at": [
                NOW + pd.Timedelta(days=60),
                NOW + pd.Timedelta(days=200),
                NOW + pd.Timedelta(days=30),
                NOW - pd.Timedelta(days=10),
                NOW + pd.Timedelta(days=90),
            ],
        }
    )


def get_user_monitor_summary() -> UserMonitorSummary:
    users = load_users()
    sessions = load_sessions()
    hourly = load_hourly_activity()
    tokens = load_token_stats()

    requests_24h = int(hourly["api_requests"].sum())
    errors_24h = int(hourly["api_errors"].sum())
    return UserMonitorSummary(
        total_users=len(users),
        active_users_7d=int((users["status"] == "active").sum()),
        dormant_users=int((users["status"] == "dormant").sum()),
        inactive_users=int((users["status"] == "inactive").sum()),
        active_sessions=int(sessions["is_active"].sum()),
        logins_24h=int(hourly["logins"].sum()),
        twofa_enabled_pct=round(float(users["two_factor_enabled"].mean()) * 100, 1),
        force_reset_count=int(users["force_password_reset"].sum()),
        api_error_rate_24h=round(errors_24h / requests_24h * 100, 2) if requests_24h else 0.0,
        tokens_never_used=int(tokens["last_used_at"].isna().sum()),
    )
