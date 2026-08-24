# PSC Stock Control PRD

## Original problem statement
Build a one-stop inverter battery distribution stock manager that quickly tracks how much comes in and goes out, and traces battery movement by brand, model, warehouse, supplier, and dealer. The user clarified: no login, one admin workspace, focused on practical stock control rather than a full accounting ERP.

## Architecture decisions
- React frontend with a focused, simple blue-and-white workspace UI.
- FastAPI backend with MongoDB collections for brands, products, suppliers, dealers, warehouses, inventory, and transactions.
- Dynamic master records and transaction APIs; stock is calculated from inventory movement records.
- No authentication by explicit user choice.
- Frontend calls only `REACT_APP_BACKEND_URL`; backend uses only existing `MONGO_URL` and `DB_NAME`.

## User personas
- Owner: wants an immediate, accurate view of available stock and business movement.
- Warehouse/admin operator: needs fast stock-in and stock-out entry with dealer/supplier traceability.

## Core requirements (static)
- View current stock by brand, model, and warehouse.
- Record inward receipts and outward dealer dispatches quickly.
- Prevent outward transactions from creating negative available stock.
- Keep a movement ledger with transaction IDs, quantities, values, references, and timestamps.
- Support dynamic brands and battery products.
- Provide clear KPIs, low-stock indicators, search, and brand filters.

## What's implemented
### 2026-02-21 — Focused stock workspace MVP
- Replaced the starter screen with VoltPulse dashboard, current stock view, and movement ledger.
- Added seeded Exide, Massimo, and Microtek brands; nine battery models; suppliers, dealers, warehouses, and realistic inventory positions.
- Added working stock inward/outward posting, automatic inventory updates, negative-stock rejection, transaction history, search, filters, and mobile responsive layout.
- Added quick battery-model creation modal and correct inventory valuation from product purchase rates.

### 2026-02-21 — PSC workflow expansion
- Renamed the product to PSC and refreshed the UI with a clean blue-and-white theme.
- Added multi-model movement entry, quick supplier/dealer/warehouse creation with automatic selection, and dealer directory/profile views.
- Added dealer opening balance plus dispatch totals for outstanding balance, brand/model preference summaries, and dispatch history.
- Added validation so an empty movement cannot be posted.

## Prioritized backlog
- P0: Add quick-add brand directly inside stock movement forms and connect new brands to product creation.
- P0: Add multi-line transactions so one receipt/dispatch can contain many models.
- P1: Add returns, damaged/defective buckets, transfers, adjustments, and opening stock.
- P1: Add dealer and supplier profile pages with movement history.
- P1: Add date/warehouse/party filters and exportable filtered ledger.
- P2: Add serial number traceability, attachments, drafts, reversal workflow, and audit history.
- P2: Add aging, fast/slow movement reports, printable documents, and company settings.

## Remaining next tasks
1. Build quick-add contextual master modals and automatically select new records.
2. Support multi-item inward/outward forms with duplicate reference warnings.
3. Add stock transfers, returns, adjustments, and physical reconciliation.
4. Expand dashboard analytics and filtered exports after the core movement flow is complete.