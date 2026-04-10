# Databricks notebook source
# MAGIC %md
# MAGIC # Demo Examples For Frontend Integration

# COMMAND ----------

import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.symptom_routing.assistant.tools import build_routing_decision

frontend_request = {
    "symptom_text": "Fever and ear pain since this morning",
    "patient_age_group": "child",
    "duration_hours": 8,
}

frontend_response = build_routing_decision(
    symptom_text=frontend_request["symptom_text"],
    patient_age_group=frontend_request["patient_age_group"],
    explicit_duration_hours=frontend_request["duration_hours"],
)

print("Frontend request")
print(json.dumps(frontend_request, indent=2))
print("\nFrontend response")
print(json.dumps(frontend_response, ensure_ascii=False, indent=2))
