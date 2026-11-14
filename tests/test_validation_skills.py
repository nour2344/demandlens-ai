
from copy import deepcopy

from src.skills.validation_skills import (
    validate_demand_result,
    validate_citations
)


VALID_RESULT = {
    "status": "success",
    "recorded_sales": 1.2,
    "estimated_lost_demand": 0.2667,
    "estimated_total_demand": 1.4667,
    "hourly_estimates": [
        {
            "hour": 19,
            "estimated_lost_demand": 0.0667,
            "comparable_observations": 3
        },
        {
            "hour": 20,
            "estimated_lost_demand": 0.1,
            "comparable_observations": 3
        },
        {
            "hour": 21,
            "estimated_lost_demand": 0.1,
            "comparable_observations": 3
        }
    ]
}


SOURCES = [
    {"citation_id": "S1"},
    {"citation_id": "S2"},
    {"citation_id": "S3"}
]


def test_valid_demand_result():

    assert validate_demand_result(VALID_RESULT) == []


def test_incorrect_total_demand():

    result = deepcopy(VALID_RESULT)
    result["estimated_total_demand"] = 9.5

    assert validate_demand_result(result) != []


def test_negative_lost_demand():

    result = deepcopy(VALID_RESULT)
    result["estimated_lost_demand"] = -0.5

    assert validate_demand_result(result) != []


def test_unsupported_estimate():

    result = {
        "status": "insufficient_evidence",
        "estimated_lost_demand": 0.5
    }

    assert validate_demand_result(result) != []


def test_valid_citation():

    assert validate_citations(
        "Stockouts affect observed sales [S1].",
        SOURCES
    ) == []


def test_grouped_citations():

    assert validate_citations(
        "Stockouts affect forecasting [S1, S2].",
        SOURCES
    ) == []


def test_invented_citation():

    assert validate_citations(
        "Stockouts affect forecasting [S9].",
        SOURCES
    ) != []


def test_invalid_grouped_citation():

    assert validate_citations(
        "Stockouts affect forecasting [S1, S9].",
        SOURCES
    ) != []


def test_missing_citations():

    assert validate_citations(
        "Stockouts affect forecasting.",
        SOURCES
    ) != []
