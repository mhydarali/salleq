from __future__ import annotations

from pathlib import Path
import sys

from pyspark.sql import SparkSession

project_root = (
    Path(__file__).resolve().parents[2]
    if "__file__" in globals()
    else Path("/Workspace/Users/muhammad.hydarali@mail.mcgill.ca/salleq_ctas_virtual_waiting_room")
)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.job_runner import bootstrap_tables


if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    print(bootstrap_tables(spark))
