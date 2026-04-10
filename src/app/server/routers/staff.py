from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from src.app.server.models.api import StaffQuestionRequest
from src.app.server.services.auth import get_current_user, get_user_access_token
from src.app.server.services.staff_ops import answer_staff_ops_question, get_staff_facility_detail, get_staff_summary

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/summary")
async def staff_summary(request: Request):
    token = get_user_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="User access token not available for scoped staff queries.")
    payload = await asyncio.to_thread(get_staff_summary, token)
    user_name = await get_current_user(request)
    return {"ok": True, "data": {"user": user_name, "rows": payload}}


@router.get("/facility/{facility_id}")
async def facility_detail(facility_id: str, request: Request):
    token = get_user_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="User access token not available for scoped staff queries.")
    payload = await asyncio.to_thread(get_staff_facility_detail, token, facility_id)
    return {"ok": True, "data": payload}


@router.post("/assistant")
async def staff_assistant(request: Request, body: StaffQuestionRequest):
    token = get_user_access_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="User access token not available for scoped staff queries.")
    payload = await asyncio.to_thread(answer_staff_ops_question, token, body.question)
    return {"ok": True, "data": payload}
