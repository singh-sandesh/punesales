# Running PSC Stock Control Locally on Windows (Docker, No Internet Needed After Setup)

This runs the exact same Docker stack as the AWS guide (`mongo` + `backend` + `frontend`) but on your own Windows PC. Once it's up, it keeps working even if your internet goes down — everything (app + database) lives on your machine.

You'll be able to open it at:
- `http://localhost` — on the same PC
- `http://<your-pc's-LAN-IP>` — from any other phone/laptop on the same WiFi/network

---

## 1. Install Docker Desktop for Windows

1. Download: https://www.docker.com/products/docker-desktop/
2. Run the installer. When prompted, **check "Use WSL 2 instead of Hyper-V"** (default on modern Windows 10/11 — recommended, lighter on resources).
3. Reboot if asked.
4. If it's your first time with WSL2, Docker Desktop will prompt you to install the **WSL2 Linux kernel update** — click the link it gives you, install it, then restart Docker Desktop.
5. Launch **Docker Desktop** from the Start menu and wait for the whale icon in the system tray to say "Docker Desktop is running".

Verify in **PowerShell**:

```powershell
docker --version
docker compose version
```

Both should print a version number. If you get "command not found", Docker Desktop isn't running yet — open it and wait ~30s.

---

## 2. Get the project files onto your PC

**Option A — you have Git installed and pushed the code to GitHub already:**

```powershell
cd C:\Users\<you>\Documents
git clone https://github.com/<your-username>/<your-repo>.git psc-app
cd psc-app
```

**Option B — no Git / no GitHub, just copy the folder:**

Copy the whole project folder (the one containing `docker-compose.yml`) onto your PC via USB drive, zip download, etc. Then open PowerShell and `cd` into it:

```powershell
cd C:\Users\<you>\Documents\psc-app
```

---

## 3. Configure your `.env`

```powershell
copy .env.example .env
notepad .env
```

Set your own values (any strong password works, it's just between your own containers):

```env
MONGO_USER=pscAdmin
MONGO_PASSWORD=change-me-to-something-only-you-know
DB_NAME=psc_stock
CORS_ORIGINS=*
SEED_DEMO_DATA=false
```

Save and close Notepad.

---

## 4. Build and start everything

```powershell
docker compose up -d --build
```

First run takes 3–5 minutes (downloads base images, builds the React app). This is the **only step that needs internet** — after this, `docker compose up -d` (without `--build`) works fully offline, even mid-flight/no-WiFi.

Check status:

```powershell
docker compose ps
```

You want to see all three as `Up` / `Up (healthy)`:

```
psc-mongo      Up (healthy)
psc-backend    Up (healthy)
psc-frontend   Up
```

Test it:

```powershell
curl http://localhost/api/bootstrap
# Expected: {"brands":[],"products":[],"suppliers":[],"dealers":[]}
```

Now open **http://localhost** in your browser — empty dashboard, ready for your first brand/dealer/stock entry.

---

## 5. Open it from other devices on your network (phone, other PC)

### 5a. Find your PC's local IP

```powershell
ipconfig
```

Look for **IPv4 Address** under your active adapter (Wi-Fi or Ethernet) — something like `192.168.1.45`.

### 5b. Allow it through Windows Firewall

By default Windows Firewall blocks incoming connections on port 80 from other devices. Run **PowerShell as Administrator**:

```powershell
New-NetFirewallRule -DisplayName "PSC Stock App" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
```

(If you'd rather use the GUI: Windows Security → Firewall & network protection → Advanced settings → Inbound Rules → New Rule → Port → TCP 80 → Allow.)

### 5c. Connect from another device

On your phone/other laptop (same Wi-Fi network), open a browser and go to:

```
http://192.168.1.45
```

(use the IP you found in step 5a — it works exactly the same as `localhost`, same data, same live app)

> Tip: your PC's LAN IP can change if your router reassigns it (DHCP). If it stops working after a reboot, just re-run `ipconfig` and use the new IP. To make it permanent, set a **DHCP reservation** for your PC in your router's admin page.

---

## 6. Everyday use

| Task | Command |
|---|---|
| Start the app (after PC restart / Docker Desktop restart) | `docker compose up -d` |
| Stop the app (data is kept) | `docker compose stop` |
| Fully stop and remove containers (data is kept — it's in a named volume) | `docker compose down` |
| See logs if something looks broken | `docker compose logs -f` |
| See just backend logs | `docker compose logs -f backend` |
| Restart after you change code | `docker compose up -d --build` |

Docker Desktop is set to launch on Windows startup by default, and each service has `restart: unless-stopped` — so after a PC reboot, just open Docker Desktop and the containers come back on their own within ~30s. No need to re-run any command unless you rebooted the PC while Docker Desktop was set to not auto-start.

---

## 7. Backing up your data

Your stock data lives in a Docker volume (`mongo-data`), not a regular Windows folder, so back it up with `mongodump`:

```powershell
docker compose exec -T mongo mongodump `
  --username pscAdmin --password "YOUR_PASSWORD" `
  --authenticationDatabase admin --archive > C:\Users\<you>\Documents\psc-backup.archive
```

Copy that `.archive` file to a USB drive / cloud folder / another PC regularly — that's your entire database in one file.

**Restore it later** (e.g. new PC, or after `docker compose down -v`):

```powershell
Get-Content -Raw C:\Users\<you>\Documents\psc-backup.archive | docker compose exec -T mongo mongorestore `
  --username pscAdmin --password "YOUR_PASSWORD" --authenticationDatabase admin --archive --drop
```

---

## 8. Wiping back to a fresh empty state

```powershell
docker compose down -v      # -v also deletes the mongo-data volume — irreversible
docker compose up -d --build
```

Because `SEED_DEMO_DATA=false`, it comes back with 0 brands, 0 dealers, 0 units.

---

## 9. Troubleshooting (Windows-specific)

- **"Docker Desktop is starting…" forever** → WSL2 not installed correctly. Open PowerShell as admin: `wsl --update`, then restart Docker Desktop.
- **`docker compose up` fails with a port 80 conflict** → something else on your PC (IIS, Skype, another web server) is using port 80. Either stop it, or change the port mapping in `docker-compose.yml` from `"80:80"` to e.g. `"8080:80"` and use `http://localhost:8080` instead.
- **Other devices can't reach it, but `localhost` works** → check step 5b (firewall rule) and confirm both devices are on the same Wi-Fi network (not guest network — some routers isolate guest Wi-Fi from LAN).
- **Everything stopped after a reboot** → open Docker Desktop app manually and wait for it to say "running"; containers with `restart: unless-stopped` will then come back automatically.
- **Ran out of disk space** → `docker system prune -a` clears unused images/build cache (your `mongo-data` volume with actual stock data is untouched).
- **Forgot your Mongo password** → it's in `.env` in the project folder, open it with Notepad.

---

That's it — no AWS account, no domain, no monthly bill. Everything runs on your PC, and once built once, it works even with no internet at all.
