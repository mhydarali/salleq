# Databricks notebook source
# MAGIC %md
# MAGIC # Validate Risk Logic

# COMMAND ----------

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.symptom_routing.assistant.tools import build_routing_decision

checks = {
    "emergency_stop_chest_pain": build_routing_decision(
        "Chest pain and shortness of breath for two hours",
        patient_age_group="adult",
        explicit_duration_hours=2,
    ),
    "ctas3_hospital_only": build_routing_decision(
        "Severe abdominal pain getting worse since yesterday",
        patient_age_group="adult",
        explicit_duration_hours=28,
    ),
    "low_acuity_queue": build_routing_decision(
        "Minor cut on finger with light bleeding, stable for 2 hours",
        patient_age_group="adult",
        explicit_duration_hours=2,
    ),
}

assert checks["emergency_stop_chest_pain"]["emergency_stop"] is True
assert checks["emergency_stop_chest_pain"]["queue_eligible"] is False
assert checks["ctas3_hospital_only"]["provisional_ctas_level"] == 3
assert checks["ctas3_hospital_only"]["recommended_facility_type"] == "hospital"
assert checks["low_acuity_queue"]["provisional_ctas_level"] in {4, 5}

display(spark.createDataFrame([(name, payload["provisional_ctas_level"], payload["risk_score"], payload["queue_eligible"]) for name, payload in checks.items()], ["check_name", "ctas_level", "risk_score", "queue_eligible"]))
