import streamlit as st

from src.ui.session_state import DEFAULT_CENTER, DEFAULT_ZOOM
from src.ui.session_state import init_session_state
from src.ui.sidebar_sections import render_sidebar
from src.ui.state_manager import get_state_snapshot
from src.ui.styles import apply_global_styles, render_page_header
from src.utils.nearby_places_utils import clear_nearby_cache, get_nearby_cache_stats
from src.utils.place_photo_utils import clear_photo_cache, get_photo_cache_stats

st.set_page_config(page_title="Settings - My Map Explorer", layout="wide")

apply_global_styles()
init_session_state()
render_sidebar()

render_page_header("⚙️ Settings", "Map and behavior settings")

if st.session_state.pop("settings_cache_cleared_notice", False):
    st.success("All cached nearby/photo data has been cleared.")

with st.expander("🗺️ Map Defaults", expanded=False):
    st.caption(
        "These controls reset only the current session map view (center/zoom). "
        "They do not affect pins, routes, or saved history."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset map center to default", key="settings_reset_center_btn", use_container_width=True):
            st.session_state.map_center = DEFAULT_CENTER.copy()
            st.success("Map center reset to default.")
    with col2:
        if st.button("Reset zoom to default", key="settings_reset_zoom_btn", use_container_width=True):
            st.session_state.zoom = DEFAULT_ZOOM
            st.success("Map zoom reset to default.")

with st.expander("🧹 Cache Management", expanded=False):
    st.caption("Clear locally downloaded cache files and in-session cache data.")

    nearby_stats = get_nearby_cache_stats()
    photo_stats = get_photo_cache_stats()

    col_cache_1, col_cache_2, col_cache_3 = st.columns(3)
    with col_cache_1:
        st.metric("Nearby cache entries", nearby_stats["persistent_entries"])
    with col_cache_2:
        st.metric("Photo cache entries", photo_stats["persistent_entries"])
    with col_cache_3:
        total_kb = (nearby_stats["file_size_bytes"] + photo_stats["file_size_bytes"]) / 1024
        st.metric("Total cache size", f"{total_kb:.1f} KB")

    st.caption(
        f"In-memory nearby cache entries: {nearby_stats['memory_entries']}"
    )

    if st.button("Clear All Downloaded Cache", key="settings_clear_all_cache_btn", use_container_width=True):
        clear_nearby_cache()
        clear_photo_cache()

        st.session_state.pin_photo_cache = {}
        st.session_state.nearby_places = {}
        st.session_state.show_nearby_places = False
        st.session_state.settings_cache_cleared_notice = True
        st.rerun()

with st.expander("🧠 Session State Monitor", expanded=False):
    st.caption("Centralized view of current platform variables.")
    st.json(get_state_snapshot())

st.divider()
if st.button("⬅️ Back to Map", use_container_width=True, key="settings_back_to_map_btn"):
    try:
        st.switch_page("app.py")
    except Exception:
        st.info("Open app.py from the Pages panel in the sidebar.")
