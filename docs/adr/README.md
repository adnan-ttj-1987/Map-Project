# Architecture Decision Records (ADR)

This folder tracks architecture-level decisions for T14 Map Explorer.

## How To Add A New ADR
1. Copy `0000-template.md` to a new file named `000N-short-title.md`.
2. Fill all sections (Context, Decision, Alternatives, Consequences).
3. Set status to `Proposed` during review, then `Accepted` after agreement.
4. If replacing an older decision, set `Supersedes` and mark old ADR as `Superseded`.

## ADR Index
| ID | Title | Status | Date |
|---|---|---|---|
| [0001](0001-ui-details-segregation.md) | UI details segregation into subpackage | Accepted | 2026-04-06 |
| [0002](0002-utils-module-relocation.md) | Relocate utility modules into src/utils | Accepted | 2026-04-06 |

## Notes
- Keep one decision per ADR.
- Prefer appending new ADRs over rewriting historical context.
- Use ADR IDs in pull requests and implementation notes for traceability.
