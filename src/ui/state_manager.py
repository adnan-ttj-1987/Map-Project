import json
import streamlit as st


DEFAULT_CENTER = [2.7258, 101.9424]
DEFAULT_ZOOM = 12


SESSION_DEFAULTS = {
    "map_center": lambda: DEFAULT_CENTER.copy(),
    "zoom": lambda: DEFAULT_ZOOM,
    "route_start": lambda: None,
    "route_end": lambda: None,
    "captured_pins": lambda: [],
    "pin_roles": lambda: {},
    "pin_labels": lambda: {},
    "pin_categories": lambda: {},
    "start_location": lambda: "",
    "end_location": lambda: "",
    "route_distance": lambda: None,
    "route_duration": lambda: None,
    "location_info": lambda: None,
    "show_location_debug": lambda: False,
    "show_location_info": lambda: True,
    "sidebar_collapsed": lambda: False,
    "nearby_places": lambda: {},
    "show_nearby_places": lambda: False,
    "search_radius_km": lambda: 1.0,
    "search_candidates": lambda: [],
    "search_candidate_query": lambda: "",
    "search_use_malaysia_bias": lambda: True,
    "nearby_sort_mode": lambda: "Smart (rating + distance)",
    "selected_pins_for_route": lambda: [],
    "multi_waypoint_route": lambda: None,
    "nearby_display_mode": lambda: "By Category",
    "generated_leg_breakpoints": lambda: {},
    "breakpoint_waypoints": lambda: [],
    "breakpoint_route_data": lambda: None,
    "journey_route_display_mode": lambda: "Base Route",
    "journey_signature": lambda: None,
}


def init_state() -> None:
    for key, default_factory in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_factory()



def _pin_key(idx: int) -> str:
    return f"pin_{idx}"



def _reindex_pin_dict(existing: dict, removed_idx: int) -> dict:
    shifted = {}
    for key, value in existing.items():
        if not key.startswith("pin_"):
            continue
        idx = int(key.split("_")[1])
        if idx == removed_idx:
            continue
        new_idx = idx - 1 if idx > removed_idx else idx
        shifted[_pin_key(new_idx)] = value
    return shifted



def invalidate_journey_state() -> None:
    st.session_state.selected_pins_for_route = []
    st.session_state.multi_waypoint_route = None
    st.session_state.generated_leg_breakpoints = {}
    st.session_state.breakpoint_waypoints = []
    st.session_state.breakpoint_route_data = None
    st.session_state.journey_route_display_mode = "Base Route"
    st.session_state.journey_signature = None



def clear_all_pins() -> None:
    st.session_state.captured_pins = []
    st.session_state.pin_roles = {}
    st.session_state.pin_labels = {}
    st.session_state.pin_categories = {}
    invalidate_journey_state()


def add_pin(
    lat: float,
    lon: float,
    label: str | None = None,
    category: str | None = None,
) -> tuple[bool, int | None]:
    new_pin = {"lat": lat, "lon": lon}
    for existing_idx, existing in enumerate(st.session_state.captured_pins):
        if existing == new_pin:
            return False, existing_idx

    st.session_state.captured_pins.append(new_pin)
    new_idx = len(st.session_state.captured_pins) - 1
    key = _pin_key(new_idx)
    st.session_state.pin_labels[key] = label or f"Pin {new_idx + 1}"
    if category:
        st.session_state.pin_categories[key] = category
    else:
        st.session_state.pin_categories.pop(key, None)

    invalidate_journey_state()
    return True, new_idx



def remove_pin_at(idx: int) -> None:
    st.session_state.captured_pins.pop(idx)
    st.session_state.pin_roles = _reindex_pin_dict(st.session_state.pin_roles, idx)
    st.session_state.pin_labels = _reindex_pin_dict(st.session_state.pin_labels, idx)
    st.session_state.pin_categories = _reindex_pin_dict(st.session_state.pin_categories, idx)
    st.session_state.selected_pins_for_route = [
        i - 1 if i > idx else i
        for i in st.session_state.selected_pins_for_route
        if i != idx
    ]
    invalidate_journey_state()



def set_pin_role(idx: int, role: str | None) -> bool:
    key = _pin_key(idx)
    current_role = st.session_state.pin_roles.get(key)

    if role is None:
        st.session_state.pin_roles.pop(key, None)
        changed = current_role is not None
    else:
        normalized = role.lower()
        st.session_state.pin_roles[key] = normalized
        changed = current_role != normalized

    if changed:
        invalidate_journey_state()

    return changed



def journey_signature_for_waypoints(waypoint_sequence: list[int]) -> str:
    signature_parts = []
    for idx in waypoint_sequence:
        pin = st.session_state.captured_pins[idx]
        signature_parts.append(f"{idx}:{pin['lat']:.6f}:{pin['lon']:.6f}")

    role_items = sorted(st.session_state.pin_roles.items())
    role_str = "|".join([f"{k}:{v}" for k, v in role_items])
    return f"wps={'|'.join(signature_parts)};roles={role_str}"



def sync_journey_state(waypoint_sequence: list[int]) -> bool:
    if not st.session_state.multi_waypoint_route:
        return False

    current_signature = journey_signature_for_waypoints(waypoint_sequence)
    stored_signature = st.session_state.journey_signature
    if stored_signature == current_signature:
        return False

    invalidate_journey_state()
    return True



def set_journey_signature(waypoint_sequence: list[int]) -> None:
    st.session_state.journey_signature = journey_signature_for_waypoints(waypoint_sequence)



def get_state_snapshot() -> dict:
    snapshot = {}
    for key in sorted(st.session_state.keys()):
        value = st.session_state[key]
        if isinstance(value, (str, int, float, bool, type(None))):
            snapshot[key] = value
        elif isinstance(value, (list, dict)):
            try:
                json.dumps(value)
                snapshot[key] = value
            except Exception:
                snapshot[key] = str(value)
        else:
            snapshot[key] = str(value)

    captured = st.session_state.get("captured_pins", [])
    roles = st.session_state.get("pin_roles", {})
    role_counts = {"start": 0, "stop": 0, "end": 0}
    for role in roles.values():
        if role in role_counts:
            role_counts[role] += 1

    snapshot["pin_count"] = len(captured)
    snapshot["pin_role_counts"] = role_counts
    return snapshot
