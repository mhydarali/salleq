from __future__ import annotations

from contextlib import closing
from typing import Any

from databricks import sql
from databricks.sdk.core import Config

from src.utils.config import settings


def warehouse_http_path() -> str:
    return f"/sql/1.0/warehouses/{settings.warehouse_id}"


def _bare_hostname() -> str:
    """Return the workspace hostname without protocol prefix."""
    cfg = Config()
    host = cfg.host.rstrip("/")
    host = host.replace("https://", "").replace("http://", "")
    return host


def get_app_connection():
    cfg = Config()
    token = cfg.authenticate().get("Authorization", "").replace("Bearer ", "")
    return sql.connect(
        server_hostname=_bare_hostname(),
        http_path=warehouse_http_path(),
        access_token=token,
    )


def get_user_connection(user_token: str):
    return sql.connect(
        server_hostname=_bare_hostname(),
        http_path=warehouse_http_path(),
        access_token=user_token,
    )


def query_rows(statement: str, user_token: str | None = None) -> list[dict[str, Any]]:
    connection = get_user_connection(user_token) if user_token else get_app_connection()
    with closing(connection) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(statement)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in rows]


def execute_statement(statement: str, user_token: str | None = None) -> None:
    connection = get_user_connection(user_token) if user_token else get_app_connection()
    with closing(connection) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(statement)
