"""Plotly charts for the user-system monitor."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app.user_data import load_users

PLOT_TEMPLATE = "plotly_white"
STATUS_COLORS = {"active": "#16a34a", "dormant": "#f59e0b", "inactive": "#94a3b8"}


def _html(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})


def login_activity_chart() -> str:
    """Users per day by their most recent login, for the last 14 days."""
    users = load_users()
    today = pd.Timestamp.now().normalize()
    days = pd.date_range(today - pd.Timedelta(days=13), today, freq="D")
    last = users["last_login_at"].dropna()
    per_day = last[last >= days[0]].dt.normalize().value_counts()
    counts = per_day.reindex(days, fill_value=0)
    fig = go.Figure(go.Bar(x=days, y=counts.values, name="Users", marker_color="#7c3aed"))
    fig.update_layout(
        title="Latest login per user, last 14 days",
        template=PLOT_TEMPLATE,
        margin={"l": 60, "r": 20, "t": 50, "b": 60},
        height=360,
    )
    fig.update_yaxes(title_text="Users")
    return _html(fig)


def user_status_chart() -> str:
    users = load_users()
    counts = users["status"].value_counts().reindex(["active", "dormant", "inactive"], fill_value=0)
    fig = go.Figure(
        go.Pie(
            labels=[s.title() for s in counts.index],
            values=counts.values,
            hole=0.55,
            marker={"colors": [STATUS_COLORS[s] for s in counts.index]},
            sort=False,
        )
    )
    fig.update_layout(
        title="Users by last login",
        template=PLOT_TEMPLATE,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        height=340,
    )
    return _html(fig)


def group_breakdown_chart() -> str:
    users = load_users()
    grouped = users.groupby(["group_code", "status"]).size().unstack(fill_value=0)
    grouped = grouped.reindex(columns=["active", "dormant", "inactive"], fill_value=0)
    fig = go.Figure()
    for status in grouped.columns:
        fig.add_trace(go.Bar(x=grouped.index, y=grouped[status], name=status.title(), marker_color=STATUS_COLORS[status]))
    fig.update_layout(
        title="Users by group and status",
        template=PLOT_TEMPLATE,
        barmode="stack",
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 60, "r": 20, "t": 50, "b": 60},
        height=340,
    )
    fig.update_yaxes(title_text="Users")
    return _html(fig)
