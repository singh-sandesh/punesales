# PSC Stock Control — PRD

## Original problem statement
Stock control app for a battery/inverter/trolley shop (React + FastAPI + MongoDB). User requested: movement date on Stock In/Out, History organized by that date, date range filter on History, wipe demo data so app starts fresh, and an AWS EC2 deployment guide.

## Core requirements
1. "Stock In" and "Stock Out" forms have a required date picker.
2. Selected date is persisted per transaction.
3. History is sorted by movement date, newest first.
4. History supports a date range filter (from / to + presets).
5. Production installs start empty — no demo data.
6. Documented AWS EC2 deployment path.

## Architecture
- Backend: FastAPI (`/app/backend/server.py`), MongoDB (`transactions`, `brands`, `products`, `suppliers`, `dealers`, `inventory`, `system`).
- Frontend: React (`/app/frontend/src/App.js`) + CSS in `psc-overrides.css`.

## Data model
`transactions`:
- `movement_date` (`YYYY-MM-DD`, user-selected, defaults to today).
- `created_at` (ISO timestamp of when the record was logged).

## API
- `POST /api/transactions`, `PUT /api/transactions/{id}` accept optional `movement_date`.
- `GET /api/ledger` returns `movement_date` and sorts by `(movement_date, created_at)` desc.
- `POST /api/admin/reset` wipes business collections and marks the DB as seeded so demo data never re-appears.

## Env variables
- `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS` — required.
- `SEED_DEMO_DATA` — set `true` for a demo box (Exide/Massimo/Microtek + fake dealers); leave unset in production and the DB will start empty.

## Implemented (Feb 2026)
- Movement date field on Stock In / Stock Out modals.
- Movement date persisted; History sorted by it.
- Date range filter on History (6 presets + manual from/to + clear + summary bar).
- `SEED_DEMO_DATA` env gate — production DBs start empty.
- Wiped the current MongoDB (0 dealers, 0 units, 0 transactions) so the shop can start fresh.
- Restored missing `.env` files; removed dead lucide imports that were failing the build.
- Deployment doc: `/app/AWS_EC2_SETUP.md` (EC2 + MongoDB + Nginx + PM2 + HTTPS + S3 backups).
- Pytest suite added at `/app/backend/tests/test_stock_flow.py` (15/15 pass).
- Full Dockerization: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`, `.env.example`.
- Local offline deployment doc: `/app/LOCAL_WINDOWS_SETUP.md` (Docker Desktop on Windows, localhost + LAN access via firewall rule, works fully offline after first build).

## Verification
Testing agent iteration_7: **100% backend (15/15), 100% frontend flows**. No open issues.

## Backlog (P2)
- Export filtered History to CSV.
- Show movement date on Dashboard's "Latest movements" widget.
- Bulk backdate multiple older movements at once.
- Modularise `App.js` (now ~1255 lines) into `History.jsx`, `TransactionModal.jsx`, `Catalog.jsx`.
