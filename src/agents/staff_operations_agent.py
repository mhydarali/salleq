from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from mlflow.pyfunc import ResponsesAgent
    from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse
except Exception:  # pragma: no cover
    ResponsesAgent = object  # type: ignore[assignment]
    ResponsesAgentRequest = Any  # type: ignore[assignment]
    ResponsesAgentResponse = Any  # type: ignore[assignment]


STAFF_AGENT_SYSTEM_PROMPT = """You are the SalleQ Staff Operations Agent.

You answer operational questions about incoming queue load, provisional CTAS mix,
facility congestion, and upcoming arrivals. Use only the scoped data supplied to
you by the application and never claim clinical certainty.
"""


@dataclass
class StaffAgentContext:
    question: str
    summary_rows: list[dict[str, Any]]


class StaffOperationsAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        question = self._extract_text(request)
        context_rows = list((getattr(request, "custom_inputs", {}) or {}).get("summary_rows", []))
        narrative = answer_staff_question(question, context_rows)
        return ResponsesAgentResponse(output=[{"role": "assistant", "content": narrative}])

    @staticmethod
    def _extract_text(request: ResponsesAgentRequest) -> str:
        for item in getattr(request, "input", []) or []:
            if isinstance(item, dict) and item.get("role") == "user":
                return str(item.get("content", ""))
        return ""


def answer_staff_question(question: str, summary_rows: list[dict[str, Any]]) -> str:
    if not summary_rows:
        return "No scoped facility data is available for this user."

    ordered = sorted(summary_rows, key=lambda row: row.get("incoming_queue_count", 0), reverse=True)
    highest = ordered[0]
    total_next_2h = sum(int(row.get("arrivals_next_2h", 0) or 0) for row in summary_rows)
    ctas4_5 = sum(int(row.get("ctas_4_count", 0) or 0) + int(row.get("ctas_5_count", 0) or 0) for row in summary_rows)

    if "next 2" in question.lower():
        return (
            f"Across the scoped facilities, there are {total_next_2h} arrivals expected in the next two hours. "
            f"The highest current queue pressure is at {highest.get('facility_name', 'unknown facility')} "
            f"with {highest.get('incoming_queue_count', 0)} queued arrivals."
        )
    if "low-acuity" in question.lower() or "ctas" in question.lower():
        return (
            f"The scoped facilities currently show {ctas4_5} expected low-acuity arrivals "
            f"(provisional CTAS 4-5) across the active queue."
        )
    return (
        f"Highest congestion in scope is {highest.get('facility_name', 'unknown facility')} in "
        f"{highest.get('city', 'unknown city')} with average live wait "
        f"{round(float(highest.get('avg_live_wait_minutes', 0) or 0), 1)} minutes."
    )
