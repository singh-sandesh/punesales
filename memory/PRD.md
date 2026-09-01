# PSC Stock Control — PRD

## Original problem statement
Add a user-selectable date for when stock came in and went out, and organize the History section by that date.

## Core requirements
1. "Stock In" and "Stock Out" forms include a date picker for the movement date.
2. Selected date is persisted to the database on each transaction.
3. History view is sorted by movement date (newest first), showing the movement date as the primary date and the recorded timestamp as a subtitle.

## Architecture
- Backend: FastAPI (`/app/backend/server.py`), MongoDB (`transactions` collection).
- Frontend: React (`/app/frontend/src/App.js`).

## Data model changes
`transactions` document now includes:
- `movement_date` (string, `YYYY-MM-DD`, user-selected; defaults to today if omitted).
- `created_at` (existing ISO timestamp of when the record was logged).

## API changes
- `POST /api/transactions` and `PUT /api/transactions/{id}` accept optional `movement_date`.
- `GET /api/ledger` returns `movement_date` and sorts by `(movement_date, created_at)` desc; older records without `movement_date` fall back to `created_at[:10]`.
- Party profile endpoints surface `movement_date` as the `date` field in history and sort by it.

## Frontend changes
- `TransactionModal` (Stock In/Out) has a required date input, defaulted to today or the editing record's date.
- `History` displays movement date as the primary cell and "recorded ..." timestamp as a subtitle; sorted client-side by movement date desc as well.

## Implemented (Feb 2026)
- Movement date field on Stock In / Stock Out modals.
- Persistence in Mongo.
- Sorted History by movement date desc.
- Restored missing `/app/backend/.env` and `/app/frontend/.env` files.
- Removed unused lucide-react imports (`Battery`, `XCircle`) that broke the frontend build.

## Backlog (P2)
- Date range filter on the History page (from / to).
- Export History to CSV.
- Show movement date on Dashboard's "Latest movements" widget.
