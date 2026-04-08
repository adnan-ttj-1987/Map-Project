import streamlit as st

from src.ui.state_manager import add_pin
from src.utils.history_utils import clear_all_history, delete_history_item, load_history
from src.utils.location_utils import get_current_location
from src.utils.nearby_places_utils import get_nearby_places
from src.utils.route_history_utils import clear_all_routes, delete_route, load_routes


def _zoom_for_span(span: float) -> int:
    if span < 0.005:
        return 16
    if span < 0.02:
        return 14
    if span < 0.08:
        return 12
    if span < 0.3:
        return 10
    return 8


def _focus_map_on_pins_or_location() -> tuple[bool, str]:
    pins = st.session_state.captured_pins
    if pins:
        lats = [pin["lat"] for pin in pins]
        lons = [pin["lon"] for pin in pins]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        st.session_state.map_center = [(min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0]
        span = max(max_lat - min_lat, max_lon - min_lon)
        st.session_state.zoom = _zoom_for_span(span)
        return True, f"Centered map to fit {len(pins)} captured pin(s)."

    try:
        location_info = get_current_location(show_debug=True)
        if location_info and location_info.get("coords"):
            st.session_state.map_center = location_info["coords"]
            st.session_state.zoom = 14
            st.session_state.location_info = location_info
            st.session_state.show_location_debug = True
            return True, "No pins found. Centered map to your current location."
        return False, "Could not detect current location."
    except Exception as exc:
        return False, f"Error: {str(exc)}"


def _ensure_sidebar_expand_state() -> None:
    if "sidebar_open_search_history" not in st.session_state:
        st.session_state.sidebar_open_search_history = False
    if "sidebar_open_route_history" not in st.session_state:
        st.session_state.sidebar_open_route_history = False


def render_sidebar_histories() -> None:
    _ensure_sidebar_expand_state()

    if (
        not st.session_state.sidebar_open_search_history
        and not st.session_state.sidebar_open_route_history
    ):
        return

    with st.expander(
        "📚 Search History",
        expanded=st.session_state.sidebar_open_search_history,
    ):
        try:
            history = load_history()
            if history:
                for idx, item in enumerate(history):
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        if st.button(f"📍 {item['query']}", key=f"hist_{idx}", use_container_width=True):
                            st.session_state.map_center = item["coords"]
                            st.session_state.zoom = 15
                            lat, lon = item["coords"]
                            add_pin(lat=lat, lon=lon, label=item["query"])
                            with st.spinner("🔍 Finding nearby places..."):
                                st.session_state.nearby_places = get_nearby_places(
                                    lat,
                                    lon,
                                    st.session_state.search_radius_km,
                                )
                                st.session_state.show_nearby_places = True
                            st.rerun()
                    with col2:
                        if st.button("✕", key=f"del_hist_{idx}", use_container_width=True):
                            delete_history_item(idx)
                            st.rerun()

                if st.button("🗑️ Clear All", key="history_clear_all_btn", use_container_width=True):
                    clear_all_history()
                    st.success("✅ History cleared!")
                    st.rerun()
            else:
                st.info("No search history")
        except Exception as exc:
            st.error(f"Error: {str(exc)}")

    with st.expander(
        "📜 Route History",
        expanded=st.session_state.sidebar_open_route_history,
    ):
        try:
            routes = load_routes()
            if routes:
                for idx, route in enumerate(routes):
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        route_text = f"🛣️ {route['start']} → {route['end']}"
                        if st.button(route_text, key=f"route_{idx}", use_container_width=True):
                            st.session_state.route_start = route["start_coords"]
                            st.session_state.route_end = route["end_coords"]
                            st.session_state.start_location = route["start"]
                            st.session_state.end_location = route["end"]
                            st.session_state.route_distance = route["distance"]
                            st.session_state.route_duration = route["duration"]
                            st.rerun()
                    with col2:
                        if st.button("✕", key=f"del_route_{idx}", use_container_width=True):
                            delete_route(idx)
                            st.rerun()

                if st.button("🗑️ Clear All", key="route_history_clear_all_btn", use_container_width=True):
                    clear_all_routes()
                    st.success("✅ Routes cleared!")
                    st.rerun()
            else:
                st.info("No route history")
        except Exception as exc:
            st.error(f"Error: {str(exc)}")


def render_sidebar(include_histories: bool = True) -> None:
    with st.sidebar:
        _ensure_sidebar_expand_state()

        col_sidebar_1, col_sidebar_2 = st.columns([0.7, 0.3])
        with col_sidebar_1:
            st.markdown("### 🗺️ My Map")
        with col_sidebar_2:
            if st.button(
                "−" if not st.session_state.sidebar_collapsed else "+",
                key="sidebar_toggle",
                help="Collapse/Expand",
            ):
                st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
                st.rerun()

        if st.session_state.sidebar_collapsed:
            return

        with st.container():
            action_col_1, action_col_2, action_col_3, action_col_4, action_col_5 = st.columns(5)

            with action_col_1:
                if st.button("🗺️", use_container_width=True, key="sidebar_map_focus_btn", help="Map Focus"):
                    ok, message = _focus_map_on_pins_or_location()
                    if ok:
                        try:
                            st.switch_page("app.py")
                        except Exception:
                            st.success(message)
                            st.rerun()
                    else:
                        st.warning(f"⚠️ {message}")

            with action_col_2:
                if st.button("⚙️", use_container_width=True, key="sidebar_settings_btn", help="Settings"):
                    try:
                        st.switch_page("pages/2_Settings.py")
                    except Exception:
                        st.info("Open Settings page from the Pages panel in the sidebar.")

            with action_col_3:
                if st.button("ℹ️", use_container_width=True, key="sidebar_about_btn", help="About"):
                    try:
                        st.switch_page("pages/1_About.py")
                    except Exception:
                        st.info("Open About page from the Pages panel in the sidebar.")

            with action_col_4:
                if st.button("🕘", use_container_width=True, key="sidebar_search_history_btn", help="Search History"):
                    is_open = st.session_state.sidebar_open_search_history
                    st.session_state.sidebar_open_search_history = not is_open
                    if not is_open:
                        st.session_state.sidebar_open_route_history = False

            with action_col_5:
                if st.button("🛣️", use_container_width=True, key="sidebar_route_history_btn", help="Route History"):
                    is_open = st.session_state.sidebar_open_route_history
                    st.session_state.sidebar_open_route_history = not is_open
                    if not is_open:
                        st.session_state.sidebar_open_search_history = False

        st.divider()

        if include_histories:
            render_sidebar_histories()
