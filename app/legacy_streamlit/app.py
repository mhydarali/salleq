from __future__ import annotations

import streamlit as st

from streamlit_data import load_demo_users, load_user_profile
from streamlit_styles import apply_global_styles, close_shell, render_bottom_nav, render_shell


def _init_state() -> None:
    defaults = {
        "selected_email": None,
        "user_profile": None,
        "patient_context": "self",
        "assessment_result": None,
        "selected_facility": None,
        "queue_result": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _login(email: str) -> None:
    profile = load_user_profile(email)
    st.session_state.selected_email = email
    st.session_state.user_profile = profile


apply_global_styles()
_init_state()

st.markdown(
    """
    <style>
    .sq-login-hero {
      text-align: center;
      padding: 1.1rem 0 0.2rem 0;
    }
    .sq-logo {
      width: 58px;
      height: 58px;
      margin: 0 auto 0.75rem auto;
      border-radius: 16px;
      background: linear-gradient(180deg, #ffffff 0%, #edf3ff 100%);
      border: 1px solid #e4ebf8;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #173F8A;
      font-size: 1.4rem;
      box-shadow: 0 10px 20px rgba(23, 63, 138, 0.08);
    }
    .sq-tagline {
      color: #7a8aa2;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-weight: 700;
      margin-top: -0.2rem;
    }
    .sq-auth-card {
      position: relative;
      overflow: hidden;
    }
    .sq-auth-card::after {
      content: "";
      position: absolute;
      right: -34px;
      top: -34px;
      width: 120px;
      height: 120px;
      border-radius: 999px;
      background: radial-gradient(circle, #eef3ff 0%, #eef3ff 45%, rgba(238,243,255,0) 70%);
      pointer-events: none;
    }
    .sq-divider {
      display: flex;
      align-items: center;
      color: #93a0b5;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin: 0.75rem 0;
    }
    .sq-divider::before,
    .sq-divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: #e3eaf7;
    }
    .sq-divider::before { margin-right: 0.75rem; }
    .sq-divider::after { margin-left: 0.75rem; }
    .sq-chip {
      text-align: center;
      padding: 0.85rem 0.6rem;
      border-radius: 14px;
      border: 1px solid #e4ebf8;
      background: #f8faff;
      font-weight: 700;
      color: #3b4c66;
      font-size: 0.92rem;
    }
    .sq-mini-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

users = load_demo_users()
emails = [row["email"] for row in users]
default_email = st.session_state.selected_email or (emails[0] if emails else "")

render_shell("", "")
st.markdown(
    """
    <div class="sq-login-hero">
      <div class="sq-logo">+</div>
      <div class="sq-brand" style="font-size:2.2rem; margin-bottom:0.2rem;">SalleQ</div>
      <div class="sq-tagline">The Digital Sanctuary</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown(
        """
        <div class="sq-card sq-auth-card">
          <div class="sq-metric-inline" style="font-size:1.8rem; color:#20344d;">Welcome Back</div>
          <div style="height:0.35rem"></div>
          <div class="sq-subtle">Please enter your details to access your queue, assessment, and facility recommendations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

entered_email = st.text_input("Email address", value=default_email, placeholder="name@example.com")
password = st.text_input("Password", value="••••••••", type="password")

context = st.radio(
    "Care context",
    options=["self", "another person"],
    horizontal=True,
    format_func=lambda v: "I am seeking care for myself" if v == "self" else "I am seeking care for another person",
    index=0 if st.session_state.patient_context == "self" else 1,
)
st.session_state.patient_context = context

if st.button("Sign In to SalleQ", use_container_width=True, type="primary"):
    email_to_use = entered_email if entered_email in emails else default_email
    _login(email_to_use)
    st.switch_page("pages/1_Assessment.py")

st.markdown('<div class="sq-divider">Or continue with</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="sq-mini-grid">
      <div class="sq-chip">Google</div>
      <div class="sq-chip">Apple</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Demo patient selector"):
    selected = st.selectbox(
        "Choose a Databricks-backed demo user",
        options=emails,
        index=emails.index(default_email) if default_email in emails else 0,
    )
    if st.button("Load selected demo profile", use_container_width=True):
        _login(selected)
        st.rerun()

profile = st.session_state.user_profile or load_user_profile(default_email)
if profile:
    st.markdown(
        f"""
        <div class="sq-card">
          <div class="sq-metric-label">Current demo identity</div>
          <div class="sq-metric-inline">{profile.get("full_name") or default_email}</div>
          <div class="sq-subtle">{profile.get("email", default_email)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="sq-card">
      <div class="sq-metric-label">What this app does</div>
      <div class="sq-subtle">Assess symptoms, flag emergency risk, recommend Quebec care sites, reserve a virtual queue spot, and track the patient journey from home.</div>
      <div style="height:0.8rem"></div>
      <div class="sq-mini-grid">
        <div class="sq-chip">Urgency Check</div>
        <div class="sq-chip">Live Wait Times</div>
        <div class="sq-chip">Virtual Queue</div>
        <div class="sq-chip">Patient Profile</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if password and st.button("Preview Queue Screen", use_container_width=True):
    email_to_use = entered_email if entered_email in emails else default_email
    _login(email_to_use)
    st.switch_page("pages/3_Queue.py")

close_shell()
render_bottom_nav("HOME")
