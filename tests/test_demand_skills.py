
import pytest

from src.skills.retail_skills import (
    load_retail_data,
    detect_stockout
)

from src.skills.demand_skills import estimate_hidden_demand


@pytest.fixture(scope="module")
def retail_data():
    return load_retail_data()


def test_stockout_detection(retail_data):

    result = detect_stockout(
        retail_data, 1, 793, "2024-06-25"
    )

    assert result["status"] == "success"
    assert result["stockout_detected"] is True
    assert result["total_stockout_hours"] == 6
    assert result["daytime_stockout_hours"] == 4


def test_successful_demand_estimation(retail_data):

    result = estimate_hidden_demand(
        retail_data, 1, 793, "2024-06-25"
    )

    assert result["status"] == "success"

    assert result["recorded_sales"] == pytest.approx(1.2)

    assert result["estimated_lost_demand"] == pytest.approx(
        0.2667
    )

    assert result["estimated_total_demand"] == pytest.approx(
        1.4667
    )


def test_insufficient_evidence(retail_data):

    result = estimate_hidden_demand(
        retail_data, 0, 72, "2024-06-25"
    )

    assert result["status"] == "insufficient_evidence"
    assert result["estimated_lost_demand"] is None


def test_unknown_product(retail_data):

    result = detect_stockout(
        retail_data, 1, -999, "2024-06-25"
    )

    assert result["status"] == "not_found"


def test_estimation_scope(retail_data):

    result = estimate_hidden_demand(
        retail_data, 1, 793, "2024-06-25"
    )

    scope = result["estimation_scope"]

    assert scope["included_stockout_hours"] == [
        18, 19, 20, 21
    ]

    assert scope["excluded_stockout_hours"] == [
        22, 23
    ]


def test_missing_date(retail_data):

    result = detect_stockout(
        retail_data, 1, 793, "2000-01-01"
    )

    assert result["status"] == "not_found"
