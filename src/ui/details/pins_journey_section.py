import math
import streamlit as st

from src.utils.nearby_places_utils import get_nearby_places
from src.utils.routing_utils import get_multi_waypoint_route, get_route
from src.ui.state_manager import (
    add_pin,
    clear_all_pins,
    remove_pin_at,
    set_journey_signature,
    set_pin_role,
    sync_journey_state,
)
from src.ui.details.shared import (
    default_pin_label,
    focus_on_location_and_refresh_nearby,
    generate_breakpoints,
    get_pin_label,
    pin_key,
)


def _display_km(distance_value: float) -> str:
    return f"{math.ceil(distance_value)} km"


def _display_duration_minutes(total_minutes_value: float) -> str:
    total_minutes = int(total_minutes_value)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


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


def _fit_map_to_points(points: list[list[float]]) -> None:
    if not points:
        return

    lats = [point[0] for point in points]
    lons = [point[1] for point in points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    st.session_state.map_center = [(min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0]
    span = max(max_lat - min_lat, max_lon - min_lon)
    st.session_state.zoom = _zoom_for_span(span)


def _route_points_from_route_data(route_data: dict | None) -> list[list[float]]:
    if not route_data:
        return []
    coords = route_data.get("coordinates", [])
    if not isinstance(coords, list):
        return []
    return [[coord[1], coord[0]] for coord in coords if isinstance(coord, list) and len(coord) == 2]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _breakpoints_from_route_points(
    route_points: list[list[float]],
    break_count: int,
    leg_idx: int,
) -> list[dict]:
    if break_count <= 0 or len(route_points) < 2:
        return []

    cumulative = [0.0]
    total = 0.0
    for i in range(1, len(route_points)):
        prev = route_points[i - 1]
        curr = route_points[i]
        seg = _haversine_km(prev[0], prev[1], curr[0], curr[1])
        total += seg
        cumulative.append(total)

    if total <= 0:
        return []

    targets = [total * (idx / (break_count + 1)) for idx in range(1, break_count + 1)]
    breaks: list[dict] = []

    for idx, target in enumerate(targets, start=1):
        seg_idx = 1
        while seg_idx < len(cumulative) and cumulative[seg_idx] < target:
            seg_idx += 1

        if seg_idx >= len(route_points):
            seg_idx = len(route_points) - 1

        a = route_points[seg_idx - 1]
        b = route_points[seg_idx]
        start_dist = cumulative[seg_idx - 1]
        seg_dist = max(cumulative[seg_idx] - start_dist, 1e-9)
        ratio = min(max((target - start_dist) / seg_dist, 0.0), 1.0)

        lat = a[0] + (b[0] - a[0]) * ratio
        lon = a[1] + (b[1] - a[1]) * ratio
        breaks.append({"lat": lat, "lon": lon, "name": f"Break L{leg_idx}-{idx}"})

    return breaks


def _next_break_stop_label() -> str:
    existing_labels = set(st.session_state.pin_labels.values())
    counter = 1
    while True:
        candidate = f"Break Stop {counter}"
        if candidate not in existing_labels:
            return candidate
        counter += 1


def _build_expanded_waypoints(waypoint_sequence: list[int]) -> tuple[list[list[float]], list[str]]:
    coords: list[list[float]] = []
    labels: list[str] = []
    leg_breaks = st.session_state.get("generated_leg_breakpoints", {}) or {}

    if not waypoint_sequence:
        return coords, labels

    first_idx = waypoint_sequence[0]
    first_pin = st.session_state.captured_pins[first_idx]
    coords.append([first_pin["lat"], first_pin["lon"]])
    labels.append(get_pin_label(first_idx))

    for leg_idx in range(1, len(waypoint_sequence)):
        generated = leg_breaks.get(str(leg_idx), [])
        for bp in generated:
            lat = bp.get("lat")
            lon = bp.get("lon")
            if lat is None or lon is None:
                continue
            coords.append([lat, lon])
            labels.append(bp.get("name", f"Break L{leg_idx}"))

        pin_idx = waypoint_sequence[leg_idx]
        pin = st.session_state.captured_pins[pin_idx]
        coords.append([pin["lat"], pin["lon"]])
        labels.append(get_pin_label(pin_idx))

    return coords, labels


def _refresh_breakpoint_route(waypoint_sequence: list[int]) -> None:
    expanded_coords, expanded_labels = _build_expanded_waypoints(waypoint_sequence)
    if len(expanded_coords) < 2:
        st.session_state.breakpoint_waypoints = []
        st.session_state.breakpoint_route_data = None
        return

    route_result = get_multi_waypoint_route(expanded_coords)
    if not route_result:
        st.session_state.breakpoint_waypoints = []
        st.session_state.breakpoint_route_data = None
        return

    st.session_state.breakpoint_waypoints = [
        {"lat": point[0], "lon": point[1], "label": label}
        for point, label in zip(expanded_coords, expanded_labels)
    ]
    st.session_state.breakpoint_route_data = route_result


def render_pins_section() -> None:
    if not st.session_state.captured_pins:
        return

    st.divider()

    with st.expander("📌 Captured Pins", expanded=True):
        if st.button("🗑️ Clear All Pins", key="pins_clear_all_btn", use_container_width=True):
            clear_all_pins()
            st.success("✅ All pins cleared!")
            st.rerun()

        st.info(f"📍 Total pins: {len(st.session_state.captured_pins)}")

        for idx, pin in enumerate(st.session_state.captured_pins):
            key = pin_key(idx)
            current_role = st.session_state.pin_roles.get(key, "unassigned")
            current_label = get_pin_label(idx)
            st.markdown(f"**Pin {idx + 1}**")

            new_label = st.text_input(
                f"Label for Pin {idx + 1}",
                value=current_label,
                key=f"pin_label_input_{idx}",
                placeholder=f"{default_pin_label(idx)}",
            ).strip()
            st.session_state.pin_labels[key] = new_label or default_pin_label(idx)

            selected_role = st.selectbox(
                f"Role for Pin {idx + 1}",
                ["UNASSIGNED", "START", "STOP", "END"],
                index=["UNASSIGNED", "START", "STOP", "END"].index(current_role.upper()),
                key=f"pin_role_select_{idx}",
            )
            role_changed = set_pin_role(
                idx,
                None if selected_role == "UNASSIGNED" else selected_role,
            )

            if role_changed:
                st.info("Journey route cleared. Recalculate after changing pin roles.")

            st.caption(f"📍 {pin['lat']:.6f}, {pin['lon']:.6f}")

            col_focus, col_del = st.columns(2)
            with col_focus:
                if st.button("🎯 Focus", key=f"focus_pin_{idx}", use_container_width=True):
                    focus_on_location_and_refresh_nearby(pin["lat"], pin["lon"])
                    st.rerun()
            with col_del:
                if st.button("🗑️ Delete", key=f"del_pin_{idx}", use_container_width=True):
                    remove_pin_at(idx)
                    st.rerun()

            st.markdown("---")

    render_build_journey_section()


def render_build_journey_section() -> None:
    if not st.session_state.captured_pins:
        return

    st.divider()

    with st.expander("🚗 Build Your Journey", expanded=True):
        role_to_indexes = {"start": [], "end": [], "stop": []}
        for idx in range(len(st.session_state.captured_pins)):
            role = st.session_state.pin_roles.get(pin_key(idx))
            if role in role_to_indexes:
                role_to_indexes[role].append(idx)

        start_pin = role_to_indexes["start"][0] if role_to_indexes["start"] else None
        end_pin = role_to_indexes["end"][0] if role_to_indexes["end"] else None
        stop_pins = role_to_indexes["stop"]

        if len(role_to_indexes["start"]) > 1:
            st.warning("Multiple START pins found. Using the first one.")
        if len(role_to_indexes["end"]) > 1:
            st.warning("Multiple END pins found. Using the first one.")

        if start_pin is None or end_pin is None:
            missing = []
            if start_pin is None:
                missing.append("START point")
            if end_pin is None:
                missing.append("END point")
            st.warning(f"⚠️ Assign {' and '.join(missing)} to build a journey")
            return

        if start_pin == end_pin:
            st.warning("⚠️ START and END cannot be the same pin.")
            return

        waypoint_sequence = [start_pin] + stop_pins + [end_pin]

        if sync_journey_state(waypoint_sequence):
            st.info("Journey route updated. Recalculate after changing route-defining pins.")

        labels = [get_pin_label(idx) for idx in waypoint_sequence]
        st.success(f"✅ Journey ready: {len(waypoint_sequence)} waypoints")
        for order_idx, label in enumerate(labels, start=1):
            st.caption(f"{order_idx}. {label}")

        if st.button("🗺️ Calculate Journey Route", key="create_journey_route_btn", use_container_width=True):
            waypoints = [
                [st.session_state.captured_pins[idx]["lat"], st.session_state.captured_pins[idx]["lon"]]
                for idx in waypoint_sequence
            ]
            route_result = get_multi_waypoint_route(waypoints)
            if route_result:
                st.session_state.multi_waypoint_route = route_result
                st.session_state.selected_pins_for_route = waypoint_sequence
                st.session_state.generated_leg_breakpoints = {}
                st.session_state.breakpoint_waypoints = []
                st.session_state.breakpoint_route_data = None
                st.session_state.journey_route_display_mode = "Base Route"
                st.session_state.route_start = None
                st.session_state.route_end = None
                set_journey_signature(waypoint_sequence)
                st.success(
                    f"✅ Route created: {_display_km(route_result['distance'])}, "
                    f"{_display_duration_minutes(route_result['duration'])}"
                )
                st.rerun()
            else:
                st.error("❌ Could not calculate route. Try checking your pins.")

        route = st.session_state.multi_waypoint_route
        if not route:
            return

        with st.expander("📊 Route Summary", expanded=True):
            has_breakpoint_route = bool(
                st.session_state.get("breakpoint_route_data")
                and st.session_state.get("breakpoint_waypoints")
            )
            route_mode_options = ["Base Route"]
            if has_breakpoint_route:
                route_mode_options.append("Breakpoint-Enhanced Route")

            current_mode = st.session_state.get("journey_route_display_mode", "Base Route")
            if current_mode not in route_mode_options:
                current_mode = "Base Route"

            selected_mode = st.radio(
                "Route display mode",
                options=route_mode_options,
                index=route_mode_options.index(current_mode),
                key="journey_route_display_mode_selector",
                horizontal=True,
            )
            st.session_state.journey_route_display_mode = selected_mode

            if selected_mode != current_mode:
                if selected_mode == "Breakpoint-Enhanced Route":
                    fit_points = _route_points_from_route_data(
                        st.session_state.get("breakpoint_route_data")
                    )
                else:
                    fit_points = _route_points_from_route_data(route)

                if fit_points:
                    _fit_map_to_points(fit_points)

            if (
                selected_mode == "Breakpoint-Enhanced Route"
                and st.session_state.get("breakpoint_route_data")
                and st.session_state.get("breakpoint_waypoints")
            ):
                display_route = st.session_state.breakpoint_route_data
                display_waypoint_labels = [
                    wp.get("label", "Waypoint")
                    for wp in st.session_state.breakpoint_waypoints
                ]
            else:
                display_route = route
                display_waypoint_labels = [get_pin_label(idx) for idx in waypoint_sequence]

            st.caption(f"📏 Total Distance: {_display_km(display_route['distance'])}")
            st.caption(f"⏱️ Total Duration: {_display_duration_minutes(display_route['duration'])}")
            st.caption(f"🛣️ Legs: {len(display_route.get('legs', []))}")
            if has_breakpoint_route:
                st.caption("Map route follows the selected display mode above.")

            st.caption("Map-aligned waypoint order:")
            for order_idx, label in enumerate(display_waypoint_labels, start=1):
                st.caption(f"{order_idx}. {label}")

            if selected_mode == "Breakpoint-Enhanced Route":
                display_legs = display_route.get("legs", [])
                for leg_idx, leg in enumerate(display_legs, start=1):
                    start_label = display_waypoint_labels[leg_idx - 1]
                    end_label = display_waypoint_labels[leg_idx]
                    with st.expander(
                        f"Leg {leg_idx}: {start_label} → {end_label}",
                        expanded=False,
                    ):
                        st.caption(
                            f"{_display_km(leg['distance'])} • "
                            f"{_display_duration_minutes(leg['duration'])}"
                        )
                        st.caption("This leg comes from breakpoint-enhanced routing.")
            else:
                legs = route.get("legs", [])
                for leg_idx, leg in enumerate(legs, start=1):
                    start_idx = waypoint_sequence[leg_idx - 1]
                    end_idx = waypoint_sequence[leg_idx]
                    start_pin_data = st.session_state.captured_pins[start_idx]
                    end_pin_data = st.session_state.captured_pins[end_idx]
                    start_label = get_pin_label(start_idx)
                    end_label = get_pin_label(end_idx)

                    with st.expander(
                        f"Leg {leg_idx}: {start_label} → {end_label}",
                        expanded=False,
                    ):
                        st.caption(
                            f"{_display_km(leg['distance'])} • "
                            f"{_display_duration_minutes(leg['duration'])}"
                        )
                        st.caption("Split settings apply to this leg only, not the full journey total.")

                        if st.button("🗺️ View Leg on Map", key=f"focus_leg_{leg_idx}", use_container_width=True):
                            leg_route = get_route(
                                [start_pin_data["lat"], start_pin_data["lon"]],
                                [end_pin_data["lat"], end_pin_data["lon"]],
                            )
                            leg_points = _route_points_from_route_data(leg_route)
                            if not leg_points:
                                leg_points = [
                                    [start_pin_data["lat"], start_pin_data["lon"]],
                                    [end_pin_data["lat"], end_pin_data["lon"]],
                                ]

                            _fit_map_to_points(leg_points)
                            st.success(f"Showing {start_label} → {end_label}")
                            st.rerun()

                        split_mode = st.selectbox(
                            f"Split mode for leg {leg_idx}",
                            ["By Distance", "By Hours"],
                            key=f"split_mode_leg_{leg_idx}",
                        )

                        if split_mode == "By Distance":
                            target_value = st.number_input(
                                "Distance per segment (km)",
                                min_value=1.0,
                                max_value=200.0,
                                value=20.0,
                                step=1.0,
                                key=f"split_target_distance_leg_{leg_idx}",
                            )
                            break_count = max(0, math.ceil(leg["distance"] / target_value) - 1)
                        else:
                            target_value = st.number_input(
                                "Hours per segment",
                                min_value=0.5,
                                max_value=8.0,
                                value=1.0,
                                step=0.5,
                                key=f"split_target_hours_leg_{leg_idx}",
                            )
                            break_count = max(0, math.ceil(leg["duration"] / (target_value * 60.0)) - 1)

                        if st.button(
                            f"Generate Breakpoints + Nearby ({break_count})",
                            key=f"generate_breaks_leg_{leg_idx}",
                            use_container_width=True,
                        ):
                            leg_route = get_route(
                                [start_pin_data["lat"], start_pin_data["lon"]],
                                [end_pin_data["lat"], end_pin_data["lon"]],
                            )
                            route_points = _route_points_from_route_data(leg_route)
                            breakpoints = _breakpoints_from_route_points(route_points, break_count, leg_idx)

                            if not breakpoints:
                                breakpoints = generate_breakpoints(
                                    [start_pin_data["lat"], start_pin_data["lon"]],
                                    [end_pin_data["lat"], end_pin_data["lon"]],
                                    break_count,
                                )

                            enriched = []
                            for breakpoint in breakpoints:
                                auto_label = _next_break_stop_label()
                                _, added_idx = add_pin(
                                    lat=breakpoint["lat"],
                                    lon=breakpoint["lon"],
                                    label=auto_label,
                                    category="Proposed Break",
                                )
                                if added_idx is not None:
                                    set_pin_role(added_idx, "STOP")
                                    st.session_state.pin_labels[f"pin_{added_idx}"] = auto_label

                                nearby = get_nearby_places(
                                    breakpoint["lat"], breakpoint["lon"], st.session_state.search_radius_km
                                )
                                enriched.append(
                                    {
                                        "lat": breakpoint["lat"],
                                        "lon": breakpoint["lon"],
                                        "name": breakpoint["name"],
                                        "nearby": nearby,
                                        "nearby_count": sum(len(items) for items in nearby.values()),
                                    }
                                )
                            st.session_state.generated_leg_breakpoints[str(leg_idx)] = enriched
                            _refresh_breakpoint_route(waypoint_sequence)

                            if st.session_state.breakpoint_route_data:
                                breakpoint_count = max(0, len(st.session_state.breakpoint_waypoints) - len(waypoint_sequence))
                                st.session_state.journey_route_display_mode = "Breakpoint-Enhanced Route"
                                st.success(
                                    f"Generated {len(enriched)} breakpoints with nearby places. "
                                    f"Route updated through {breakpoint_count} breakpoints."
                                )
                            else:
                                st.success(f"Generated {len(enriched)} breakpoints with nearby places.")
                            st.rerun()

                        generated = st.session_state.generated_leg_breakpoints.get(str(leg_idx), [])
                        if generated:
                            for bp_idx, breakpoint in enumerate(generated, start=1):
                                st.caption(
                                    f"{breakpoint['name']} • {breakpoint['lat']:.4f}, {breakpoint['lon']:.4f}"
                                )
                                st.caption(f"Nearby captured: {breakpoint['nearby_count']} places")
                                if st.button(
                                    "🔎 Focus Breakpoint",
                                    key=f"focus_breakpoint_{leg_idx}_{bp_idx}",
                                    use_container_width=True,
                                ):
                                    focus_on_location_and_refresh_nearby(
                                        breakpoint["lat"], breakpoint["lon"]
                                    )
                                    st.rerun()
                                st.markdown("---")
