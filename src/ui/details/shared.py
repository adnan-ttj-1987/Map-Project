import streamlit as st

from src.ui.state_manager import add_pin
from src.utils.nearby_places_utils import get_nearby_places


def pin_key(idx: int) -> str:
    return f"pin_{idx}"


def default_pin_label(idx: int) -> str:
    return f"Pin {idx + 1}"


def get_pin_label(idx: int) -> str:
    return st.session_state.pin_labels.get(pin_key(idx), default_pin_label(idx))


def capture_pin(
    lat: float,
    lon: float,
    label: str | None = None,
    category: str | None = None,
) -> None:
    add_pin(lat=lat, lon=lon, label=label, category=category)


def reindex_pin_dict(existing: dict, removed_idx: int) -> dict:
    shifted = {}
    for key, value in existing.items():
        if not key.startswith("pin_"):
            continue
        idx = int(key.split("_")[1])
        if idx == removed_idx:
            continue
        new_idx = idx - 1 if idx > removed_idx else idx
        shifted[pin_key(new_idx)] = value
    return shifted


def focus_on_location_and_refresh_nearby(lat: float, lon: float) -> None:
    st.session_state.map_center = [lat, lon]
    st.session_state.zoom = 16
    st.session_state.nearby_places = get_nearby_places(
        lat, lon, st.session_state.search_radius_km
    )
    st.session_state.show_nearby_places = True


def generate_breakpoints(start: list[float], end: list[float], count: int) -> list[dict]:
    if count <= 0:
        return []

    points = []
    start_lat, start_lon = start
    end_lat, end_lon = end

    for idx in range(1, count + 1):
        ratio = idx / (count + 1)
        points.append(
            {
                "lat": start_lat + ((end_lat - start_lat) * ratio),
                "lon": start_lon + ((end_lon - start_lon) * ratio),
                "name": f"Break {idx}",
            }
        )

    return points
