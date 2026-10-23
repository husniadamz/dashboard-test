"""Plotly chart builders for the KPI dashboard."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.data import load_monthly_metrics, load_region_metrics

PLOT_TEMPLATE = "plotly_white"


def _html(fig: go.Figure) -> str:
    # plotly.js is loaded once from the CDN in the page template.
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displaylogo": False})


def revenue_trend_chart() -> str:
    df = load_monthly_metrics()
    fig = go.Figure(
        go.Scatter(
            x=df["month"],
            y=df["revenue"],
            mode="lines+markers",
            name="Revenue",
            line={"color": "#7c3aed", "width": 3},
        )
    )
    fig.update_layout(
        title="Monthly revenue",
        template=PLOT_TEMPLATE,
        yaxis_title="Revenue ($)",
        margin={"l": 60, "r": 20, "t": 50, "b": 40},
        height=340,
    )
    return _html(fig)


def orders_and_customers_chart() -> str:
    df = load_monthly_metrics()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["month"], y=df["orders"], name="Orders", marker_color="#f0abfc"), secondary_y=False)
    fig.add_trace(
        go.Scatter(x=df["month"], y=df["new_customers"], name="New customers", mode="lines+markers", line={"color": "#ec4899"}),
        secondary_y=True,
    )
    fig.update_layout(
        title="Orders & new customers",
        template=PLOT_TEMPLATE,
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 60, "r": 60, "t": 50, "b": 60},
        height=340,
    )
    fig.update_yaxes(title_text="Orders", secondary_y=False)
    fig.update_yaxes(title_text="New customers", secondary_y=True)
    return _html(fig)


def churn_nps_chart() -> str:
    df = load_monthly_metrics()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df["month"], y=df["churn_rate"], name="Churn rate (%)", mode="lines+markers", line={"color": "#e11d48"}),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=df["month"], y=df["nps"], name="NPS", mode="lines+markers", line={"color": "#c026d3"}),
        secondary_y=True,
    )
    fig.update_layout(
        title="Churn rate & NPS",
        template=PLOT_TEMPLATE,
        legend={"orientation": "h", "y": -0.2},
        margin={"l": 60, "r": 60, "t": 50, "b": 60},
        height=340,
    )
    fig.update_yaxes(title_text="Churn (%)", secondary_y=False)
    fig.update_yaxes(title_text="NPS", secondary_y=True)
    return _html(fig)


def region_attainment_chart() -> str:
    df = load_region_metrics()
    df = df.assign(attainment=df["revenue"] / df["target"] * 100)
    colors = ["#16a34a" if a >= 100 else "#f59e0b" if a >= 90 else "#dc2626" for a in df["attainment"]]
    fig = go.Figure(
        go.Bar(
            x=df["region"],
            y=df["attainment"],
            marker_color=colors,
            text=[f"{a:.1f}%" for a in df["attainment"]],
            textposition="outside",
            name="Target attainment",
        )
    )
    fig.add_hline(y=100, line_dash="dash", line_color="#334155", annotation_text="Target")
    fig.update_layout(
        title="Revenue vs target by region",
        template=PLOT_TEMPLATE,
        yaxis_title="Attainment (%)",
        margin={"l": 60, "r": 20, "t": 50, "b": 40},
        height=340,
        showlegend=False,
    )
    return _html(fig)
