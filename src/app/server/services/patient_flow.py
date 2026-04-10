from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet

from src.app.server.services.agent_endpoints import invoke_chat_agent, invoke_json_agent
from src.app.server.services.databricks_sql import execute_statement, query_rows
from src.ranking.facility_ranker import FacilityCandidate, rank_facilities
from src.utils.config import settings
from src.utils.text import haversine_km, make_id

logger = logging.getLogger(__name__)


def _sql_string(value: str | None) -> str:
    if value is None:
        return "NULL"
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _sql_array(values: list[str]) -> str:
    if not values:
        return "CAST(array() AS ARRAY<STRING>)"
    return "array(" + ", ".join(_sql_string(value) for value in values) + ")"


def _encrypt_value(value: str) -> str:
    key = settings.encryption_key
    if not key or key.startswith("TODO_"):
        raise ValueError("APP_ENCRYPTION_KEY must be configured before storing contact data.")
    return Fernet(key.encode()).encrypt(value.encode()).decode()


_STRUCTURED_INTAKE_PROMPT = """Assess the following patient symptoms and return ONLY a valid JSON object (no markdown, no explanation, just raw JSON) with exactly these fields:

{{
  "language": "en or fr",
  "patient_age_group": "{age_group}",
  "primary_symptom": "brief description",
  "symptom_category": "category",
  "duration_hours": 0,
  "severity_indicators": [],
  "emergency_flags": [],
  "emergency_stop": false,
  "provisional_ctas_level": 1-5,
  "provisional_ctas_label": "Resuscitation|Emergent|Urgent|Less Urgent|Non-Urgent",
  "recommended_facility_type": "hospital|ambulatory|unknown",
  "recommended_urgency_band": "emergency|same_day|low_acuity|unknown",
  "queue_eligible": true or false,
  "reasoning_summary": "brief explanation"
}}

Patient symptoms: {symptom_text}
Patient age group: {age_group}

Return ONLY the JSON object, nothing else."""


_FINALIZE_PROMPT = """Based on our entire conversation above, now produce your final assessment.
Return ONLY a valid JSON object (no markdown, no explanation, just raw JSON) with exactly these fields:

{{
  "language": "en or fr",
  "patient_age_group": "{age_group}",
  "primary_symptom": "brief description",
  "symptom_category": "category",
  "duration_hours": 0,
  "severity_indicators": [],
  "emergency_flags": [],
  "emergency_stop": false,
  "provisional_ctas_level": 1-5,
  "provisional_ctas_label": "Resuscitation|Emergent|Urgent|Less Urgent|Non-Urgent",
  "recommended_facility_type": "hospital|ambulatory|unknown",
  "recommended_urgency_band": "emergency|same_day|low_acuity|unknown",
  "queue_eligible": true or false,
  "reasoning_summary": "brief explanation"
}}

Return ONLY the JSON object, nothing else."""


def _run_intake_via_endpoint(symptom_text: str, patient_age_group: str) -> dict[str, Any]:
    """Call the MAS supervisor endpoint for patient intake."""
    prompt = _STRUCTURED_INTAKE_PROMPT.format(
        symptom_text=symptom_text,
        age_group=patient_age_group,
    )
    response = invoke_json_agent(
        settings.patient_agent_endpoint,
        prompt,
    )
    result = response.get("json")
    if not isinstance(result, dict):
        # Try to extract JSON from markdown code fences
        content = response.get("content", "")
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    if not isinstance(result, dict):
        logger.error("MAS endpoint returned non-JSON content: %s", response.get("content", "")[:500])
        raise ValueError("The agent endpoint did not return valid JSON. Check endpoint logs.")
    return result


def _run_intake_local(symptom_text: str, patient_age_group: str) -> dict[str, Any]:
    """Run patient intake locally (no endpoint call)."""
    from src.agents.patient_intake_agent import run_patient_intake

    return run_patient_intake(symptom_text, patient_age_group).payload


def analyze_and_store_intake(symptom_text: str, patient_age_group: str) -> dict[str, Any]:
    if settings.patient_agent_mode == "endpoint" and settings.patient_agent_endpoint:
        logger.info("Routing intake to MAS endpoint: %s", settings.patient_agent_endpoint)
        result = _run_intake_via_endpoint(symptom_text, patient_age_group)
    else:
        result = _run_intake_local(symptom_text, patient_age_group)

    return _store_intake(result)


def _store_intake(result: dict[str, Any]) -> dict[str, Any]:
    """Persist an intake result dict and return it with session metadata."""
    intake_session_id = make_id("intake")
    now = datetime.now(timezone.utc)
    result["intake_session_id"] = intake_session_id
    result["created_at"] = now.isoformat()

    statement = f"""
    INSERT INTO {settings.fq_schema}.intake_sessions
    VALUES (
      {_sql_string(intake_session_id)},
      TIMESTAMP({_sql_string(now.strftime('%Y-%m-%d %H:%M:%S'))}),
      {_sql_string(result['language'])},
      {_sql_string(result['patient_age_group'])},
      {_sql_string(result['primary_symptom'])},
      {_sql_string(result['symptom_category'])},
      {float(result['duration_hours'])},
      {_sql_array(list(result['severity_indicators']))},
      {_sql_array(list(result['emergency_flags']))},
      {str(bool(result['emergency_stop'])).lower()},
      {int(result['provisional_ctas_level'])},
      {_sql_string(result['provisional_ctas_label'])},
      {_sql_string(result['recommended_facility_type'])},
      {_sql_string(result['recommended_urgency_band'])},
      {str(bool(result['queue_eligible'])).lower()},
      {_sql_string(result['reasoning_summary'])}
    )
    """
    execute_statement(statement)
    return result


def chat_with_mas_agent(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """Send a user message (with conversation history) to the MAS agent and return the reply."""
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})
    response = invoke_chat_agent(settings.patient_agent_endpoint, messages)
    reply = response["content"]
    updated_history = messages + [{"role": "assistant", "content": reply}]
    return {"reply": reply, "history": updated_history}


def finalize_and_store_intake(history: list[dict[str, str]], patient_age_group: str) -> dict[str, Any]:
    """Take a completed chat history, ask the agent for a structured JSON assessment, and store it."""
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    finalize_prompt = _FINALIZE_PROMPT.format(age_group=patient_age_group)
    messages.append({"role": "user", "content": finalize_prompt})

    response = invoke_chat_agent(settings.patient_agent_endpoint, messages)
    content = response["content"].strip()

    # Parse JSON from the response
    result = None
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    if not isinstance(result, dict):
        logger.error("Finalize returned non-JSON: %s", content[:500])
        raise ValueError("Could not extract a structured assessment from the conversation.")

    return _store_intake(result)


def get_recommendations(intake_session_id: str, latitude: float | None, longitude: float | None) -> list[dict[str, Any]]:
    intake_rows = query_rows(
        f"SELECT * FROM {settings.fq_schema}.intake_sessions WHERE intake_session_id = {_sql_string(intake_session_id)}"
    )
    if not intake_rows:
        raise ValueError(f"Unknown intake_session_id: {intake_session_id}")
    intake = intake_rows[0]
    ctas_level = int(intake["provisional_ctas_level"])

    facilities = query_rows(
        f"""
        SELECT
          facility_id_normalized,
          facility_name,
          odhf_facility_type,
          city,
          latitude,
          longitude,
          wait_time_non_priority_minutes,
          people_waiting,
          stretcher_occupancy_pct,
          total_people_er,
          virtual_queue_depth,
          avg_wait_room_minutes_prev_day,
          avg_stretcher_wait_minutes_prev_day
        FROM {settings.fq_schema}.vw_facility_live_joined
        WHERE is_quebec IS NULL OR is_quebec = TRUE
        """
    )
    candidates = [
        FacilityCandidate(
            facility_id_normalized=row["facility_id_normalized"],
            facility_name=row["facility_name"],
            odhf_facility_type=row.get("odhf_facility_type"),
            city=row.get("city"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            wait_time_non_priority_minutes=row.get("wait_time_non_priority_minutes"),
            people_waiting=row.get("people_waiting"),
            stretcher_occupancy_pct=row.get("stretcher_occupancy_pct"),
            total_people_er=row.get("total_people_er"),
            virtual_queue_depth=row.get("virtual_queue_depth"),
        )
        for row in facilities
    ]
    ranked = rank_facilities(candidates, ctas_level, latitude, longitude)
    ranked_lookup = {row.facility_id_normalized: row for row in ranked}

    filtered_rows: list[dict[str, Any]] = []
    for row in facilities:
        if ctas_level <= 3 and "ambul" in (row.get("odhf_facility_type") or "").lower():
            continue
        ranked_row = ranked_lookup[row["facility_id_normalized"]]
        filtered_rows.append(
            {
                **row,
                "distance_km": ranked_row.distance_km,
                "score": ranked_row.score,
                "fit_penalty": ranked_row.fit_penalty,
                "estimated_total_time_minutes": (
                    (row.get("wait_time_non_priority_minutes") or 0)
                    + int((ranked_row.distance_km or 0) * 2)
                    + int((row.get("virtual_queue_depth") or 0) * 10)
                ),
                "fit_for_ctas": "high" if ranked_row.fit_penalty <= 0.15 else "caution",
            }
        )

    return sorted(filtered_rows, key=lambda item: item["score"])[:12]


def reserve_queue(
    intake_session_id: str,
    facility_id: str,
    arrival_window_start: str,
    arrival_window_end: str,
    notification_preference: str,
    channel_type: str | None = None,
    contact_value: str | None = None,
) -> dict[str, Any]:
    queue_rows = query_rows(
        f"""
        SELECT COALESCE(MAX(queue_position), 0) + 1 AS next_position
        FROM {settings.fq_schema}.virtual_queue
        WHERE facility_id = {_sql_string(facility_id)}
          AND queue_status IN ('reserved', 'confirmed', 'called')
        """
    )
    next_position = int(queue_rows[0]["next_position"])
    queue_id = make_id("queue")
    created_at = datetime.now(timezone.utc)
    estimated_call_time = datetime.fromisoformat(arrival_window_start).replace(tzinfo=timezone.utc) + timedelta(
        minutes=next_position * 12
    )

    execute_statement(
        f"""
        INSERT INTO {settings.fq_schema}.virtual_queue
        VALUES (
          {_sql_string(queue_id)},
          {_sql_string(intake_session_id)},
          {_sql_string(facility_id)},
          TIMESTAMP({_sql_string(arrival_window_start.replace('T', ' ').replace('Z', ''))}),
          TIMESTAMP({_sql_string(arrival_window_end.replace('T', ' ').replace('Z', ''))}),
          {next_position},
          TIMESTAMP({_sql_string(estimated_call_time.strftime('%Y-%m-%d %H:%M:%S'))}),
          {_sql_string(notification_preference)},
          'reserved',
          TIMESTAMP({_sql_string(created_at.strftime('%Y-%m-%d %H:%M:%S'))})
        )
        """
    )

    if contact_value and notification_preference not in {"none", ""}:
        encrypted = _encrypt_value(contact_value)
        contact_id = make_id("contact")
        execute_statement(
            f"""
            INSERT INTO {settings.fq_schema}.contact_info
            VALUES (
              {_sql_string(contact_id)},
              {_sql_string(queue_id)},
              {_sql_string(channel_type or notification_preference)},
              {_sql_string(encrypted)},
              TIMESTAMP({_sql_string((created_at + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'))})
            )
            """
        )

    return {
        "queue_id": queue_id,
        "queue_position": next_position,
        "estimated_call_time": estimated_call_time.isoformat(),
        "queue_status": "reserved",
    }


def track_queue(queue_id: str, user_latitude: float | None = None, user_longitude: float | None = None) -> dict[str, Any]:
    rows = query_rows(
        f"""
        SELECT
          q.queue_id,
          q.queue_position,
          q.estimated_call_time,
          q.queue_status,
          q.arrival_window_start,
          q.arrival_window_end,
          f.facility_name,
          f.city,
          f.latitude,
          f.longitude
        FROM {settings.fq_schema}.virtual_queue q
        JOIN {settings.fq_schema}.facility_master f
          ON q.facility_id = f.facility_id_normalized
        WHERE q.queue_id = {_sql_string(queue_id)}
        """
    )
    if not rows:
        raise ValueError(f"Unknown queue_id: {queue_id}")
    row = rows[0]
    distance_km = haversine_km(user_latitude, user_longitude, row.get("latitude"), row.get("longitude"))
    remaining_minutes = max(
        0,
        int(
            (
                datetime.fromisoformat(str(row["estimated_call_time"]).replace("Z", "+00:00"))
                - datetime.now(timezone.utc)
            ).total_seconds()
            // 60
        ),
    )
    leave_now = distance_km is not None and remaining_minutes <= max(15, int(distance_km * 2))
    return {
        **row,
        "distance_km": distance_km,
        "remaining_minutes": remaining_minutes,
        "leave_now_recommendation": leave_now,
    }
