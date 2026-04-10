from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_data import current_user_token, get_staff_dashboard, get_staff_queue_detail
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


apply_global_styles()
render_shell("811 Health Support", "Operational view of incoming virtual queue demand.")

rows = get_staff_dashboard(current_user_token())
if not rows:
    st.info("No scoped staff data is available for the current identity yet.")
else:
    df = pd.DataFrame(rows)
    total_incoming = int(df["incoming_queue_count"].fillna(0).sum())
    arrivals = int(df["arrivals_next_2h"].fillna(0).sum())
    st.markdown(
        f"""
        <div class="sq-card">
          <div class="sq-metric-label">Incoming low-acuity patients</div>
          <div class="sq-metric-value">{total_incoming}</div>
          <div class="sq-subtle">Expected arrivals in next 2 hours: {arrivals}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    facility_names = df["facility_name"].fillna("Unknown").tolist()
    selected = st.selectbox("Facility", facility_names)
    facility_row = df[df["facility_name"] == selected].iloc[0]

    chart_df = df[["facility_name", "incoming_queue_count"]].sort_values("incoming_queue_count", ascending=False)
    fig = px.bar(chart_df, x="facility_name", y="incoming_queue_count", color="incoming_queue_count", color_continuous_scale="Blues")
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    detail = get_staff_queue_detail(str(facility_row["facility_id"]), current_user_token())
    st.markdown(
        f"""
        <div class="sq-card">
          <div class="sq-metric-inline">{selected}</div>
          <div class="sq-subtle">Average live wait {round(float(facility_row.get('avg_live_wait_minutes') or 0), 1)} minutes • CTAS 4-5 volume {int(facility_row.get('ctas_4_count') or 0) + int(facility_row.get('ctas_5_count') or 0)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for item in detail[:5]:
        st.markdown(
            f"""
            <div class="sq-list-item">
              <div class="sq-metric-inline">{item.get("primary_symptom", "Unknown symptom")}</div>
              <div class="sq-subtle">Queue #{item.get("queue_position")} • CTAS {item.get("provisional_ctas_level")} • {item.get("queue_status")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

close_shell()
render_bottom_nav("STAFF")
