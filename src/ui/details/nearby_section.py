import streamlit as st

from src.ui.details.shared import capture_pin, focus_on_location_and_refresh_nearby


def _render_nearby_place_card(place: dict, button_key: str, category: str) -> None:
    distance = place.get("distance", "?")
    name = place.get("name", "Unknown Place")

    detail_parts = [f"{distance} km"]
    if place.get("halal") is not None:
        detail_parts.append("✅ Halal" if place["halal"] else "❌ Non-Halal")

    st.markdown(f"**{name}**")
    st.caption(f"{category} • {' • '.join(detail_parts)}")

    if st.button("📍 Focus + Capture", key=button_key, use_container_width=True):
        capture_pin(
            place["lat"],
            place["lon"],
            label=place["name"],
            category=category,
        )
        focus_on_location_and_refresh_nearby(place["lat"], place["lon"])
        st.success("✅ Place added to captured pins")
        st.rerun()


def render_nearby_places_section() -> None:
    if not st.session_state.show_nearby_places:
        return

    st.divider()

    with st.expander("🏘️ Nearby Places Around This Area", expanded=True):
        nearby = st.session_state.nearby_places or {}
        if not nearby:
            st.warning("⚠️ No nearby places found for this location. Try a different area.")
            return

        total_places = sum(len(places) for places in nearby.values())
        st.info(f"📍 Found {total_places} interesting places nearby")

        display_mode = st.selectbox(
            "Display Mode",
            ["By Category", "By Distance (Flat)"],
            index=0 if st.session_state.nearby_display_mode == "By Category" else 1,
            key="nearby_display_mode_select",
        )
        st.session_state.nearby_display_mode = display_mode

        if display_mode == "By Category":
            st.session_state.nearby_sort_mode = st.selectbox(
                "Sort Category Items",
                ["Smart (rating + distance)", "Distance (nearest first)"],
                index=0 if st.session_state.nearby_sort_mode == "Smart (rating + distance)" else 1,
                key="nearby_sort_mode_select",
            )
        else:
            st.caption("Flat mode is sorted by distance (nearest first).")

        if display_mode == "By Distance (Flat)":
            flat_places = []
            for category, places in nearby.items():
                for place in places:
                    place_copy = dict(place)
                    place_copy["_category"] = category
                    flat_places.append(place_copy)

            flat_places = sorted(flat_places, key=lambda item: item.get("distance", 9999))

            for place_idx, place in enumerate(flat_places):
                category = place.get("_category", "Unknown")
                _render_nearby_place_card(
                    place,
                    button_key=f"nearby_flat_focus_{place_idx}_{place['lat']}_{place['lon']}",
                    category=category,
                )
                st.markdown("---")
            return

        for category in sorted(nearby.keys()):
            places = nearby[category]
            if not places:
                continue

            if st.session_state.nearby_sort_mode == "Distance (nearest first)":
                places = sorted(places, key=lambda item: item.get("distance", 9999))

            st.markdown(f"#### {category} ({len(places)} found)")
            for place_idx, place in enumerate(places):
                _render_nearby_place_card(
                    place,
                    button_key=f"nearby_group_focus_{category}_{place_idx}_{place['lat']}_{place['lon']}",
                    category=category,
                )
                st.markdown("---")
