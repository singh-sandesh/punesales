# PSC Stock Control

A small, offline-friendly stock control app (React + FastAPI + MongoDB).

## Run it on a Windows PC (no Docker)

See **[WINDOWS_SETUP.md](./WINDOWS_SETUP.md)** — install Python, Node, MongoDB, run `windows\Setup-Once.bat` once, then double-click `windows\Start-PSC.bat` (or its desktop shortcut) any time you want to use the app.

- Same PC: `http://localhost:8000`
- Other devices on your Wi-Fi: `http://<your-PC-IP>:8000`

## Project layout

```
backend/    FastAPI app (also serves the built React frontend)
frontend/   React source; `npm run build` produces frontend/build
windows/    Setup-Once.bat, Start-PSC.bat, Stop-PSC.bat
```
