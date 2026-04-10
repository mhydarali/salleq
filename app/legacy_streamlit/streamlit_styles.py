from __future__ import annotations

import streamlit as st


def apply_global_styles() -> None:
    st.set_page_config(
        page_title="SalleQ",
        page_icon="🏥",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        :root {
          --sq-blue: #173F8A;
          --sq-blue-2: #275cc5;
          --sq-bg: #f5f7fc;
          --sq-card: #ffffff;
          --sq-danger: #c7252a;
          --sq-success: #1f9d61;
          --sq-text: #16314c;
          --sq-muted: #70819a;
          --sq-border: #dbe4f2;
        }
        .stApp {
          background: var(--sq-bg);
          color: var(--sq-text);
        }
        .block-container {
          max-width: 440px;
          padding-top: 1rem;
          padding-bottom: 4rem;
        }
        div[data-testid="stSidebar"] {display: none;}
        header[data-testid="stHeader"] {background: transparent;}
        .sq-shell {
          background: linear-gradient(180deg, #ffffff 0%, #f5f7fc 100%);
          border: 1px solid var(--sq-border);
          border-radius: 28px;
          padding: 1.25rem 1rem 5rem 1rem;
          box-shadow: 0 18px 40px rgba(23, 63, 138, 0.08);
          min-height: 90vh;
          position: relative;
        }
        .sq-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
        }
        .sq-brand {
          font-size: 1.3rem;
          font-weight: 800;
          color: var(--sq-blue);
        }
        .sq-card {
          background: var(--sq-card);
          border-radius: 22px;
          padding: 1rem;
          border: 1px solid rgba(23, 63, 138, 0.08);
          box-shadow: 0 10px 24px rgba(23, 63, 138, 0.08);
          margin-bottom: 0.9rem;
        }
        .sq-hero {
          text-align: center;
          padding: 0.5rem 0 0.8rem 0;
        }
        .sq-hero h1 {
          color: var(--sq-blue);
          margin: 0.4rem 0 0.4rem 0;
          font-size: 2rem;
          line-height: 1.1;
        }
        .sq-subtle {
          color: var(--sq-muted);
          font-size: 0.92rem;
        }
        .sq-badge {
          display: inline-block;
          padding: 0.2rem 0.55rem;
          border-radius: 999px;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.02em;
          background: #ebf4ff;
          color: var(--sq-blue);
        }
        .sq-badge.success { background: #e9f8f0; color: var(--sq-success); }
        .sq-badge.danger { background: #feecec; color: var(--sq-danger); }
        .sq-alert {
          border-radius: 22px;
          padding: 1rem;
          margin-bottom: 1rem;
          color: white;
          background: linear-gradient(180deg, #d53438 0%, #b91f26 100%);
          box-shadow: 0 18px 28px rgba(185, 31, 38, 0.25);
        }
        .sq-alert h3, .sq-alert p { color: white; margin: 0; }
        .sq-metric-label {
          color: var(--sq-muted);
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-weight: 700;
          margin-bottom: 0.25rem;
        }
        .sq-metric-value {
          color: var(--sq-blue);
          font-size: 2rem;
          font-weight: 800;
          line-height: 1.05;
        }
        .sq-metric-inline {
          color: var(--sq-text);
          font-size: 1.1rem;
          font-weight: 700;
        }
        .sq-list-item {
          background: white;
          border: 1px solid rgba(23, 63, 138, 0.08);
          border-radius: 18px;
          padding: 0.9rem;
          margin-bottom: 0.75rem;
        }
        .sq-timeline {
          border-left: 3px solid #cad7f5;
          margin-left: 0.45rem;
          padding-left: 1rem;
        }
        .sq-time-node {
          position: relative;
          padding-bottom: 0.85rem;
        }
        .sq-time-node::before {
          content: "";
          position: absolute;
          left: -1.37rem;
          top: 0.25rem;
          width: 0.7rem;
          height: 0.7rem;
          border-radius: 999px;
          background: var(--sq-blue);
          border: 3px solid #eef3ff;
        }
        .sq-nav {
          position: fixed;
          left: 50%;
          transform: translateX(-50%);
          bottom: 0.75rem;
          width: min(408px, calc(100vw - 2rem));
          background: white;
          border: 1px solid var(--sq-border);
          border-radius: 24px;
          box-shadow: 0 12px 24px rgba(23, 63, 138, 0.08);
          padding: 0.6rem 0.8rem;
          z-index: 999;
        }
        .sq-nav-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 0.25rem;
          text-align: center;
          font-size: 0.72rem;
          color: var(--sq-muted);
        }
        .sq-nav-grid .active {
          color: var(--sq-blue);
          font-weight: 700;
        }
        div[data-testid="stVerticalBlock"] > div:has(> div.sq-nav) {
          position: sticky;
          bottom: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_shell(title: str, subtitle: str | None = None) -> None:
    st.markdown('<div class="sq-shell">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sq-topbar">
          <div class="sq-brand">SalleQ</div>
          <div class="sq-badge">Live Demo</div>
        </div>
        <div class="sq-hero">
          <h1>{title}</h1>
          {f'<div class="sq-subtle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def close_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def render_bottom_nav(active: str) -> None:
    labels = ["HOME", "QUEUE", "CARE", "CAREGIVERS", "PROFILE"]
    active_map = {
        "HOME": "HOME",
        "ASSESSMENT": "CARE",
        "RECOMMENDATIONS": "CARE",
        "QUEUE": "QUEUE",
        "PROFILE": "PROFILE",
        "STAFF": "CAREGIVERS",
    }
    current = active_map.get(active.upper(), active.upper())
    items = "".join(
        f'<div class="{"active" if label == current else ""}">{label}</div>' for label in labels
    )
    st.markdown(
        f'<div class="sq-nav"><div class="sq-nav-grid">{items}</div></div>',
        unsafe_allow_html=True,
    )
