from src.ui.details.nearby_section import render_nearby_places_section
from src.ui.details.pins_journey_section import render_build_journey_section, render_pins_section


# Backward-compatible entrypoints for existing imports.
def render_status_footer() -> None:
    # Intentionally disabled based on user request: no value-add status section.
    return


__all__ = [
    "render_nearby_places_section",
    "render_pins_section",
    "render_build_journey_section",
    "render_status_footer",
]
