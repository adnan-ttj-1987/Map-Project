import html

import folium
import streamlit as st
from streamlit_folium import st_folium

from src.ui.state_manager import add_pin
from src.utils.nearby_places_utils import get_nearby_places
from src.utils.routing_utils import add_route_to_map, add_multi_waypoint_route_to_map, get_route


CATEGORY_COLORS = {
    "Education": "green",
    "Food & Dining": "orange",
    "Attractions": "cadetblue",
    "Accommodation": "purple",
    "Transport": "darkblue",
    "Amenities": "gray",
}

CATEGORY_ICONS = {
    "Education": "graduation-cap",
    "Food & Dining": "utensils",
    "Attractions": "landmark",
    "Accommodation": "hotel",
    "Transport": "bus",
    "Amenities": "info-circle",
}


def _get_pin_label(idx: int) -> str:
    key = f"pin_{idx}"
    return st.session_state.pin_labels.get(key, f"Pin {idx + 1}")


def _build_pin_popup_and_tooltip_html(
    pin_name: str,
    role_label: str,
    lat: float,
    lon: float,
    category: str | None,
) -> tuple[str, folium.Tooltip]:
    safe_name = html.escape(pin_name)
    safe_role = html.escape(role_label)
    safe_category = html.escape(category) if category else "N/A"

    popup_html = (
        "<div style='min-width:230px;max-width:260px;'>"
        f"<b>{safe_name}</b><br/>"
        f"{safe_role}<br/>"
        f"Category: {safe_category}<br/>"
        f"Lat/Lon: {lat:.5f}, {lon:.5f}<br/>"
        "</div>"
    )

    tooltip_html = (
        "<div style='min-width:200px;max-width:240px;'>"
        f"<b>{safe_name}</b><br/>"
        f"{safe_role}<br/>"
        f"{safe_category}"
        "</div>"
    )

    return popup_html, folium.Tooltip(tooltip_html, sticky=True)
def render_interactive_map() -> None:
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.zoom,
        control_scale=True,
        prefer_canvas=True,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps",
    )

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Street Map",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)

    # Show detected current location as a blue marker with detail tooltip.
    location_info = st.session_state.get("location_info")
    if location_info and location_info.get("coords"):
        loc_lat, loc_lon = location_info["coords"]
        city = location_info.get("city", "Unknown")
        country = location_info.get("country", "Unknown")
        source = location_info.get("source", "Unknown")
        accuracy = location_info.get("accuracy", "Unknown")
        detail_text = f"{city}, {country} | Source: {source} | Accuracy: {accuracy}"

        folium.Marker(
            location=[loc_lat, loc_lon],
            popup=(
                f"📍 My Location<br/>"
                f"City: {city}<br/>"
                f"Country: {country}<br/>"
                f"Source: {source}<br/>"
                f"Accuracy: {accuracy}<br/>"
                f"Lat/Lon: {loc_lat:.6f}, {loc_lon:.6f}"
            ),
            tooltip=detail_text,
            icon=folium.Icon(color="blue", icon="user", prefix="fa"),
        ).add_to(m)

    # Handle multi-waypoint route display (priority over single-point routes)
    if st.session_state.multi_waypoint_route:
        try:
            breakpoint_route = st.session_state.get("breakpoint_route_data")
            breakpoint_waypoints = st.session_state.get("breakpoint_waypoints", [])
            display_mode = st.session_state.get("journey_route_display_mode", "Base Route")

            if (
                display_mode == "Breakpoint-Enhanced Route"
                and breakpoint_route
                and breakpoint_waypoints
            ):
                waypoints = [[wp["lat"], wp["lon"]] for wp in breakpoint_waypoints]
                waypoint_labels = [wp.get("label", "Waypoint") for wp in breakpoint_waypoints]
                route_to_draw = breakpoint_route
            else:
                # Get waypoints from selected pins
                waypoints = [
                    [st.session_state.captured_pins[idx]["lat"], st.session_state.captured_pins[idx]["lon"]]
                    for idx in st.session_state.selected_pins_for_route
                ]
                waypoint_labels = [_get_pin_label(idx) for idx in st.session_state.selected_pins_for_route]
                route_to_draw = st.session_state.multi_waypoint_route
            
            if waypoints:
                add_multi_waypoint_route_to_map(
                    m,
                    waypoints,
                    route_to_draw,
                    waypoint_labels=waypoint_labels,
                )
        except Exception as exc:
            st.warning(f"⚠️ Multi-route display error: {str(exc)}")
    
    # Handle single-point route display (start to end)
    elif st.session_state.route_start and st.session_state.route_end:
        try:
            route_data = get_route(st.session_state.route_start, st.session_state.route_end)
            if route_data:
                add_route_to_map(m, st.session_state.route_start, st.session_state.route_end, route_data)
        except Exception as exc:
            st.warning(f"⚠️ Route error: {str(exc)}")
    
    for idx, pin in enumerate(st.session_state.captured_pins):
        pin_role = st.session_state.pin_roles.get(f"pin_{idx}", None)

        role_color_map = {
            "start": ("green", "play", "🟢 START"),
            "stop": ("orange", "stop", "🟠 STOP"),
            "end": ("red", "flag", "🔴 END"),
        }

        if pin_role and pin_role in role_color_map:
            color, icon, label = role_color_map[pin_role]
            category_text = st.session_state.pin_categories.get(f"pin_{idx}")
        else:
            pin_category = st.session_state.pin_categories.get(f"pin_{idx}")
            if pin_category:
                color = CATEGORY_COLORS.get(pin_category, "gray")
                icon = CATEGORY_ICONS.get(pin_category, "map-pin")
                label = f"⚪ {pin_category.upper()}"
                category_text = pin_category
            else:
                color = "gray"
                icon = "map-pin"
                label = "⚪ UNASSIGNED"
                category_text = None

        pin_label = _get_pin_label(idx)
        popup_html, tooltip_html = _build_pin_popup_and_tooltip_html(
            pin_name=pin_label,
            role_label=label,
            lat=pin["lat"],
            lon=pin["lon"],
            category=category_text,
        )

        folium.Marker(
            location=[pin["lat"], pin["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=tooltip_html,
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(m)

        folium.Marker(
            location=[pin["lat"] + 0.0005, pin["lon"] + 0.0005],
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.DivIcon(html=f"""
                <div style="
                    background-color: white;
                    border: 2px solid {color};
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                    font-size: 12px;
                    white-space: nowrap;
                ">{label} {idx + 1}</div>
            """),
        ).add_to(m)

    generated_breaks = st.session_state.get("generated_leg_breakpoints", {}) or {}
    captured_pin_points = [
        (pin.get("lat"), pin.get("lon"))
        for pin in st.session_state.get("captured_pins", [])
        if isinstance(pin, dict)
    ]

    for leg_key, breakpoints in generated_breaks.items():
        if not isinstance(breakpoints, list):
            continue
        for bp_idx, breakpoint in enumerate(breakpoints, start=1):
            lat = breakpoint.get("lat")
            lon = breakpoint.get("lon")
            if lat is None or lon is None:
                continue

            already_captured = any(
                abs((cp_lat or 0) - lat) < 1e-6 and abs((cp_lon or 0) - lon) < 1e-6
                for cp_lat, cp_lon in captured_pin_points
            )
            if already_captured:
                continue

            bp_name = breakpoint.get("name", f"Break {bp_idx}")
            nearby_count = breakpoint.get("nearby_count", 0)
            safe_bp_name = html.escape(str(bp_name))

            nearby_preview = []
            nearby_data = breakpoint.get("nearby", {})
            if isinstance(nearby_data, dict):
                flattened = []
                for category_name, entries in nearby_data.items():
                    if not isinstance(entries, list):
                        continue
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        flattened.append(
                            (
                                entry.get("distance", 9999),
                                entry.get("name", "Unnamed"),
                                category_name,
                            )
                        )
                flattened.sort(key=lambda item: item[0])
                for _, place_name, category_name in flattened[:3]:
                    nearby_preview.append(
                        f"- {html.escape(str(place_name))} ({html.escape(str(category_name))})"
                    )

            nearby_preview_html = "<br/>".join(nearby_preview) if nearby_preview else "- No nearby preview"

            folium.Marker(
                location=[lat, lon],
                popup=(
                    f"🛑 {safe_bp_name}<br/>"
                    f"Leg: {leg_key}<br/>"
                    f"Nearby captured: {nearby_count}<br/>"
                    f"Top nearby:<br/>{nearby_preview_html}<br/>"
                    f"Lat/Lon: {lat:.5f}, {lon:.5f}"
                ),
                tooltip=f"Break {bp_idx} (Leg {leg_key}): {bp_name}",
                icon=folium.Icon(color="black", icon="coffee", prefix="fa"),
            ).add_to(m)

    if st.session_state.get("nearby_places"):
        if st.session_state.captured_pins:
            last_pin = st.session_state.captured_pins[-1]
            ref_point = (last_pin["lat"], last_pin["lon"])
        else:
            ref_point = tuple(st.session_state.map_center)

        for category, places in st.session_state.nearby_places.items():
            for place in places:
                try:
                    plat = place.get("lat") or place.get("latitude")
                    plon = place.get("lon") or place.get("longitude")
                    if plat is None or plon is None:
                        continue

                    name = place.get("name", "Unnamed")
                    rating = place.get("rating")
                    distance = place.get("distance")
                    safe_name = html.escape(name)
                    safe_category = html.escape(category)

                    popup_lines = [f"<b>{safe_name}</b>", f"Category: {safe_category}"]
                    if rating is not None:
                        popup_lines.append(f"⭐ {rating}")
                    if distance is not None:
                        popup_lines.append(f"{distance:.2f} km away")
                    popup_html = "<br/>".join(popup_lines)

                    tooltip_html = (
                        "<div style='min-width:200px;max-width:240px;'>"
                        f"<b>{safe_name}</b><br/>"
                        f"{safe_category}<br/>"
                        "</div>"
                    )

                    color = CATEGORY_COLORS.get(category, "red")
                    icon_name = CATEGORY_ICONS.get(category, "info-circle")

                    try:
                        folium.PolyLine(
                            locations=[ref_point, (plat, plon)],
                            color=color,
                            weight=2,
                            opacity=0.6,
                            dash_array="5,5",
                        ).add_to(m)
                    except Exception:
                        pass

                    folium.Marker(
                        location=[plat, plon],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=folium.Tooltip(tooltip_html, sticky=True),
                        icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
                    ).add_to(m)
                except Exception:
                    continue

    map_data = st_folium(
        m,
        height=600,
        key="main_map",
        use_container_width=True,
        returned_objects=["last_clicked", "last_object_clicked"],
    )

    is_marker_or_object_click = bool(
        map_data and (
            map_data.get("last_object_clicked") is not None
        )
    )
    if map_data and map_data.get("last_clicked") and not is_marker_or_object_click:
        clicked = map_data["last_clicked"]
        new_pin = {"lat": clicked["lat"], "lon": clicked["lng"]}
        added, _ = add_pin(lat=new_pin["lat"], lon=new_pin["lon"])
        if added:
            with st.spinner("🔍 Finding nearby places..."):
                nearby = get_nearby_places(
                    new_pin["lat"], new_pin["lon"], st.session_state.search_radius_km
                )
                st.session_state.nearby_places = nearby
                st.session_state.show_nearby_places = True
            st.success(f"📍 Pinned: {new_pin['lat']:.4f}, {new_pin['lon']:.4f}")
            st.rerun()
