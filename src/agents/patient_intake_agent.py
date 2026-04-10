from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.agents.triage_rules import assess_symptoms

try:
    from mlflow.pyfunc import ResponsesAgent
    from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
except Exception:  # pragma: no cover - runtime fallback when mlflow is absent
    ResponsesAgent = object  # type: ignore[assignment]
    ResponsesAgentRequest = Any  # type: ignore[assignment]
    ResponsesAgentResponse = Any  # type: ignore[assignment]


SYSTEM_PROMPT = """You are the SalleQ Patient Intake Agent.

Return JSON only with this schema:
{
  "language": "en|fr|unknown",
  "patient_age_group": "infant|child|adult|older_adult|unknown",
  "primary_symptom": "string",
  "symptom_category": "string",
  "duration_hours": 0,
  "severity_indicators": ["string"],
  "emergency_flags": ["string"],
  "emergency_stop": false,
  "provisional_ctas_level": 1,
  "provisional_ctas_label": "Resuscitation|Emergent|Urgent|Less Urgent|Non-Urgent",
  "recommended_facility_type": "hospital|ambulatory|unknown",
  "recommended_urgency_band": "emergency|same_day|low_acuity|unknown",
  "queue_eligible": false,
  "reasoning_summary": "string"
}

Instructions:
- Be conservative.
- Prefer higher acuity when uncertain.
- Never diagnose.
- Never claim to replace clinical triage.
- Escalate emergency red flags immediately.
- Use CTAS only as provisional AI-estimated urgency support.
"""


@dataclass
class PatientIntakeResult:
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.payload, ensure_ascii=True)


class PatientIntakeAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        user_text = self._extract_text(request)
        age_group = self._extract_age_group(request)
        result = assess_symptoms(user_text, age_group)
        return ResponsesAgentResponse(output=[{"role": "assistant", "content": result.as_dict()}])

    @staticmethod
    def _extract_text(request: ResponsesAgentRequest) -> str:
        for item in getattr(request, "input", []) or []:
            if isinstance(item, dict) and item.get("role") == "user":
                content = item.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "input_text":
                            return str(part.get("text", ""))
        return ""

    @staticmethod
    def _extract_age_group(request: ResponsesAgentRequest) -> str:
        custom_inputs = getattr(request, "custom_inputs", {}) or {}
        return str(custom_inputs.get("patient_age_group", "unknown"))


def run_patient_intake(symptom_text: str, patient_age_group: str | None = None) -> PatientIntakeResult:
    result = assess_symptoms(symptom_text, patient_age_group)
    return PatientIntakeResult(payload=result.as_dict())
