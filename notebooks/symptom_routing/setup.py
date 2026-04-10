# Databricks notebook source
# MAGIC %md
# MAGIC # Setup SalleQ Symptom Routing Agent

# COMMAND ----------

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.symptom_routing.data.generate_simulated_cases import build_seed_sql


def run_sql_script(sql_text: str) -> None:
    statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]
    for statement in statements:
        spark.sql(statement)


run_sql_script((project_root / "sql" / "symptom_routing" / "01_schema.sql").read_text())
run_sql_script((project_root / "sql" / "symptom_routing" / "02_reference_data.sql").read_text())
run_sql_script(build_seed_sql("montreal_hackathon.salleq_symptom_routing_agent.intake_sessions_simulated"))

display(spark.sql("SELECT COUNT(*) AS simulated_case_count FROM montreal_hackathon.salleq_symptom_routing_agent.intake_sessions_simulated"))
