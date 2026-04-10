from __future__ import annotations

from src.symptom_routing.scoring.emergency_logic import is_emergent_flag, is_resuscitation_flag


CTAS_LABELS = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}


def ctas_label(level: int) -> str:
    return CTAS_LABELS.get(level, "Non-Urgent")


def assign_provisional_ctas(
    *,
    symptom_category: str,
    age_group: str,
    emergency_flags: list[str],
    severity_indicators: list[str],
    duration_hours: int,
) -> int:
    if any(is_resuscitation_flag(flag) for flag in emergency_flags):
        return 1
    if any(is_emergent_flag(flag) for flag in emergency_flags):
        return 2

    if age_group == "infant" and symptom_category in {"respiratory", "infection"}:
        return 3

    if symptom_category in {"cardiac", "neurological", "respiratory"}:
        return 3

    if "severe pain" in severity_indicators or "impaired function" in severity_indicators:
        return 3

    if "worsening" in severity_indicators and duration_hours >= 24:
        return 3

    if symptom_category in {"digestive", "infection", "injury", "immune"}:
        if "moderate pain" in severity_indicators or duration_hours >= 24:
            return 4
        return 5

    return 4


def default_facility_type(ctas_level: int, symptom_category: str) -> str:
    if ctas_level <= 3:
        return "hospital"
    if symptom_category in {"cardiac", "neurological", "respiratory"}:
        return "hospital"
    return "ambulatory"


def default_urgency_band(ctas_level: int) -> str:
    if ctas_level <= 2:
        return "emergency"
    if ctas_level == 3:
        return "same_day"
    if ctas_level in {4, 5}:
        return "low_acuity" if ctas_level == 5 else "same_day"
    return "unknown"
