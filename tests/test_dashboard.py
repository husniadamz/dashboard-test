from fastapi.testclient import TestClient
import pandas as pd

from app.data import get_kpi_cards, load_monthly_metrics, load_region_metrics
from app.main import app
from app.user_data import get_user_monitor_summary, load_users

client = TestClient(app)


def test_monthly_metrics_has_12_months_and_expected_columns():
    df = load_monthly_metrics()
    assert len(df) == 12
    assert {"month", "revenue", "orders", "new_customers", "churn_rate", "nps"} <= set(df.columns)


def test_region_metrics_has_one_row_per_region():
    df = load_region_metrics()
    assert len(df) == 5
    assert (df["target"] > 0).all()


def test_kpi_cards_status_thresholds():
    cards = get_kpi_cards()
    assert [c.name for c in cards] == ["Revenue", "Orders", "New customers", "Churn rate", "NPS"]
    for card in cards:
        assert card.status in {"on-track", "at-risk", "off-track"}


def test_card_change_handles_zero_previous():
    from app.data import KpiCard

    assert KpiCard("x", 10, 10, "", 0).change_pct == 0.0


def test_lower_is_better_metric_attainment_and_status():
    from app.data import KpiCard

    churn = KpiCard("Churn", 2.0, 3.5, "%", 2.5, higher_is_better=False)
    assert churn.attainment > 100
    assert churn.status == "on-track"
    assert churn.is_good_change  # churn fell vs prior month


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_api_kpis():
    response = client.get("/api/kpis")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert {"name", "value", "target", "unit", "attainment_pct", "change_pct", "status"} <= set(body[0])


def test_dashboard_page_renders_cards_and_charts():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "PACED" in html
    assert "Price, Admission &amp; Clinical Electronic Datahub" in html
    assert html.count('class="card ') == 5
    assert html.count('class="panel"') == 4
    assert "plotly-graph-div" in html


def test_user_status_counts_are_consistent():
    users = load_users()
    assert set(users["status"]) <= {"active", "dormant", "inactive"}
    summary = get_user_monitor_summary()
    assert summary.total_users == len(users)
    assert summary.active_users_7d + summary.dormant_users + summary.inactive_users == summary.total_users


def test_users_come_from_casemix_without_secrets():
    users = load_users()
    assert not {"password", "remember_token"} & set(users.columns)
    assert len(users) > 0


def test_api_users_summary():
    body = client.get("/api/users/summary").json()
    assert body["total_users"] == len(load_users())
    assert 0 <= body["twofa_enabled_pct"] <= 100
    assert "active_sessions" not in body


def test_users_page_renders():
    response = client.get("/users")
    assert response.status_code == 200
    html = response.text
    assert "User Monitor" in html
    assert html.count('class="card ') == 4
    assert html.count("plotly-graph-div") == 3
    assert "Live data · casemix" in html
    assert "Sample data" not in html
