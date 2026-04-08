# ADR 0002: Relocate Utility Modules into src/utils

- Status: Accepted
- Date: 2026-04-06
- Owners: T14 Map Explorer maintainers
- Supersedes: None

## Context
Most non-UI modules were utility/service helpers and were stored directly under `src/`.
As the codebase grows, mixing UI modules and utility modules at top-level makes navigation and ownership less clear.

## Decision
Move utility/service modules into `src/utils/` and update imports accordingly.

Moved modules:
- `changelog_utils.py`
- `search_utils.py`
- `location_utils.py`
- `history_utils.py`
- `route_history_utils.py`
- `nearby_places_utils.py`
- `routing_utils.py`

## Alternatives Considered
1. Keep files in `src/` and rely on naming only.
   - Pros: no import changes.
   - Cons: flatter structure becomes harder to maintain.
2. Split by domain folders (search/, routing/, nearby/).
   - Pros: strongest domain boundaries.
   - Cons: more disruptive now and may over-fragment current scope.

## Consequences
### Positive
- Cleaner separation between UI layer (`src/ui/`) and utility/services (`src/utils/`).
- Easier onboarding and file discovery.
- Better foundation for future domain-level extraction.

### Trade-offs
- Import paths changed across UI modules.
- Existing references in docs required updates.

## Compatibility and Migration
- Updated imports in UI modules and page modules from `src.<module>` to `src.utils.<module>`.
- Added `src/utils/__init__.py`.
- Runtime behavior unchanged.

## Follow-up Actions
1. Add unit tests targeting utility modules in `src/utils/`.
2. Consider future split of `src/utils/` by domain if it grows large.
3. Keep architecture docs synchronized with module moves.
