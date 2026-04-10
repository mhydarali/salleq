from __future__ import annotations

import streamlit as st

from streamlit_data import load_user_profile
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


apply_global_styles()
email = st.session_state.get("selected_email")
if not email:
    st.switch_page("app.py")

profile = st.session_state.get("user_profile") or load_user_profile(email)
render_shell("Patient Profile", email)

if not profile:
    st.info("No profile available for this user.")
else:
    st.markdown(
        f"""
        <div class="sq-card">
          <div class="sq-metric-inline">{profile.get("full_name", "Unknown patient")}</div>
          <div class="sq-subtle">{email}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    fields = [
        ("Date of birth", profile.get("date_of_birth")),
        ("Blood type", profile.get("blood_type")),
        ("Insurance number", profile.get("insurance_number")),
        ("Phone number", profile.get("phone_number")),
        ("Allergies", profile.get("allergies")),
        ("Medical history", profile.get("medical_antecedents")),
        ("Address", profile.get("address")),
    ]
    for label, value in fields:
        st.markdown(
            f"""
            <div class="sq-list-item">
              <div class="sq-metric-label">{label}</div>
              <div class="sq-subtle">{value or 'Not available'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

close_shell()
render_bottom_nav("PROFILE")
