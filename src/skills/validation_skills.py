
import math
import re


def validate_demand_result(data):
    """Check numerical consistency and uncertainty."""

    issues = []
    status = data.get("status")

    if status == "insufficient_evidence":
        if data.get("estimated_lost_demand") is not None:
            issues.append(
                "Unsupported estimate despite insufficient evidence."
            )
        return issues

    if status != "success":
        return issues

    recorded = data["recorded_sales"]
    lost = data["estimated_lost_demand"]
    total = data["estimated_total_demand"]

    if lost < 0:
        issues.append("Lost demand cannot be negative.")

    if not math.isclose(
        recorded + lost, total,
        rel_tol=0, abs_tol=0.0001
    ):
        issues.append("Estimated total demand is inconsistent.")

    hourly = data["hourly_estimates"]

    hourly_total = sum(
        item["estimated_lost_demand"]
        for item in hourly
    )

    if not math.isclose(
        hourly_total, lost,
        rel_tol=0, abs_tol=0.0001
    ):
        issues.append("Hourly estimates do not match total lost demand.")

    for item in hourly:
        if item["comparable_observations"] < 3:
            issues.append(
                f"Insufficient observations at hour {item['hour']}."
            )

    return issues



def validate_citations(analysis, sources):
    """Validate individual and grouped citations."""

    issues = []

    valid_ids = {
        source["citation_id"]
        for source in sources
    }

    citation_groups = re.findall(
        r"\[(S\d+(?:\s*,\s*S\d+)*)\]",
        analysis
    )

    cited_ids = {
        citation
        for group in citation_groups
        for citation in re.findall(r"S\d+", group)
    }

    if sources and not cited_ids:
        issues.append("No source citations found.")

    invalid_ids = cited_ids - valid_ids

    for citation in sorted(invalid_ids):
        issues.append(f"Unknown citation: {citation}")

    return issues
