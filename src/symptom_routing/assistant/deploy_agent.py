from __future__ import annotations

import json
import os

from databricks import agents


MODEL_NAME = os.environ.get(
    "REGISTERED_MODEL_NAME",
    "montreal_hackathon.salleq_symptom_routing_agent.symptom_routing_agent",
)
MODEL_VERSION = os.environ.get("MODEL_VERSION", "1")
ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", "salleq-symptom-routing-agent")


def main() -> None:
    deployment = agents.deploy(
        MODEL_NAME,
        MODEL_VERSION,
        endpoint_name=ENDPOINT_NAME,
        tags={"project": "salleq", "component": "symptom-routing-agent"},
    )
    print(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "model_version": MODEL_VERSION,
                "endpoint_name": deployment.endpoint_name,
                "query_endpoint": getattr(deployment, "query_endpoint", None),
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
