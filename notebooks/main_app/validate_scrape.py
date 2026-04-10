# Databricks notebook source
# MAGIC %md
# MAGIC # Validate Quebec ER Scrape

# COMMAND ----------

from src.ingestion.qc_er_scraper import fetch_quebec_er_records
from src.utils.config import settings
from src.utils.text import now_utc_iso

records = fetch_quebec_er_records(settings.qc_source_url, now_utc_iso())
len(records), records[:3]
