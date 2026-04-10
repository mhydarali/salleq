# Databricks notebook source
# MAGIC %md
# MAGIC # SalleQ Setup
# MAGIC
# MAGIC Bootstraps facility master data, scrapes the live Quebec ER page, computes facility matches,
# MAGIC and writes the initial project tables into `montreal_hackathon.salleq_ctas_virtual_waiting_room`.

from pathlib import Path
import sys

from pyspark.sql import SparkSession

project_root = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.job_runner import bootstrap_tables

spark = SparkSession.builder.getOrCreate()
payload = bootstrap_tables(spark)

# COMMAND ----------

display(spark.table("montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_facility_live_joined").limit(20))
