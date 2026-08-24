# PSC Stock Control — Product Doc

## Problem Statement (original)
Production-ready web app for an inverter battery distributor. Must be traceable end-to-end: what came in, from whom, when, which brand/model, how many, where it went, which dealer received it, how much remains. Later scoped down by user to a no-login single-location admin dashboard focused on speed and traceability.

## Users
- Owner/Admin (self) — main daily user, records movements, checks stock, plans reorders.

## Latest scope (Iteration 4, Feb 2026)
- Single-location model, no login, no money/cost display.
- Product types: Battery, Inverter, Trolley.
- Cart-style transaction UX (multi-item stock in/out).
- Full traceability via ledger + editable transactions with audit trail and delta-based recalculation.

## Implemented so far
- Backend (FastAPI + Motor/MongoDB): /api/bootstrap, /api/stock, /api/dashboard, /api/ledger, /api/masters/{kind}, /api/products (POST/DELETE), /api/transactions (POST/PUT with delta math), /api/dealers/{id}/profile, /api/suppliers/{id}/profile, /api/admin/reset. Seed marker in db.system so reset stays reset.
- Frontend (React): Dashboard (big Stock In/Out, clickable analytics cards, What to order next + Top movers, expandable brand cards, recent activity), Current Stock with search + brand/type/status filters, History with search + kind filter, Dealers directory with search, Suppliers directory with search, Brands with drill-in per brand + add/delete products, Settings with reset, cart-style transaction modal (no quick-add clutter), Sidebar collapse (desktop) + mobile hamburger overlay.

## Backlog (P1)
- Dealer/supplier detail: exportable ledger (PDF/Excel).
- Attach documents (invoice PDFs) to a movement.
- Auto-suggest reorder quantities per product beyond the current heuristic.
- Simple payments tracking (invoice amount, paid, due date) once user asks for it.

## Backlog (P2)
- Serial-number tracking for warranty-critical batteries.
- Returns management (dealer / supplier / damaged / defective bins).
- Multi-user access with roles.
