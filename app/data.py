"""KPI data provider.

Currently serves deterministic sample data so the dashboard works without a
database. When a database is added, replace the body of `load_monthly_metrics`
and `load_region_metrics` (keep the return shapes) and nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REGIONS = ["North", "South", "East", "West", "Central"]


@dataclass(frozen=True)
class KpiCard:
    name: str
    value: float
    target: float
    unit: str
    previous: float
    higher_is_better: bool = True

    @property
    def attainment(self) -> float:
        if not self.target or not self.value:
            return 0.0
        ratio = self.value / self.target if self.higher_is_better else self.target / self.value
        return ratio * 100

    @property
    def change_pct(self) -> float:
        if not self.previous:
            return 0.0
        return (self.value - self.previous) / self.previous * 100

    @property
    def is_good_change(self) -> bool:
        if self.change_pct == 0:
            return True
        return (self.change_pct > 0) == self.higher_is_better

    @property
    def status(self) -> str:
        if self.attainment >= 100:
            return "on-track"
        if self.attainment >= 90:
            return "at-risk"
        return "off-track"


def load_monthly_metrics() -> pd.DataFrame:
    """One row per month for the last 12 months."""
    months = pd.period_range(end=pd.Timestamp("2026-09-01"), periods=12, freq="M")
    idx = range(len(months))
    return pd.DataFrame(
        {
            "month": [str(m) for m in months],
            "revenue": [120_000 + 6_500 * i + (i % 3) * 4_000 for i in idx],
            "orders": [1_100 + 45 * i + (i % 4) * 30 for i in idx],
            "new_customers": [240 + 12 * i + (i % 2) * 15 for i in idx],
            "churn_rate": [4.8 - 0.25 * i + (0.3 if i % 5 == 0 else 0.0) for i in idx],
            "nps": [31 + 1.5 * i - (2 if i % 4 == 3 else 0) for i in idx],
        }
    )


def load_region_metrics() -> pd.DataFrame:
    """Latest-month revenue and target per region (regions sum to the latest month's revenue)."""
    revenue = [62_000, 41_500, 47_000, 24_000, 25_000]
    target = [60_000, 45_000, 48_000, 26_000, 27_000]
    return pd.DataFrame({"region": REGIONS, "revenue": revenue, "target": target})


def get_kpi_cards() -> list[KpiCard]:
    monthly = load_monthly_metrics()
    last, prev = monthly.iloc[-1], monthly.iloc[-2]
    regions = load_region_metrics()
    return [
        KpiCard("Revenue", float(last.revenue), float(regions.target.sum()), "$", float(prev.revenue)),
        KpiCard("Orders", float(last.orders), 1_800.0, "", float(prev.orders)),
        KpiCard("New customers", float(last.new_customers), 320.0, "", float(prev.new_customers)),
        KpiCard("Churn rate", float(last.churn_rate), 3.5, "%", float(prev.churn_rate), higher_is_better=False),
        KpiCard("NPS", float(last.nps), 40.0, "", float(prev.nps)),
    ]
