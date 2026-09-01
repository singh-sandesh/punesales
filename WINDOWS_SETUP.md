# PSC Stock Control — Windows Local Setup (No Docker)

A completely offline, no-Docker setup for Windows 10/11.
When you're done you'll have **one desktop icon**. Double-click it → the app opens in your browser in ~5 seconds.

**Architecture (kept intentionally small):**
- **MongoDB Community Server** → runs as a Windows Service, auto-starts with Windows.
- **Python (FastAPI) backend** → also serves the pre-built React frontend on the **same port**. So only one process to launch.
- **No Node.js is needed at runtime** — Node is only used once, during setup, to build the frontend.

You'll be able to open the app at:
- `http://localhost:8000` — on the same PC
- `http://<your-PC-LAN-IP>:8000` — from any other phone/laptop on the same Wi-Fi

---

## 1. Install the three prerequisites (one-time, ~10 minutes)

Open each link, download, run the installer with the options noted.

### 1a. Python 3.11 or newer
- Download: <https://www.python.org/downloads/windows/>
- Run the installer.
- **Important:** on the first screen tick **"Add python.exe to PATH"**, then click **Install Now**.

Verify in **PowerShell** (Start menu → type "PowerShell"):
```powershell
python --version
```
Should print something like `Python 3.12.x`.

### 1b. Node.js LTS (needed only to build the frontend once)
- Download: <https://nodejs.org/en/download>
- Take the **LTS** installer. Accept all defaults.

Verify:
```powershell
node --version
npm --version
```

### 1c. MongoDB Community Server 7.x
- Download: <https://www.mongodb.com/try/download/community> (pick Platform = Windows, Package = msi).
- Run the installer.
- Choose **Complete** setup.
- **Important:** on the "Service Configuration" screen leave the default **"Install MongoDB as a Service"** ticked. This is what makes Mongo auto-start with Windows.
- You can **untick "Install MongoDB Compass"** if you don't want the GUI (it's optional).
- Finish install.

Verify:
```powershell
Get-Service MongoDB
```
Should show `Status: Running`. If not:
```powershell
Start-Service MongoDB
```

That's it. Mongo now starts every time Windows boots.

---

## 2. Put the project on your PC

Pick any folder. Recommended:
```
C:\psc-app\
```

Copy the entire project into that folder so you end up with:
```
C:\psc-app\
├── backend\
├── frontend\
├── windows\
│   ├── Setup-Once.bat
│   ├── Start-PSC.bat
│   └── Stop-PSC.bat
└── ...
```

---

## 3. Run the one-time setup

Open File Explorer, go to `C:\psc-app\windows\`, and **double-click `Setup-Once.bat`**.

It does everything for you:
1. Checks that Python, Node and MongoDB are installed.
2. Creates a Python virtual environment at `backend\.venv`.
3. Installs the backend Python packages.
4. Writes a default `backend\.env` (points to local Mongo, demo data off).
5. Writes `frontend\.env` with `REACT_APP_BACKEND_URL=` (empty → same origin).
6. Runs `npm install` and `npm run build` — this produces `frontend\build\`.

First run takes **~5–8 minutes**. When it says `Setup complete.`, you're done.

*(You only ever run this again if you change the code or update packages.)*

---

## 4. Start the app — one click

Double-click **`C:\psc-app\windows\Start-PSC.bat`**.

You'll see a small window that says "Starting PSC Stock Control…", then your default browser opens on `http://localhost:8000` and the app is live.

To stop everything: double-click **`Stop-PSC.bat`**.

---

## 5. Make a desktop icon (the real "click to open" experience)

1. Open `C:\psc-app\windows\`.
2. **Right-click `Start-PSC.bat` → Send to → Desktop (create shortcut)**.
3. On your desktop, right-click the new shortcut → **Rename** → call it `PSC Stock Control`.
4. (Optional) Right-click → **Properties** → **Change Icon…** → **Browse…** → pick an icon from `C:\Windows\System32\SHELL32.dll` (there's a warehouse/box one in there) → **OK** → **Apply**.
5. (Optional) Right-click → **Properties** → next to **Run**, choose **Minimized** so the launcher window doesn't pop up.

Now double-clicking the desktop icon just opens the app in your browser. Done.

### Pin to Taskbar / Start (optional)
Right-click the desktop shortcut → **Show more options** → **Pin to taskbar** or **Pin to Start**.

### Auto-start with Windows (optional)
1. Press `Win + R`, type `shell:startup`, press Enter.
2. Copy your `PSC Stock Control` desktop shortcut into the folder that opens.
3. Now every time you log in to Windows, the app is already running.

---

## 6. Open it from other devices on your network

The launcher already binds to `0.0.0.0`, so all you need is:

### 6a. Find your PC's LAN IP
In PowerShell:
```powershell
ipconfig
```
Look for the "IPv4 Address" under your Wi-Fi/Ethernet adapter, e.g. `192.168.1.42`.

### 6b. Open Windows Firewall for port 8000 (one time)
Run PowerShell **as Administrator** and paste:
```powershell
New-NetFirewallRule -DisplayName "PSC Stock Control (8000)" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```
This opens port 8000 **only on your private network** (safe for home/office Wi-Fi).

### 6c. Visit from any phone/laptop on the same Wi-Fi
```
http://192.168.1.42:8000
```
(replace with your PC's actual IP).

If nothing loads, check:
- Both devices are on the **same Wi-Fi** (not "guest" — many routers block guest → LAN).
- Your Wi-Fi is set to **Private** network in Windows (Settings → Network → your Wi-Fi → Network profile type: Private).

---

## 7. Everyday use

| What you want to do | Do this |
| --- | --- |
| Open the app | Double-click the desktop icon |
| Stop the app | Double-click `Stop-PSC.bat` |
| Reboot the PC | Nothing — Mongo auto-starts, and the app will start too if you set up section 5's auto-start |
| See if it's running | Open `http://localhost:8000` in a browser |
| Change the port (if 8000 is taken) | Open `windows\Start-PSC.bat` and `Stop-PSC.bat` in Notepad, change `set "PSC_PORT=8000"` to another number (e.g. 8080), and re-run the firewall rule with the new port |

---

## 8. Reset back to an empty database

Everything is stored in your local Mongo. To wipe it clean:

```powershell
& "C:\Program Files\MongoDB\Server\7.0\bin\mongosh.exe" psc_stock --eval "db.dropDatabase()"
```
(Path may say `Server\8.0\bin` depending on your Mongo version.)

Or via the app: it exposes an admin endpoint you can hit from the browser once:
```
http://localhost:8000/api/admin/reset
```
(POST — easiest from Postman or the built-in reset button if you add one to the UI).

Because `SEED_DEMO_DATA=false`, the app comes back with **0 brands, 0 dealers, 0 units**.

---

## 9. Backups (recommended — it's your real data)

Everything is inside one Mongo folder. Back it up whenever you want:

**Manual copy** (fine for weekly backups):
1. Stop the app: `Stop-PSC.bat`
2. Stop Mongo: `Stop-Service MongoDB` (in an admin PowerShell)
3. Copy `C:\Program Files\MongoDB\Server\7.0\data\` to a USB stick or another drive.
4. Start Mongo again: `Start-Service MongoDB`

**Cleaner dump** (works while Mongo is running):
```powershell
& "C:\Program Files\MongoDB\Server\7.0\bin\mongodump.exe" --db psc_stock --out D:\psc-backup\%DATE%
```

Restore later with:
```powershell
& "C:\Program Files\MongoDB\Server\7.0\bin\mongorestore.exe" --db psc_stock D:\psc-backup\<DATE>\psc_stock
```

---

## 10. Troubleshooting

- **`Setup-Once.bat` says "Python is not in PATH"** → reinstall Python and tick "Add python.exe to PATH" on the first screen. Or add it manually via Settings → System → About → Advanced system settings → Environment Variables.
- **`npm install` fails** → run `Setup-Once.bat` again; the first run sometimes trips on network hiccups.
- **`Start-PSC.bat` closes and browser shows "can't be reached"** → open the minimized `PSC-Backend` window in the taskbar to read the Python error. Most common cause: Mongo service is stopped. Fix: `Start-Service MongoDB` in admin PowerShell.
- **Port 8000 already in use** → change the port in both `Start-PSC.bat` and `Stop-PSC.bat` (see section 7).
- **Other devices can't reach it, but `localhost` works** → firewall rule from section 6b is missing, or your Wi-Fi profile is Public (change it to Private).
- **"MongoDB service won't start"** → open Event Viewer or run `mongod --dbpath "C:\Program Files\MongoDB\Server\7.0\data"` from an admin PowerShell to see the real error. Usually a permissions issue on the data folder.

---

That's it — no cloud, no domain, no monthly bill, no Docker. Everything runs directly on your PC and keeps working with no internet at all.
