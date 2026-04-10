# Databricks notebook source
# MAGIC %md
# MAGIC # SalleQ Demo Queries

# COMMAND ----------

spark.sql(
    """
    SELECT
      facility_name,
      city,
      wait_time_non_priority_minutes,
      people_waiting,
      stretcher_occupancy_pct,
      virtual_queue_depth
    FROM montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_facility_live_joined
    ORDER BY wait_time_non_priority_minutes DESC
    LIMIT 20
    """
).display()

# COMMAND ----------

spark.sql(
    """
    SELECT
      facility_name,
      incoming_queue_count,
      arrivals_next_2h,
      avg_live_wait_minutes,
      ctas_4_count + ctas_5_count AS low_acuity_mix
    FROM montreal_hackathon.salleq_ctas_virtual_waiting_room.vw_staff_dashboard_secure
    ORDER BY incoming_queue_count DESC
    """
).display()
