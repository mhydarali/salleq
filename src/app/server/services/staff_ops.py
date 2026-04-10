from __future__ import annotations

from src.agents.staff_operations_agent import answer_staff_question
from src.app.server.services.databricks_sql import query_rows
from src.utils.config import settings


def get_staff_summary(user_token: str) -> list[dict[str, object]]:
    return query_rows(
        f"""
        SELECT *
        FROM {settings.fq_schema}.vw_staff_dashboard_secure
        ORDER BY incoming_queue_count DESC, avg_stretcher_occupancy_pct DESC
        """,
        user_token=user_token,
    )


def get_staff_facility_detail(user_token: str, facility_id: str) -> list[dict[str, object]]:
    return query_rows(
        f"""
        SELECT *
        FROM {settings.fq_schema}.vw_staff_queue_secure
        WHERE facility_id = '{facility_id.replace("'", "''")}'
        ORDER BY arrival_window_start ASC, queue_position ASC
        """,
        user_token=user_token,
    )


def answer_staff_ops_question(user_token: str, question: str) -> dict[str, object]:
    summary_rows = get_staff_summary(user_token)
    answer = answer_staff_question(question, summary_rows)
    return {"answer": answer, "summary_rows": summary_rows}
