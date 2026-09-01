# PSC Stock Control — Product Requirements Document

## Original problem statement
PSC Stock Control is a small offline-friendly stock control app for batteries, inverters, and trolleys. Movements (inward/outward) support user-selected dates; history is sorted by movement date. The user is running it on **one Windows PC, fully offline, no Docker**.

## Current architecture (Feb 2026)
- **Frontend**: React 19 (CRA + craco). Built once with `npm run build` and served as static files by the backend.
- **Backend**: FastAPI (async, motor). On startup it also mounts `frontend/build` if present, so one Python process serves both API and UI on the same port.
- **DB**: MongoDB Community Server, running as a Windows Service on the same PC.
- **Data safety**: `SEED_DEMO_DATA=false` in `.env` — production installs come up empty.

## Deployment
No Docker. No cloud. The user runs it on a single Windows PC:
- `windows/Setup-Once.bat` — installs backend/frontend deps, builds frontend.
- `windows/Start-PSC.bat` — starts uvicorn (which serves the built frontend), opens browser.
- `windows/Stop-PSC.bat` — clean stop.
- Full step-by-step guide: `WINDOWS_SETUP.md` (covers desktop icon, auto-start on boot, LAN access, firewall, backups).

## What's implemented
- **[Feb 2026]** Removed all Docker artefacts (Dockerfiles, compose, nginx, AWS + old Windows guides).
- **[Feb 2026]** Backend now serves the React build itself (`StaticFiles` + SPA catch-all) when `frontend/build` exists — single process on port 8000.
- **[Feb 2026]** Windows batch scripts + `WINDOWS_SETUP.md` written for a true "double-click to run" experience.
- Movement date picker, sorted history, clean-install DB state (from earlier sessions).

## Prioritized backlog
- **P1** CSV Export of filtered History.
- **P1** Bulk backdate on multiple older movements.
- **P1** Low-stock banner when any product drops below its reorder level.
- **P2** Saved Views (pinned filter combos).
- **P2** Split `App.js` (~1255 lines) into `History.jsx`, `TransactionModal.jsx`, `Catalog.jsx`.

## Files of reference
- `backend/server.py` — API + optional SPA mount.
- `frontend/src/App.js` — all UI (needs splitting eventually).
- `windows/*.bat`, `WINDOWS_SETUP.md` — local Windows deployment.
