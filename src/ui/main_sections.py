import streamlit as st

from src.utils.history_utils import save_to_history
from src.utils.location_utils import get_current_location
from src.utils.nearby_places_utils import get_nearby_places
from src.utils.search_utils import search_address_candidates
from src.ui.session_state import DEFAULT_CENTER, DEFAULT_ZOOM
from src.ui.styles import render_page_header


def render_header() -> None:
    render_page_header(
        title="🗺️ My Map Explorer",
        subtitle="Navigate, Search & Plan Routes",
    )


def render_location_info_panel() -> None:
    if not (st.session_state.show_location_debug and st.session_state.location_info):
        return

    info = st.session_state.location_info

    col_loc_title, col_loc_toggle = st.columns([0.85, 0.15])
    with col_loc_title:
        st.markdown("### 📍 Your Location")
    with col_loc_toggle:
        if st.button(
            "−" if st.session_state.show_location_info else "+",
            key="location_info_toggle",
            help="Toggle details",
        ):
            st.session_state.show_location_info = not st.session_state.show_location_info
            st.rerun()

    col_info_1, col_info_2 = st.columns(2)
    with col_info_1:
        st.metric("🏙️ City", info.get("city", "N/A"))
    with col_info_2:
        st.metric("🌍 Country", info.get("country", "N/A"))

    if st.session_state.show_location_info:
        col_info_3, col_info_4 = st.columns(2)
        with col_info_3:
            st.metric("📡 Source", info.get("source", "N/A"))
        with col_info_4:
            st.metric("📐 Accuracy", info.get("accuracy", "N/A"))

        col_lat, col_lon = st.columns(2)
        with col_lat:
            st.code(f"Latitude: {info['coords'][0]:.6f}", language="text")
        with col_lon:
            st.code(f"Longitude: {info['coords'][1]:.6f}", language="text")

    st.divider()


def render_main_action_buttons() -> None:
    col_action_1, col_action_2, col_action_3, col_action_4 = st.columns(4)

    with col_action_1:
        if st.button("🏠 My Location", use_container_width=True, key="main_location_btn"):
            try:
                location_info = get_current_location(show_debug=True)
                if location_info and location_info["coords"]:
                    st.session_state.map_center = location_info["coords"]
                    st.session_state.zoom = 14
                    st.session_state.location_info = location_info
                    st.session_state.show_location_debug = True
                    st.rerun()
                else:
                    st.warning("⚠️ Could not detect location")
            except Exception as exc:
                st.error(f"Error: {str(exc)}")

    with col_action_2:
        if st.button("🔄 Refresh Map", key="main_refresh_map_btn", use_container_width=True):
            st.rerun()

    with col_action_3:
        if st.button("⚙️ Reset View", key="main_reset_view_btn", use_container_width=True):
            st.session_state.map_center = DEFAULT_CENTER.copy()
            st.session_state.zoom = DEFAULT_ZOOM
            st.rerun()

    with col_action_4:
        if st.button("ℹ️ About", key="main_about_btn", use_container_width=True):
            try:
                st.switch_page("pages/1_About.py")
            except Exception:
                st.info("Open About page from the left sidebar Pages panel.")


def _apply_selected_search_result(query: str, coords: list[float], label: str = "") -> None:
    st.session_state.map_center = coords
    st.session_state.zoom = 15
    save_to_history(query, coords)

    previous_nearby = st.session_state.nearby_places
    fetched_nearby = {}

    with st.spinner("🔍 Finding nearby places..."):
        # Overpass can intermittently return empty payloads; retry quickly before giving up.
        for _ in range(2):
            nearby = get_nearby_places(coords[0], coords[1], st.session_state.search_radius_km)
            if nearby and len(nearby) > 0:
                fetched_nearby = nearby
                break

    if fetched_nearby:
        st.session_state.nearby_places = fetched_nearby
        st.session_state.show_nearby_places = True
    elif previous_nearby:
        st.session_state.nearby_places = previous_nearby
        st.session_state.show_nearby_places = True
        st.info("Nearby places service is temporarily unstable. Showing the last successful nearby results.")
    else:
        st.session_state.nearby_places = {}
        st.session_state.show_nearby_places = True

    if label:
        st.success(f"✅ Found: {label}")
    else:
        st.success(f"✅ Found: {query}")


def render_main_search_section(compact: bool = False) -> None:
    if not compact:
        st.markdown("### 🔍 Search Location")
    search_query = st.text_input(
        "Find a place:",
        key="search_input",
        placeholder="e.g., 'Kuala Lumpur', 'Petronas Tower'",
        label_visibility="collapsed",
    )

    with st.expander("Search Options", expanded=False):
        control_1, control_2 = st.columns([0.7, 0.3])
        with control_1:
            st.session_state.search_use_malaysia_bias = st.checkbox(
                "Malaysia-focused search",
                value=st.session_state.search_use_malaysia_bias,
                key="search_bias_checkbox",
                help="When disabled, search is fully global and not biased to Malaysia.",
            )
        with control_2:
            st.markdown("**Search Radius**")
            st.session_state.search_radius_km = st.slider(
                "Nearby places search radius (km):",
                min_value=0.5,
                max_value=5.0,
                value=st.session_state.search_radius_km,
                step=0.5,
                key="radius_slider",
                label_visibility="collapsed",
            )

    col_search_1, col_search_2 = st.columns(2)
    with col_search_1:
        if st.button("🔍 Search", key="main_search_btn", use_container_width=True):
            if search_query:
                try:
                    candidates = search_address_candidates(
                        search_query,
                        near_coords=st.session_state.map_center,
                        use_malaysia_bias=st.session_state.search_use_malaysia_bias,
                        max_results=5,
                    )
                    if candidates:
                        st.session_state.search_candidates = candidates
                        st.session_state.search_candidate_query = search_query
                        top = candidates[0]
                        _apply_selected_search_result(
                            search_query,
                            [top["lat"], top["lon"]],
                            label=top.get("label", search_query),
                        )
                    else:
                        st.session_state.search_candidates = []
                        st.error(f"❌ Not found: {search_query}")
                except Exception as exc:
                    st.error(f"⚠️ Error: {str(exc)}")
            else:
                st.warning("Please enter a location")

    with col_search_2:
        if st.button("🔄 Clear", key="main_search_clear_btn", use_container_width=True):
            st.session_state.map_center = DEFAULT_CENTER.copy()
            st.session_state.zoom = DEFAULT_ZOOM
            st.session_state.search_candidates = []
            st.session_state.search_candidate_query = ""
            st.rerun()

    if st.session_state.search_candidates:
        st.caption("Top search matches")
        for idx, candidate in enumerate(st.session_state.search_candidates):
            label = candidate.get("label", f"Match {idx + 1}")
            provider = candidate.get("provider", "unknown")
            if st.button(
                f"{idx + 1}. {label} [{provider}]",
                key=f"main_search_candidate_btn_{idx}",
                use_container_width=True,
            ):
                _apply_selected_search_result(
                    st.session_state.search_candidate_query or search_query,
                    [candidate["lat"], candidate["lon"]],
                    label=label,
                )
                st.rerun()

    if not compact:
        st.divider()
