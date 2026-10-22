"""Plotly charts for the user-system monitor."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.user_data import load_hourly_activity, load_users

PLOT_TEMPLATE = "plotly_white"
STATUS_COLORS = {"active": "#16a34a", "dormant": "#f59e0b", "inactive": "#94a3b8"}


def _html(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})


def hourly_activity_chart() -> str:
    df = load_hourly_activity()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["hour"], y=df["api_requests"], name="API requests", marker_color="#93c5fd"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df["hour"], y=df["logins"], name="Logins", mode="lines+markers", line={"color": "#2563eb"}), secondary_y=True)
    fig.add_trace(go.Scatter(x=df["hour"], y=df["model_changes"], name="Record changes", mode="lines", line={"color": "#7c3aed"}), secondary_y=True)
    fig.add_trace(go.Scatter(x=df["hour"], y=df["api_errors"], name="API errors", mode="lines+markers", line={"color": "#dc2626"}), secondary_y=True)
    fig.update_layout(
        title="Activity, last 24 hours",
        template=PLOT_TEMPLATE,
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 60, "r": 60, "t": 50, "b": 60},
        height=360,
    )
    fig.update_yaxes(title_text="API requests", secondary_y=False)
    fig.update_yaxes(title_text="Logins / changes / errors", secondary_y=True)
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
