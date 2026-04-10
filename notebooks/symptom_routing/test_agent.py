# Databricks notebook source
# MAGIC %md
# MAGIC # Test The Symptom Routing Agent

# COMMAND ----------

import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.symptom_routing.assistant.tools import build_routing_decision

examples = [
    {
        "label": "English low-acuity",
        "symptom_text": "Twisted ankle with swelling after a fall, stable pain for 4 hours",
        "patient_age_group": "adult",
        "duration_hours": 4,
    },
    {
        "label": "French emergency",
        "symptom_text": "Douleur thoracique et difficulte respiratoire severe depuis une heure",
        "patient_age_group": "older_adult",
        "duration_hours": 1,
    },
]

for example in examples:
    result = build_routing_decision(
        symptom_text=example["symptom_text"],
        patient_age_group=example["patient_age_group"],
        explicit_duration_hours=example["duration_hours"],
    )
    print(f"\n## {example['label']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
