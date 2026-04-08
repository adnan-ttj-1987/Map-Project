import streamlit as st

from src.ui.session_state import init_session_state
from src.ui.sidebar_sections import render_sidebar
from src.ui.styles import apply_global_styles, render_page_header
from src.utils.changelog_utils import load_update_history

st.set_page_config(page_title="About - My Map Explorer", layout="wide")

apply_global_styles()
init_session_state()
render_sidebar()

render_page_header(
    "ℹ️ About My Map Explorer",
    "Capabilities, architecture, and update timeline",
    icon_line="🗺️ ✨ 🚗 📍 🧭",
)

st.markdown(
    """
    <div style="
        background: linear-gradient(130deg, #0f766e 0%, #14b8a6 45%, #f59e0b 100%);
        border-radius: 18px;
        padding: 18px 20px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
    ">
        <div style="font-size: 34px; line-height: 1.2;">🗺️ ✨ 🚗 📍 🧭</div>
        <div style="font-size: 16px; margin-top: 8px; font-weight: 600;">Plan. Explore. Discover nearby places beautifully.</div>
        <div style="font-size: 13px; margin-top: 4px; opacity: 0.95;">Smart journey planning with role-based pins, route legs, and nearby caching.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### What This Platform Can Do")
    st.markdown("- Search locations using multi-provider geocoding fallback.")
    st.markdown("- Plan routes, view distance and duration, and save route history.")
    st.markdown("- Drop pins interactively and use them as route points.")
    st.markdown("- Discover nearby points of interest by category.")
    st.markdown("- Persist search and route activity for faster repeat work.")

with col2:
    if st.button("⬅️ Back to Map", use_container_width=True, key="about_back_to_map_btn"):
        try:
            st.switch_page("app.py")
        except Exception:
            st.info("Open app.py from the Pages panel in the sidebar.")

st.divider()
st.markdown("### Update History")

history = load_update_history()
if history:
    for idx, item in enumerate(history):
        title = f"{item.get('date', 'Unknown Date')} • v{item.get('version', '-')}: {item.get('title', 'Update')}"
        with st.expander(title, expanded=(idx == 0)):
            details = item.get("details", [])
            if isinstance(details, list):
                for detail in details:
                    st.markdown(f"- {detail}")
            else:
                st.write(str(details))
else:
    st.info("No update history found yet.")
