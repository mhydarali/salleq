from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import mlflow


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REGISTERED_MODEL_NAME = os.environ.get(
    "REGISTERED_MODEL_NAME",
    "montreal_hackathon.salleq_symptom_routing_agent.symptom_routing_agent",
)

INPUT_EXAMPLE = {
    "input": [{"role": "user", "content": "Fever and ear pain since this morning"}],
    "custom_inputs": {"patient_age_group": "child", "duration_hours": 8},
}


def main() -> None:
    mlflow.set_registry_uri("databricks-uc")

    with mlflow.start_run():
        model_info = mlflow.pyfunc.log_model(
            name="symptom_routing_agent",
            python_model=str(PROJECT_ROOT / "src" / "symptom_routing" / "assistant" / "agent.py"),
            code_paths=[str(PROJECT_ROOT / "src")],
            input_example=INPUT_EXAMPLE,
            registered_model_name=REGISTERED_MODEL_NAME,
            pip_requirements=[
                "mlflow==3.6.0",
            ],
        )

    client = mlflow.MlflowClient()
    versions = client.search_model_versions(f"name = '{REGISTERED_MODEL_NAME}'")
    latest_version = max(int(version.version) for version in versions)

    validation = mlflow.models.predict(
        model_uri=f"models:/{REGISTERED_MODEL_NAME}/{latest_version}",
        input_data=INPUT_EXAMPLE,
        env_manager="uv",
    )

    print(
        json.dumps(
            {
                "registered_model_name": REGISTERED_MODEL_NAME,
                "version": latest_version,
                "model_uri": model_info.model_uri,
                "validation": validation,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
