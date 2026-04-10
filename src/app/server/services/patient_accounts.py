from __future__ import annotations

import json
from typing import Any

from src.app.server.services.databricks_sql import execute_statement, query_rows
from src.utils.config import settings


def _sql_string(value: str | None) -> str:
    if value is None:
        return "NULL"
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _compact_text(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.split()).strip()
    return compact or None


def _escape_registration_text(value: str | None) -> str | None:
    compact = _compact_text(value)
    if compact is None:
        return None
    if '"' in compact or "\\" in compact:
        raise ValueError('Registration fields cannot contain double quotes or backslashes.')
    return compact.replace("'", "''")


def _run_json_scalar(statement: str, user_token: str | None = None) -> dict[str, Any]:
    rows = query_rows(statement, user_token=user_token)
    if not rows:
        raise ValueError("The account function returned no rows.")

    payload = next(iter(rows[0].values()), None)
    if not isinstance(payload, str):
        raise ValueError("The account function returned an unexpected payload.")

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("The account function returned invalid JSON.") from exc

    if not isinstance(decoded, dict):
        raise ValueError("The account function returned an invalid envelope.")
    return decoded


def login_patient_account(email: str, password: str, user_token: str | None = None) -> dict[str, Any]:
    normalized_email = _compact_text(email)
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("A valid email address is required.")
    if not password:
        raise ValueError("A password is required.")

    statement = f"""
    SELECT {settings.patient_account_schema}.login_user(
      {_sql_string(normalized_email.lower())},
      {_sql_string(password)}
    ) AS response_json
    """
    payload = _run_json_scalar(statement, user_token=user_token)
    if payload.get("status") != "success":
        raise ValueError(str(payload.get("message") or "Login failed."))
    if not isinstance(payload.get("user"), dict):
        raise ValueError("Login completed without a user profile.")
    return payload


def register_patient_account(payload: dict[str, Any], user_token: str | None = None) -> dict[str, Any]:
    email = _compact_text(str(payload.get("email") or ""))
    password = str(payload.get("password") or "")
    full_name = _escape_registration_text(payload.get("full_name"))

    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not full_name:
        raise ValueError("Full name is required.")

    height_cm = payload.get("height_cm")
    weight_kg = payload.get("weight_kg")

    statement = f"""
    SELECT {settings.patient_account_schema}.register_user(
      {_sql_string(email.lower())},
      {_sql_string(password)},
      {_sql_string(full_name)},
      {_sql_string(_escape_registration_text(payload.get("date_of_birth")))},
      {_sql_string(_escape_registration_text(payload.get("sex")))},
      {"NULL" if height_cm in (None, "") else float(height_cm)},
      {"NULL" if weight_kg in (None, "") else float(weight_kg)},
      {_sql_string(_escape_registration_text(payload.get("blood_type")))},
      {_sql_string(_escape_registration_text(payload.get("insurance_number")))},
      {_sql_string(_escape_registration_text(payload.get("allergies")))},
      {_sql_string(_escape_registration_text(payload.get("medical_antecedents")))},
      {_sql_string(_escape_registration_text(payload.get("phone_number")))},
      {_sql_string(_escape_registration_text(payload.get("emergency_contact_name")))},
      {_sql_string(_escape_registration_text(payload.get("emergency_contact_phone")))},
      {_sql_string(_escape_registration_text(payload.get("address")))}
    ) AS response_json
    """
    registration = _run_json_scalar(statement, user_token=user_token)
    if registration.get("status") != "ready":
        raise ValueError(str(registration.get("message") or "Registration failed."))

    insert_sql = registration.get("insert_sql")
    if not isinstance(insert_sql, str) or not insert_sql.strip():
        raise ValueError("Registration returned no insert statement.")

    execute_statement(insert_sql, user_token=user_token)
    logged_in = login_patient_account(email, password, user_token=user_token)
    logged_in["message"] = "Registration complete. Account created successfully."
    return logged_in
