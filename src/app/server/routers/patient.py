from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

from src.app.server.models.api import (
    AccountLoginRequest,
    AccountRegisterRequest,
    ChatRequest,
    FinalizeAssessmentRequest,
    ReservationRequest,
    SymptomIntakeRequest,
)
from src.app.server.services.auth import get_user_access_token
from src.app.server.services.patient_accounts import login_patient_account, register_patient_account
from src.app.server.services.patient_flow import (
    analyze_and_store_intake,
    chat_with_mas_agent,
    finalize_and_store_intake,
    get_recommendations,
    reserve_queue,
    track_queue,
)

router = APIRouter(prefix="/patient", tags=["patient"])


@router.post("/login")
async def login_account(payload: AccountLoginRequest, request: Request):
    try:
        result = await asyncio.to_thread(login_patient_account, payload.email, payload.password, get_user_access_token(request))
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/register")
async def register_account(payload: AccountRegisterRequest, request: Request):
    try:
        result = await asyncio.to_thread(register_patient_account, payload.model_dump(), get_user_access_token(request))
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat")
async def chat_with_agent(payload: ChatRequest):
    try:
        result = await asyncio.to_thread(
            chat_with_mas_agent,
            payload.message,
            [m.model_dump() for m in payload.history],
        )
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/finalize-assessment")
async def finalize_assessment(payload: FinalizeAssessmentRequest):
    try:
        result = await asyncio.to_thread(
            finalize_and_store_intake,
            [m.model_dump() for m in payload.history],
            payload.patient_age_group,
        )
        return {"ok": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/intake")
async def submit_intake(request: SymptomIntakeRequest):
    try:
        payload = await asyncio.to_thread(analyze_and_store_intake, request.symptom_text, request.patient_age_group)
        return {"ok": True, "data": payload}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/recommendations/{intake_session_id}")
async def recommendations(
    intake_session_id: str,
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
):
    try:
        payload = await asyncio.to_thread(get_recommendations, intake_session_id, latitude, longitude)
        return {"ok": True, "data": payload}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reserve")
async def create_reservation(request: ReservationRequest):
    try:
        payload = await asyncio.to_thread(
            reserve_queue,
            request.intake_session_id,
            request.facility_id,
            request.arrival_window_start,
            request.arrival_window_end,
            request.notification_preference,
            request.channel_type,
            request.contact_value,
        )
        return {"ok": True, "data": payload}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/track/{queue_id}")
async def queue_tracking(
    queue_id: str,
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
):
    try:
        payload = await asyncio.to_thread(track_queue, queue_id, latitude, longitude)
        return {"ok": True, "data": payload}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
