import streamlit as st

from src.ui.detail_sections import (
    render_nearby_places_section,
    render_pins_section,
)
from src.ui.main_sections import (
    render_main_search_section,
)
from src.ui.map_sections import render_interactive_map
from src.ui.session_state import init_session_state
from src.ui.sidebar_sections import render_sidebar, render_sidebar_histories
from src.ui.styles import apply_global_styles


st.set_page_config(
    page_title="My Map Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
init_session_state()

render_sidebar(include_histories=False)

with st.sidebar:
    with st.expander("🔍 Search Location", expanded=bool(st.session_state.search_candidates)):
        render_main_search_section(compact=True)

    render_pins_section()
    render_nearby_places_section()

    render_sidebar_histories()

render_interactive_map()
