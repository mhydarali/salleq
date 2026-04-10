from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import streamlit as st

from src.app.server.services.databricks_sql import query_rows
from src.app.server.services.patient_flow import (
    analyze_and_store_intake,
    get_recommendations,
    get_knowledge_guidance,
    get_live_wait_guidance,
    reserve_queue,
    track_queue,
)
from src.app.server.services.staff_ops import get_staff_facility_detail, get_staff_summary
from src.utils.config import settings


@st.cache_data(ttl=300)
def load_demo_users() -> list[dict[str, Any]]:
    return query_rows(
        """
        SELECT email, full_name, date_of_birth, blood_type, insurance_number, allergies,
               medical_antecedents, phone_number, address
        FROM montreal_hackathon.virtual_waiting_room.users
        ORDER BY created_at DESC
        """
    )


def load_user_profile(email: str) -> dict[str, Any] | None:
    escaped = email.replace("'", "''")
    rows = query_rows(
        f"""
        SELECT email, full_name, date_of_birth, blood_type, insurance_number, allergies,
               medical_antecedents, phone_number, address
        FROM montreal_hackathon.virtual_waiting_room.users
        WHERE email = '{escaped}'
        LIMIT 1
        """
    )
    return rows[0] if rows else None


@st.cache_data(ttl=180)
def load_intake_examples() -> list[dict[str, Any]]:
    return query_rows(
        """
        SELECT intake_session_id, raw_symptom_text, patient_age_group, provisional_ctas_level,
               provisional_ctas_label, queue_eligible, emergency_stop, reasoning_summary
        FROM montreal_hackathon.salleq_symptom_routing_agent.intake_sessions_simulated
        ORDER BY created_at DESC
        LIMIT 12
        """
    )


def get_assessment_record(session_id: str) -> dict[str, Any] | None:
    escaped = session_id.replace("'", "''")
    rows = query_rows(
        f"""
        SELECT *
        FROM {settings.fq_schema}.intake_sessions
        WHERE intake_session_id = '{escaped}'
        LIMIT 1
        """
    )
    if rows:
        return rows[0]
    simulated = query_rows(
        f"""
        SELECT *
        FROM montreal_hackathon.salleq_symptom_routing_agent.intake_sessions_simulated
        WHERE intake_session_id = '{escaped}'
        LIMIT 1
        """
    )
    return simulated[0] if simulated else None


def submit_symptom_text(symptom_text: str, patient_age_group: str) -> dict[str, Any]:
    return analyze_and_store_intake(symptom_text, patient_age_group)


def get_assessment_result(session_id: str) -> dict[str, Any]:
    result = get_assessment_record(session_id)
    if not result:
        raise ValueError(f"Assessment not found for session_id={session_id}")
    return result


def get_recommended_facilities(session_id: str, latitude: float | None = None, longitude: float | None = None) -> list[dict[str, Any]]:
    return get_recommendations(session_id, latitude, longitude)


def reserve_queue_spot(
    session_id: str,
    facility_id: str,
    notification_preference: str = "sms",
    channel_type: str | None = None,
    contact_value: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=15)
    end = start + timedelta(minutes=45)
    return reserve_queue(
        intake_session_id=session_id,
        facility_id=facility_id,
        arrival_window_start=start.isoformat().replace("+00:00", "Z"),
        arrival_window_end=end.isoformat().replace("+00:00", "Z"),
        notification_preference=notification_preference,
        channel_type=channel_type,
        contact_value=contact_value,
    )


def get_queue_status(queue_id: str) -> dict[str, Any]:
    return track_queue(queue_id)


def get_staff_dashboard(user_token: str | None = None) -> list[dict[str, Any]]:
    if user_token:
        return get_staff_summary(user_token)
    return query_rows(
        f"""
        SELECT *
        FROM {settings.fq_schema}.vw_staff_dashboard_secure
        ORDER BY incoming_queue_count DESC, avg_stretcher_occupancy_pct DESC
        """
    )


def get_staff_queue_detail(facility_id: str, user_token: str | None = None) -> list[dict[str, Any]]:
    if user_token:
        return get_staff_facility_detail(user_token, facility_id)
    escaped = facility_id.replace("'", "''")
    return query_rows(
        f"""
        SELECT *
        FROM {settings.fq_schema}.vw_staff_queue_secure
        WHERE facility_id = '{escaped}'
        ORDER BY arrival_window_start ASC, queue_position ASC
        """
    )


def current_user_token() -> str | None:
    headers = getattr(st.context, "headers", {}) if hasattr(st, "context") else {}
    return headers.get("x-forwarded-access-token")


def get_assessment_guidance(symptom_text: str) -> str:
    return get_knowledge_guidance(symptom_text)


def get_live_facility_guidance(facility_name: str, city: str | None = None) -> str:
    return get_live_wait_guidance(facility_name, city)
