from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SymptomIntakeRequest(BaseModel):
    symptom_text: str = Field(min_length=3)
    patient_age_group: str = "unknown"
    language: str = "unknown"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []


class FinalizeAssessmentRequest(BaseModel):
    history: list[ChatMessage]
    patient_age_group: str = "unknown"


class AccountLoginRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=1)


class AccountRegisterRequest(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=1)
    full_name: str = Field(min_length=2)
    date_of_birth: str | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    blood_type: str | None = None
    insurance_number: str | None = None
    allergies: str | None = None
    medical_antecedents: str | None = None
    phone_number: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    address: str | None = None


class ReservationRequest(BaseModel):
    intake_session_id: str
    facility_id: str
    arrival_window_start: str
    arrival_window_end: str
    notification_preference: str = "none"
    channel_type: str | None = None
    contact_value: str | None = None


class StaffQuestionRequest(BaseModel):
    question: str = Field(min_length=3)


class ApiEnvelope(BaseModel):
    ok: bool = True
    data: Any
