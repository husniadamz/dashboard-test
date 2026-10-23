"""User-system monitoring data provider.

Every figure is read live from the `casemix` database (`users` joined to `user_2fa`).
No sample data is used.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.db import read_sql

ACTIVE_USER_WINDOW = pd.Timedelta(days=7)
DORMANT_USER_WINDOW = pd.Timedelta(days=30)


@dataclass(frozen=True)
class UserMonitorSummary:
    total_users: int
    active_users_7d: int
    dormant_users: int
    inactive_users: int
    logins_24h: int
    twofa_enabled_pct: float
    force_reset_count: int


def _status(last_login: pd.Timestamp, now: pd.Timestamp) -> str:
    if pd.isna(last_login):
        return "inactive"
    age = now - last_login
    if age <= ACTIVE_USER_WINDOW:
        return "active"
    if age <= DORMANT_USER_WINDOW:
        return "dormant"
    return "inactive"


def _as_datetime(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        df[col] = pd.to_datetime(df[col])
    return df


def load_users() -> pd.DataFrame:
    """One row per live user account, read from casemix.users.

    The password hash and remember token are never selected. 2FA state comes from
    user_2fa; soft-deleted accounts (deleted_at set) are excluded.
    """
    df = read_sql(
        "SELECT u.id AS user_id, u.name, u.email, u.group_code, u.provider_id, u.last_login_at, "
        "u.force_password_reset, COALESCE(f.enabled, 0) AS two_factor_enabled "
        "FROM users u LEFT JOIN user_2fa f ON f.user_id = u.id "
        "WHERE u.deleted_at IS NULL ORDER BY u.id"
    )
    df = _as_datetime(df, ["last_login_at"])
    now = pd.Timestamp.now()
    df["two_factor_enabled"] = df["two_factor_enabled"].astype(bool)
    df["force_password_reset"] = df["force_password_reset"].astype(bool)
    df["status"] = [_status(ts, now) for ts in df["last_login_at"]]
    df["provider_id"] = df["provider_id"].map(lambda v: "" if pd.isna(v) else str(int(v)))
    df["last_login_label"] = df["last_login_at"].map(
        lambda ts: "Never" if pd.isna(ts) else ts.strftime("%Y-%m-%d %H:%M")
    )
    return df


def get_user_monitor_summary() -> UserMonitorSummary:
    users = load_users()
    now = pd.Timestamp.now()

    return UserMonitorSummary(
        total_users=len(users),
        active_users_7d=int((users["status"] == "active").sum()),
        dormant_users=int((users["status"] == "dormant").sum()),
        inactive_users=int((users["status"] == "inactive").sum()),
        logins_24h=int((users["last_login_at"] >= now - pd.Timedelta(hours=24)).sum()),
        twofa_enabled_pct=round(float(users["two_factor_enabled"].mean()) * 100, 1),
        force_reset_count=int(users["force_password_reset"].sum()),
    )
