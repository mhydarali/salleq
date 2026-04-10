from __future__ import annotations

import json
from typing import Any

import requests
from databricks.sdk.core import Config


def _endpoint_url(endpoint_name: str) -> str:
    cfg = Config()
    host = cfg.host.rstrip("/")
    if not host.startswith("https://") and not host.startswith("http://"):
        host = f"https://{host}"
    return f"{host}/serving-endpoints/{endpoint_name}/invocations"


def _auth_headers() -> dict[str, str]:
    cfg = Config()
    headers = cfg.authenticate()
    headers["Content-Type"] = "application/json"
    return headers


def invoke_responses_agent(
    endpoint_name: str,
    message: str,
    *,
    custom_inputs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "input": [{"role": "user", "content": message}],
    }
    if custom_inputs:
        payload["custom_inputs"] = custom_inputs
    if metadata:
        payload["metadata"] = metadata

    response = requests.post(_endpoint_url(endpoint_name), headers=_auth_headers(), json=payload, timeout=90)
    response.raise_for_status()
    body = response.json()

    # Responses API returns output directly (not wrapped in predictions)
    output = body.get("output", [])
    content = ""
    if output:
        texts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            # Handle message items
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                        texts.append(str(part.get("text", "")))
            # Handle legacy flat content
            raw_content = item.get("content")
            if isinstance(raw_content, str):
                texts.append(raw_content)
        content = "\n".join(part for part in texts if part)
    return {"raw": body, "content": content, "output": output}


def invoke_json_agent(
    endpoint_name: str,
    message: str,
    *,
    custom_inputs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = invoke_responses_agent(endpoint_name, message, custom_inputs=custom_inputs, metadata=metadata)
    content = response["content"].strip()
    try:
        response["json"] = json.loads(content)
    except json.JSONDecodeError:
        response["json"] = None
    return response


def invoke_chat_agent(
    endpoint_name: str,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    """Send multi-turn conversation history to the MAS endpoint."""
    payload: dict[str, Any] = {"input": messages}
    response = requests.post(_endpoint_url(endpoint_name), headers=_auth_headers(), json=payload, timeout=120)
    response.raise_for_status()
    body = response.json()

    output = body.get("output", [])
    # Extract the last assistant message text
    content = ""
    for item in reversed(output):
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message" and item.get("role") == "assistant":
            for part in item.get("content", []):
                if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                    text = str(part.get("text", "")).strip()
                    if text and not text.startswith("<name>"):
                        content = text
                        break
            if content:
                break
    return {"raw": body, "content": content, "output": output}
