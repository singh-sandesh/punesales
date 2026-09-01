# PSC Stock Control — PRD

## Original problem statement
Add a user-selectable date for when stock came in and went out, and organize the History section by that date. Later: add from/to date filters on History for quick period pulls.

## Core requirements
1. "Stock In" and "Stock Out" forms include a date picker for the movement date.
2. Selected date is persisted to the database on each transaction.
3. History view is sorted by movement date (newest first).
4. History supports date range filtering: from/to inputs plus quick-pick presets (Today, This week, This month, Last month, Last 30 days, All time).

## Architecture
- Backend: FastAPI (`/app/backend/server.py`), MongoDB (`transactions` collection).
- Frontend: React (`/app/frontend/src/App.js`), CSS in `psc-overrides.css`.

## Data model
`transactions` document:
- `movement_date` (string, `YYYY-MM-DD`, user-selected; defaults to today if omitted).
- `created_at` (ISO timestamp of when the record was logged).

## API
- `POST /api/transactions` and `PUT /api/transactions/{id}` accept optional `movement_date`.
- `GET /api/ledger` returns `movement_date` and sorts by `(movement_date, created_at)` desc; legacy rows fall back to `created_at[:10]`.
- Party profile endpoints surface `movement_date` as the `date` field.

## Frontend
- `TransactionModal` (Stock In/Out): required date input, defaults to today or the editing record's date.
- `History`:
  - Primary date is the movement date; "recorded …" timestamp as subtitle.
  - Client-side date range filter (`from`, `to`) with 6 preset chips.
  - Range summary bar showing count of movements and total units in the current filter.

## Implemented (Feb 2026)
- Movement date field on Stock In / Stock Out modals.
- Persistence in Mongo; sorted History by movement date desc.
- Date range filter (presets + from/to + clear + summary bar).
- Restored missing `/app/backend/.env` and `/app/frontend/.env`.
- Removed unused lucide-react imports (`Battery`, `XCircle`) that were breaking the frontend build.

## Backlog (P2)
- Export filtered History to CSV.
- Show movement date on Dashboard's "Latest movements" widget.
- Bulk backdate multiple older movements at once.
