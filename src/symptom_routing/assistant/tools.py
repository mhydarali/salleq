from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.symptom_routing.scoring.ctas_logic import assign_provisional_ctas, ctas_label
from src.symptom_routing.scoring.emergency_logic import detect_emergency_flags, red_flag_component
from src.symptom_routing.scoring.risk_score import calculate_risk_score, determine_queue_eligibility
from src.symptom_routing.utils.parsing import (
    coerce_age_group,
    detect_language,
    extract_severity_indicators,
    infer_primary_symptom,
    infer_symptom_category,
    parse_duration_hours,
)

DISCLAIMER = "AI-estimated provisional CTAS urgency for routing support only. Final triage is determined by clinical staff."
EXPECTED_KEYS = (
    "language",
    "patient_age_group",
    "primary_symptom",
    "symptom_category",
    "duration_hours",
    "severity_indicators",
    "emergency_flags",
    "emergency_stop",
    "provisional_ctas_level",
    "provisional_ctas_label",
    "recommended_facility_type",
    "recommended_urgency_band",
    "queue_eligible",
    "risk_score",
    "risk_band",
    "reasoning_summary",
)
DEFAULT_OUTPUT_SCHEMA: dict[str, Any] = {
    "properties": {
        "language": {"enum": ["en", "fr", "unknown"]},
        "patient_age_group": {"enum": ["infant", "child", "adult", "older_adult", "unknown"]},
        "symptom_category": {"enum": ["infection", "injury", "respiratory", "cardiac", "neurological", "digestive", "immune", "other"]},
        "provisional_ctas_level": {"enum": [1, 2, 3, 4, 5]},
        "provisional_ctas_label": {"enum": ["Resuscitation", "Emergent", "Urgent", "Less Urgent", "Non-Urgent"]},
        "recommended_facility_type": {"enum": ["hospital", "ambulatory", "unknown"]},
        "recommended_urgency_band": {"enum": ["emergency", "same_day", "low_acuity", "unknown"]},
        "risk_band": {"enum": ["low", "moderate", "high", "critical"]},
    }
}


def load_output_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("output_schema.json")
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return DEFAULT_OUTPUT_SCHEMA


def validate_output_shape(payload: dict[str, Any]) -> None:
    schema = load_output_schema()["properties"]
    missing = [key for key in EXPECTED_KEYS if key not in payload]
    extra = [key for key in payload if key not in EXPECTED_KEYS]
    if missing or extra:
        raise ValueError(f"Output schema mismatch. Missing={missing} extra={extra}")

    for key in ("language", "patient_age_group", "symptom_category", "provisional_ctas_label", "recommended_facility_type", "recommended_urgency_band", "risk_band"):
        allowed = schema[key].get("enum", [])
        if payload[key] not in allowed:
            raise ValueError(f"Unexpected enum value for {key}: {payload[key]}")

    if payload["provisional_ctas_level"] not in schema["provisional_ctas_level"]["enum"]:
        raise ValueError("Unexpected provisional_ctas_level")

    if not isinstance(payload["duration_hours"], int) or payload["duration_hours"] < 0:
        raise ValueError("duration_hours must be a non-negative integer")

    if not isinstance(payload["risk_score"], int) or not 0 <= payload["risk_score"] <= 100:
        raise ValueError("risk_score must be an integer between 0 and 100")


def check_emergency_flags(symptom_text: str, patient_age_group: str | None = None) -> list[str]:
    return detect_emergency_flags(symptom_text, coerce_age_group(patient_age_group))


def assign_provisional_ctas_level(
    symptom_text: str,
    patient_age_group: str | None = None,
    duration_hours: int | None = None,
) -> tuple[int, str]:
    age_group = coerce_age_group(patient_age_group)
    derived_duration = parse_duration_hours(symptom_text, duration_hours)
    severity_indicators = extract_severity_indicators(symptom_text)
    emergency_flags = detect_emergency_flags(symptom_text, age_group)
    symptom_category = infer_symptom_category(symptom_text)
    level = assign_provisional_ctas(
        symptom_category=symptom_category,
        age_group=age_group,
        emergency_flags=emergency_flags,
        severity_indicators=severity_indicators,
        duration_hours=derived_duration,
    )
    return level, ctas_label(level)


def calculate_routing_risk(
    symptom_text: str,
    patient_age_group: str | None = None,
    duration_hours: int | None = None,
) -> tuple[int, str]:
    age_group = coerce_age_group(patient_age_group)
    derived_duration = parse_duration_hours(symptom_text, duration_hours)
    emergency_flags = detect_emergency_flags(symptom_text, age_group)
    severity_indicators = extract_severity_indicators(symptom_text)
    symptom_category = infer_symptom_category(symptom_text)
    provisional_ctas_level = assign_provisional_ctas(
        symptom_category=symptom_category,
        age_group=age_group,
        emergency_flags=emergency_flags,
        severity_indicators=severity_indicators,
        duration_hours=derived_duration,
    )
    emergency_stop = bool(emergency_flags) or provisional_ctas_level in {1, 2}
    return calculate_risk_score(
        ctas_level=provisional_ctas_level,
        red_flag_component_value=red_flag_component(symptom_text, emergency_flags),
        age_group=age_group,
        severity_indicators=severity_indicators,
        duration_hours=derived_duration,
        emergency_stop=emergency_stop,
    )


def determine_queue_policy(
    symptom_text: str,
    patient_age_group: str | None = None,
    duration_hours: int | None = None,
) -> tuple[bool, str, str]:
    age_group = coerce_age_group(patient_age_group)
    derived_duration = parse_duration_hours(symptom_text, duration_hours)
    severity_indicators = extract_severity_indicators(symptom_text)
    emergency_flags = detect_emergency_flags(symptom_text, age_group)
    symptom_category = infer_symptom_category(symptom_text)
    provisional_ctas_level = assign_provisional_ctas(
        symptom_category=symptom_category,
        age_group=age_group,
        emergency_flags=emergency_flags,
        severity_indicators=severity_indicators,
        duration_hours=derived_duration,
    )
    emergency_stop = bool(emergency_flags) or provisional_ctas_level in {1, 2}
    risk_score, risk_band = calculate_risk_score(
        ctas_level=provisional_ctas_level,
        red_flag_component_value=red_flag_component(symptom_text, emergency_flags),
        age_group=age_group,
        severity_indicators=severity_indicators,
        duration_hours=derived_duration,
        emergency_stop=emergency_stop,
    )
    if risk_band == "critical":
        emergency_stop = True
        risk_score = 100
        risk_band = "critical"
    return determine_queue_eligibility(
        ctas_level=provisional_ctas_level,
        risk_band=risk_band,
        emergency_stop=emergency_stop,
        symptom_category=symptom_category,
    )


def build_routing_decision(
    symptom_text: str,
    patient_age_group: str | None = None,
    explicit_duration_hours: int | None = None,
) -> dict[str, Any]:
    language = detect_language(symptom_text)
    normalized_age_group = coerce_age_group(patient_age_group)
    duration_hours = parse_duration_hours(symptom_text, explicit_duration_hours)
    primary_symptom = infer_primary_symptom(symptom_text)
    symptom_category = infer_symptom_category(symptom_text)
    severity_indicators = extract_severity_indicators(symptom_text)
    emergency_flags = detect_emergency_flags(symptom_text, normalized_age_group)
    provisional_ctas_level = assign_provisional_ctas(
        symptom_category=symptom_category,
        age_group=normalized_age_group,
        emergency_flags=emergency_flags,
        severity_indicators=severity_indicators,
        duration_hours=duration_hours,
    )
    provisional_ctas_label = ctas_label(provisional_ctas_level)
    emergency_stop = bool(emergency_flags) or provisional_ctas_level in {1, 2}
    risk_score, risk_band = calculate_risk_score(
        ctas_level=provisional_ctas_level,
        red_flag_component_value=red_flag_component(symptom_text, emergency_flags),
        age_group=normalized_age_group,
        severity_indicators=severity_indicators,
        duration_hours=duration_hours,
        emergency_stop=emergency_stop,
    )

    if risk_band == "critical":
        emergency_stop = True
        risk_score = 100
        risk_band = "critical"

    queue_eligible, facility_type, urgency_band = determine_queue_eligibility(
        ctas_level=provisional_ctas_level,
        risk_band=risk_band,
        emergency_stop=emergency_stop,
        symptom_category=symptom_category,
    )

    if emergency_stop:
        facility_type = "hospital"
        urgency_band = "emergency"
        queue_eligible = False
        risk_score = 100
        risk_band = "critical"

    reasoning_parts = [
        f"Primary symptom: {primary_symptom}.",
        f"Provisional CTAS {provisional_ctas_level} ({provisional_ctas_label}).",
    ]
    if emergency_flags:
        reasoning_parts.append(f"Emergency flags detected: {', '.join(emergency_flags)}.")
    elif risk_band in {"high", "moderate"}:
        reasoning_parts.append(f"Risk band is {risk_band}, so lower-acuity routing is limited.")
    else:
        reasoning_parts.append("No hard emergency flags detected in the current description.")
    reasoning_parts.append(DISCLAIMER)

    payload = {
        "language": language,
        "patient_age_group": normalized_age_group,
        "primary_symptom": primary_symptom,
        "symptom_category": symptom_category,
        "duration_hours": duration_hours,
        "severity_indicators": severity_indicators,
        "emergency_flags": emergency_flags,
        "emergency_stop": emergency_stop,
        "provisional_ctas_level": provisional_ctas_level,
        "provisional_ctas_label": provisional_ctas_label,
        "recommended_facility_type": facility_type,
        "recommended_urgency_band": urgency_band,
        "queue_eligible": queue_eligible,
        "risk_score": risk_score,
        "risk_band": risk_band,
        "reasoning_summary": " ".join(reasoning_parts),
    }
    validate_output_shape(payload)
    return payload
