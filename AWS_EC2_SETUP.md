# Deploying PSC Stock Control on AWS EC2

A step-by-step, copy-and-paste guide to get the app running on a fresh AWS EC2 instance with MongoDB, Nginx, PM2 and HTTPS. Total time: about 30–40 minutes.

The app is a three-part stack:

- **MongoDB 7** — the database (runs on the same EC2 or on MongoDB Atlas)
- **FastAPI backend** — Python, runs on port `8001`
- **React frontend** — built once, served as static files by Nginx

---

## 1. Launch the EC2 instance

1. Sign in to the AWS Console → **EC2** → **Launch instance**.
2. **Name**: `psc-stock`
3. **AMI**: `Ubuntu Server 22.04 LTS` (or 24.04). Architecture: `64-bit (x86)`.
4. **Instance type**:
   - `t3.small` (2 vCPU, 2 GB RAM) is enough for a single-user shop.
   - `t3.medium` if you plan to keep MongoDB on the same box and expect real traffic.
5. **Key pair**: create or pick one and download the `.pem`. Keep it safe.
6. **Network settings** → *Edit* → **Security group** — create new with these inbound rules:
   | Type       | Port | Source          | Purpose                 |
   | ---------- | ---- | --------------- | ----------------------- |
   | SSH        | 22   | Your IP only    | Login                   |
   | HTTP       | 80   | `0.0.0.0/0`     | Nginx / Let's Encrypt   |
   | HTTPS      | 443  | `0.0.0.0/0`     | Nginx (after SSL)       |
7. **Storage**: 20 GB `gp3` root volume is plenty.
8. Click **Launch instance**.

Once it's `Running`, copy the **Public IPv4 address**.

---

## 2. First-time login

From your laptop:

```bash
chmod 400 ~/Downloads/psc-stock.pem
ssh -i ~/Downloads/psc-stock.pem ubuntu@<EC2_PUBLIC_IP>
```

Update the box:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential nginx ufw
```

Enable the firewall (optional but recommended):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

---

## 3. Install MongoDB 7 (on the same EC2)

> Skip this section if you use **MongoDB Atlas** — jump to Section 4 and just paste your Atlas connection string when creating `backend/.env`.

```bash
# Add MongoDB signing key + repo
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
  https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod --no-pager     # should say "active (running)"
```

**Secure MongoDB** with a database user:

```bash
mongosh
```

Inside the mongo shell:

```javascript
use admin
db.createUser({
  user: "pscAdmin",
  pwd:  "CHANGE_ME_STRONG_PASSWORD",
  roles: [{ role: "root", db: "admin" }]
})
exit
```

Turn on authentication:

```bash
sudo sed -i 's/#security:/security:\n  authorization: enabled/' /etc/mongod.conf
sudo systemctl restart mongod
```

Now MongoDB is only accessible with credentials. The connection URL you will use in `backend/.env` is:

```
mongodb://pscAdmin:CHANGE_ME_STRONG_PASSWORD@127.0.0.1:27017/?authSource=admin
```

### Storage for the database
By default MongoDB stores data in `/var/lib/mongodb`, which lives on the root EBS volume. **20 GB is enough for years of stock movements** for a single shop. If you want more headroom later:

1. In AWS Console → EC2 → **Volumes** → your `gp3` root volume → *Modify volume* → change from 20 → 50 GB.
2. On the instance: `sudo growpart /dev/nvme0n1 1 && sudo resize2fs /dev/nvme0n1p1`.

Automatic backups (recommended): run `mongodump --uri="mongodb://pscAdmin:PASS@127.0.0.1:27017/?authSource=admin" --out /home/ubuntu/backups/$(date +%F)` from cron nightly, then sync `/home/ubuntu/backups` to an S3 bucket with `aws s3 sync` (5 GB S3 free tier is plenty).

---

## 4. Install Node.js, Yarn and Python

```bash
# Node 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn pm2

# Python 3.11 + venv
sudo apt install -y python3 python3-venv python3-pip
```

Check versions:

```bash
node -v && yarn -v && python3 -V
```

---

## 5. Clone the app

```bash
cd /home/ubuntu
git clone https://github.com/singh-sandesh/punesales.git app
cd app
```

---

## 6. Configure the backend

```bash
cd /home/ubuntu/app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```bash
cat > /home/ubuntu/app/backend/.env <<'EOF'
MONGO_URL=mongodb://pscAdmin:CHANGE_ME_STRONG_PASSWORD@127.0.0.1:27017/?authSource=admin
DB_NAME=psc_stock
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
SEED_DEMO_DATA=false
EOF
```

Notes:
- `SEED_DEMO_DATA=false` means the app starts **completely empty** — no demo brands, dealers, or units.
- Set `CORS_ORIGINS` to the final domain(s) the frontend will be served from. During initial testing you can temporarily use `CORS_ORIGINS=*`.

Test the backend:

```bash
cd /home/ubuntu/app/backend
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
# Ctrl-C once you see "Uvicorn running on http://0.0.0.0:8001"
```

Now run it as a background service with PM2:

```bash
cd /home/ubuntu/app/backend
pm2 start "/home/ubuntu/app/backend/.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001" \
  --name psc-backend --cwd /home/ubuntu/app/backend
pm2 save
pm2 startup systemd -u ubuntu --hp /home/ubuntu
# Copy-paste the last "sudo env PATH=... pm2 startup" command it prints, and run it.
```

Verify:

```bash
curl http://127.0.0.1:8001/api/bootstrap
# expected: {"brands":[],"products":[],"suppliers":[],"dealers":[]}
```

---

## 7. Build the frontend

```bash
cd /home/ubuntu/app/frontend
```

Create `frontend/.env` — this URL is baked into the build, so set it to the domain (or public IP for now) that Nginx will serve:

```bash
cat > /home/ubuntu/app/frontend/.env <<'EOF'
REACT_APP_BACKEND_URL=https://your-domain.com
EOF
```

Install & build:

```bash
yarn install
yarn build
```

The static site is now in `/home/ubuntu/app/frontend/build/`.

---

## 8. Nginx: serve frontend + proxy `/api` to backend

```bash
sudo tee /etc/nginx/sites-available/psc-stock >/dev/null <<'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    root /home/ubuntu/app/frontend/build;
    index index.html;

    # React router — always fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Forward all API traffic to FastAPI on port 8001
    location /api/ {
        proxy_pass         http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        client_max_body_size 20m;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/psc-stock /etc/nginx/sites-enabled/psc-stock
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Open `http://<EC2_PUBLIC_IP>` — you should see the empty PSC dashboard, ready to accept your first brand and first stock-in.

---

## 9. Point your domain, then enable HTTPS

1. In your DNS provider (Route 53, GoDaddy, Cloudflare, etc.) create an **A record** for `your-domain.com` → your EC2 public IP.
2. Wait 2–5 minutes for DNS to propagate (`dig your-domain.com` should resolve to the EC2 IP).
3. Get a free Let's Encrypt certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
# Choose "redirect HTTP to HTTPS" when prompted
```

Certbot auto-renews via a systemd timer — no cron needed.

Finally, rebuild the frontend so it points at the HTTPS URL:

```bash
sed -i 's|http://your-domain.com|https://your-domain.com|' /home/ubuntu/app/frontend/.env
cd /home/ubuntu/app/frontend && yarn build
```

Reload Nginx once:

```bash
sudo systemctl reload nginx
```

---

## 10. Everyday operations

| Task                        | Command                                                        |
| --------------------------- | -------------------------------------------------------------- |
| See backend logs            | `pm2 logs psc-backend`                                         |
| Restart backend             | `pm2 restart psc-backend`                                      |
| Stop backend                | `pm2 stop psc-backend`                                         |
| Update to latest code       | `cd /home/ubuntu/app && git pull`                              |
| Rebuild frontend            | `cd /home/ubuntu/app/frontend && yarn build && sudo systemctl reload nginx` |
| Restart backend after pull  | `pm2 restart psc-backend`                                      |
| Backup DB now               | `mongodump --uri="mongodb://pscAdmin:PASS@127.0.0.1:27017/?authSource=admin" --out ~/backups/$(date +%F)` |
| Restore DB                  | `mongorestore --uri="…" --drop ~/backups/<folder>`             |

---

## 11. Daily backup to S3 (optional but strongly recommended)

```bash
sudo apt install -y awscli
aws configure                # paste an IAM user access key that has s3:PutObject on your bucket

cat > /home/ubuntu/backup.sh <<'EOF'
#!/bin/bash
DATE=$(date +%F)
DIR=/home/ubuntu/backups/$DATE
mkdir -p "$DIR"
mongodump --uri="mongodb://pscAdmin:CHANGE_ME_STRONG_PASSWORD@127.0.0.1:27017/?authSource=admin" --out "$DIR"
tar -czf "$DIR.tar.gz" -C /home/ubuntu/backups "$DATE"
aws s3 cp "$DIR.tar.gz" s3://your-bucket/psc-backups/
find /home/ubuntu/backups -mtime +7 -delete
EOF
chmod +x /home/ubuntu/backup.sh

crontab -e
# add this line, save & exit:
0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

Now the DB is dumped every night at 2 AM, gzipped, pushed to S3, and locally kept for a week.

---

## 12. Troubleshooting

- **`curl /api/bootstrap` hangs** → backend isn't running: `pm2 logs psc-backend`.
- **Frontend loads but data doesn't** → the value in `frontend/.env` (`REACT_APP_BACKEND_URL`) doesn't match the domain. Fix it and re-run `yarn build`.
- **CORS error in the browser console** → add your domain to `CORS_ORIGINS` in `backend/.env`, then `pm2 restart psc-backend`.
- **MongoDB won't start** → `sudo journalctl -u mongod -n 50`.
- **Nginx 502 Bad Gateway** → backend is down or listening on the wrong port. Check `pm2 status`.

---

## 13. Cost sketch

| Item                            | Approx / month |
| ------------------------------- | -------------- |
| EC2 `t3.small` on-demand        | $15            |
| 20 GB gp3 EBS                   | $2             |
| Route 53 hosted zone            | $0.50          |
| S3 backups (<1 GB)              | $0.03          |
| **Total**                       | **≈ $18**      |

You can drop to $10/mo with a 1-year Reserved Instance, or move MongoDB to Atlas Free Tier and downsize to `t3.micro` for about $8/mo.

---

That's it — your PSC Stock Control is live on your own domain, with automated backups and HTTPS, and starts completely empty so you begin fresh from your first brand and first stock-in.
