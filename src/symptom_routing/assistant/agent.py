from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

from src.symptom_routing.assistant.tools import build_routing_decision, validate_output_shape

try:
    import mlflow
    from mlflow.pyfunc import ResponsesAgent
    from mlflow.types.responses import (
        ResponsesAgentRequest,
        ResponsesAgentResponse,
        ResponsesAgentStreamEvent,
    )
except ImportError:  # pragma: no cover - local fallback for static validation
    mlflow = None

    class ResponsesAgent:  # type: ignore[override]
        def create_text_output_item(self, text: str, id: str) -> dict[str, Any]:
            return {"type": "message", "id": id, "text": text}

    class ResponsesAgentRequest(dict):
        pass

    class ResponsesAgentResponse(dict):
        def __init__(self, output: list[dict[str, Any]]):
            super().__init__(output=output)

    class ResponsesAgentStreamEvent(dict):
        def __init__(self, type: str, item: dict[str, Any]):
            super().__init__(type=type, item=item)


DEFAULT_SYSTEM_PROMPT = """You are the SalleQ symptom-routing agent.

You are not a general chatbot.
You are not a diagnostic tool.
You are not a treatment tool.
You do not replace nurse triage or clinical judgment.

Your only task is to transform symptom intake information into a strict JSON routing payload for a frontend application.

Rules:
- Never diagnose.
- Never provide treatment advice.
- Be conservative.
- If uncertain between two acuity levels, choose the higher-acuity level.
- Escalate emergencies immediately.
- Return valid JSON only.
- Never output prose, markdown, code fences, or explanations outside the JSON.
- Use CTAS only as provisional routing support.
- Honor this product statement in reasoning:
  AI-estimated provisional CTAS urgency for routing support only. Final triage is determined by clinical staff.
"""

system_prompt_path = Path(__file__).with_name("system_prompt.txt")
SYSTEM_PROMPT = system_prompt_path.read_text() if system_prompt_path.exists() else DEFAULT_SYSTEM_PROMPT


def _extract_user_message(request: Any) -> tuple[str, str | None, int | None]:
    if isinstance(request, dict):
        input_items = request.get("input", [])
        custom_inputs = request.get("custom_inputs", {}) or {}
    else:
        input_items = getattr(request, "input", [])
        custom_inputs = getattr(request, "custom_inputs", {}) or {}

    text_parts: list[str] = []
    for item in input_items:
        role = item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
        content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
        if role == "user" and content:
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        text_parts.append(part.get("text", ""))
            elif isinstance(content, str):
                text_parts.append(content)

    symptom_text = " ".join(part.strip() for part in text_parts if part).strip()
    patient_age_group = custom_inputs.get("patient_age_group")
    duration_hours = custom_inputs.get("duration_hours")
    return symptom_text, patient_age_group, duration_hours


class SymptomRoutingAgent(ResponsesAgent):
    """Deterministic routing agent wrapped in the ResponsesAgent interface."""

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        symptom_text, patient_age_group, duration_hours = _extract_user_message(request)
        if not symptom_text:
            raise ValueError("A user symptom description is required.")

        payload = build_routing_decision(
            symptom_text=symptom_text,
            patient_age_group=patient_age_group,
            explicit_duration_hours=duration_hours,
        )
        validate_output_shape(payload)
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=json.dumps(payload, ensure_ascii=False), id="routing_decision_1")]
        )

    def predict_stream(
        self, request: ResponsesAgentRequest
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        response = self.predict(request)
        output_items = response["output"] if isinstance(response, dict) else response.output
        for item in output_items:
            yield ResponsesAgentStreamEvent(type="response.output_item.done", item=item)


AGENT = SymptomRoutingAgent()

if mlflow is not None:
    mlflow.models.set_model(AGENT)
