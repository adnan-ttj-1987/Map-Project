# ADR 0001: Segregate UI Details Module into Subpackage

- Status: Accepted
- Date: 2026-04-06
- Owners: T14 Map Explorer maintainers

## Context
The previous `src/ui/detail_sections.py` file accumulated mixed responsibilities:
- Nearby places rendering and interactions
- Pin management and label/role editing
- Journey building and leg-level controls
- Utility/helper functions used by multiple UI sections

This made the file harder to reason about, increased merge conflict risk, and reduced testability/readability.

## Decision
Split the details UI into a focused subpackage while preserving public compatibility:

- `src/ui/details/shared.py`
  - Shared helper functions for pin keys/labels, reindexing, focus actions, and breakpoint generation
- `src/ui/details/nearby_section.py`
  - Nearby display modes, sorting, and capture/focus actions
- `src/ui/details/pins_journey_section.py`
  - Captured pins UI, role assignment, journey construction, route summary, and leg splitting controls
- `src/ui/detail_sections.py`
  - Backward-compatible wrapper exporting the same entrypoints used by existing imports

## Consequences
### Positive
- Better separation of concerns and maintainability
- Cleaner ownership boundaries for future changes
- Easier unit-level testing by module responsibility
- Lower cognitive load for onboarding and code reviews

### Trade-offs
- Slightly more files to navigate
- Requires discipline to keep helpers in `shared.py` and avoid cross-module leakage

## Compatibility and Migration
No app-level import changes are required because `src/ui/detail_sections.py` remains as a compatibility wrapper.

## Follow-up Actions
1. Add targeted tests for `pins_journey_section` and `nearby_section` behavior.
2. Consider adding `src/journey_planner_utils.py` for polyline-aware split calculations.
3. Add ADR template (`0000-template.md`) for future architecture decisions.
