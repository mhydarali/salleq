from __future__ import annotations

from src.symptom_routing.scoring.ctas_logic import default_facility_type, default_urgency_band


CTAS_COMPONENT = {
    1: 100,
    2: 85,
    3: 60,
    4: 30,
    5: 10,
}

VULNERABILITY_COMPONENT = {
    "adult": 0,
    "child": 10,
    "infant": 20,
    "older_adult": 15,
    "unknown": 5,
}


def severity_component(severity_indicators: list[str]) -> int:
    if "severe pain" in severity_indicators or "impaired function" in severity_indicators:
        return 30
    if "worsening" in severity_indicators:
        return 20
    if "moderate pain" in severity_indicators:
        return 10
    return 0


def duration_component(duration_hours: int, severity_indicators: list[str]) -> int:
    if duration_hours <= 0 or duration_hours < 12:
        return 0
    if duration_hours < 24:
        return 5
    if duration_hours > 24 and "worsening" in severity_indicators:
        return 10
    if duration_hours >= 72:
        return 15
    return 5


def risk_band_from_score(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def calculate_risk_score(
    *,
    ctas_level: int,
    red_flag_component_value: int,
    age_group: str,
    severity_indicators: list[str],
    duration_hours: int,
    emergency_stop: bool,
) -> tuple[int, str]:
    if emergency_stop:
        return 100, "critical"
    if ctas_level == 1:
        return 100, "critical"

    computed = round(
        0.45 * CTAS_COMPONENT[ctas_level]
        + 0.30 * red_flag_component_value
        + 0.10 * VULNERABILITY_COMPONENT.get(age_group, 5)
        + 0.10 * severity_component(severity_indicators)
        + 0.05 * duration_component(duration_hours, severity_indicators)
    )

    if ctas_level == 2:
        computed = max(computed, 85)

    computed = max(0, min(100, computed))
    return computed, risk_band_from_score(computed)


def determine_queue_eligibility(
    *,
    ctas_level: int,
    risk_band: str,
    emergency_stop: bool,
    symptom_category: str,
) -> tuple[bool, str, str]:
    if emergency_stop:
        return False, "hospital", "emergency"

    if ctas_level <= 3:
        return False, "hospital", default_urgency_band(ctas_level)

    if risk_band == "critical":
        return False, "hospital", "emergency"

    if risk_band == "high":
        return False, "hospital", "same_day"

    if risk_band == "moderate":
        facility_type = "ambulatory" if ctas_level == 5 and symptom_category not in {"cardiac", "neurological", "respiratory"} else "hospital"
        queue_eligible = facility_type == "ambulatory"
        urgency_band = "low_acuity" if queue_eligible else "same_day"
        return queue_eligible, facility_type, urgency_band

    return True, default_facility_type(ctas_level, symptom_category), default_urgency_band(ctas_level)
