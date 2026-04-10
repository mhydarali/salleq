from __future__ import annotations

import logging
import os
from typing import Optional

from databricks.sdk import WorkspaceClient
from fastapi import Request

logger = logging.getLogger(__name__)


def is_local_development() -> bool:
    return os.getenv("ENV", "development") == "development"


def has_oauth_credentials() -> bool:
    return bool(os.getenv("DATABRICKS_CLIENT_ID") and os.getenv("DATABRICKS_CLIENT_SECRET"))


def get_workspace_client() -> WorkspaceClient:
    if has_oauth_credentials():
        return WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST", ""),
            client_id=os.getenv("DATABRICKS_CLIENT_ID", ""),
            client_secret=os.getenv("DATABRICKS_CLIENT_SECRET", ""),
            auth_type="oauth-m2m",
        )
    return WorkspaceClient()


async def get_current_user(request: Request) -> str:
    for header_name in ("X-Forwarded-Email", "X-Forwarded-User"):
        value = request.headers.get(header_name)
        if value:
            return value
    if is_local_development():
        me = get_workspace_client().current_user.me()
        return me.user_name or me.display_name or "local-user"
    return "unknown-user"


def get_user_access_token(request: Request) -> Optional[str]:
    token = request.headers.get("x-forwarded-access-token")
    if token:
        return token
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return os.getenv("DATABRICKS_TOKEN") if is_local_development() else None
