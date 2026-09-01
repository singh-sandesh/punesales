# Deploying PSC Stock Control on AWS EC2 — Docker Compose Edition

One-file deploy. You run `docker compose up -d` and the app, database, and web server all come up together. About **15 minutes end-to-end**.

The stack:

- `mongo` — MongoDB 7 with a named volume for persistence
- `backend` — FastAPI on port 8001 (internal only, not exposed)
- `frontend` — Nginx that serves the built React app **and** reverse-proxies `/api/*` to `backend`

Only `frontend` publishes a port on the host (80 → 80). The database and API are on an internal Docker network, invisible from the internet.

---

## 1. Launch the EC2 instance

1. AWS Console → **EC2** → **Launch instance**.
2. **Name**: `psc-stock`
3. **AMI**: `Ubuntu Server 24.04 LTS` (or 22.04). Architecture: `64-bit (x86)`.
4. **Instance type**: `t3.small` is plenty for a single shop. Bump to `t3.medium` if you expect heavy usage or want headroom for the DB.
5. **Key pair**: create or pick one, download the `.pem`.
6. **Security group** — inbound rules:

   | Type       | Port | Source          |
   | ---------- | ---- | --------------- |
   | SSH        | 22   | Your IP only    |
   | HTTP       | 80   | `0.0.0.0/0`     |
   | HTTPS      | 443  | `0.0.0.0/0`     |

7. **Storage**: 20 GB `gp3` root volume.
8. **Launch instance** → wait for `Running` → copy the **Public IPv4 address**.

---

## 2. Log in and install Docker

From your laptop:

```bash
chmod 400 ~/Downloads/psc-stock.pem
ssh -i ~/Downloads/psc-stock.pem ubuntu@<EC2_PUBLIC_IP>
```

On the instance:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg git

# Official Docker install
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Run docker without sudo
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
exit
```

Reconnect:

```bash
ssh -i ~/Downloads/psc-stock.pem ubuntu@<EC2_PUBLIC_IP>
docker --version && docker compose version
```

---

## 3. Clone the repo and configure

```bash
cd /home/ubuntu
git clone https://github.com/singh-sandesh/punesales.git app
cd app

# Copy the sample and set your own secrets
cp .env.example .env
nano .env
```

Set at minimum:

```env
MONGO_USER=pscAdmin
MONGO_PASSWORD=<a-long-random-string>
DB_NAME=psc_stock
CORS_ORIGINS=*
SEED_DEMO_DATA=false
```

Save and exit (Ctrl-O, Enter, Ctrl-X).

> Tip — generate a strong password: `openssl rand -base64 24`

---

## 4. Bring the stack up

```bash
cd /home/ubuntu/app
docker compose up -d --build
```

First build takes 3–5 minutes (pulling images, building React). Subsequent runs are seconds.

Check that everything is healthy:

```bash
docker compose ps
```

You should see three containers `Up (healthy)`:

```
psc-mongo      Up (healthy)
psc-backend    Up (healthy)
psc-frontend   Up (healthy)
```

Test the API from inside the box:

```bash
curl http://localhost/api/bootstrap
# Expected: {"brands":[],"products":[],"suppliers":[],"dealers":[]}
```

Now open `http://<EC2_PUBLIC_IP>` in your browser — you'll see the empty PSC dashboard, ready to accept your first brand and first stock-in.

---

## 5. Point your domain

In your DNS provider (Route 53, Cloudflare, GoDaddy…) create an **A record**:

```
your-domain.com   →   <EC2_PUBLIC_IP>
www.your-domain.com → <EC2_PUBLIC_IP>
```

Wait 2–5 minutes, then verify:

```bash
dig your-domain.com +short
# should print your EC2 IP
```

---

## 6. HTTPS with Let's Encrypt (recommended)

The cleanest way with Docker is to add a small **Caddy** container as the public reverse proxy — it auto-issues and renews certificates, no manual certbot needed.

Stop the current stack:

```bash
cd /home/ubuntu/app
docker compose down
```

Move the frontend off port 80 by editing `docker-compose.yml` and change the `frontend` service ports block:

```yaml
  frontend:
    # ... existing config ...
    # remove:  ports:
    #            - "80:80"
    expose:
      - "80"
```

Add a Caddy service (append inside `services:`):

```yaml
  caddy:
    image: caddy:2-alpine
    container_name: psc-caddy
    restart: unless-stopped
    depends_on:
      - frontend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    networks:
      - psc-net
```

And add these two volumes at the bottom (next to `mongo-data`):

```yaml
volumes:
  mongo-data:
  caddy-data:
  caddy-config:
```

Create `/home/ubuntu/app/Caddyfile`:

```caddy
your-domain.com, www.your-domain.com {
    encode gzip zstd
    reverse_proxy frontend:80
}
```

Bring it back up:

```bash
docker compose up -d --build
```

Caddy will now automatically fetch a Let's Encrypt cert on first request and auto-renew forever. Visit `https://your-domain.com` — it just works.

---

## 7. Everyday operations

| Task                                 | Command                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| Container status                     | `docker compose ps`                                         |
| Tail all logs                        | `docker compose logs -f`                                    |
| Tail backend only                    | `docker compose logs -f backend`                            |
| Restart just the backend             | `docker compose restart backend`                            |
| Update code from GitHub              | `git pull && docker compose up -d --build`                  |
| Stop everything                      | `docker compose down`                                       |
| Stop **and** delete DB (destructive) | `docker compose down -v`                                    |
| Open a mongo shell                   | `docker compose exec mongo mongosh -u $MONGO_USER -p`       |

---

## 8. Backups

**Local snapshot** (run any time):

```bash
docker compose exec -T mongo mongodump \
  --username "$(grep MONGO_USER /home/ubuntu/app/.env | cut -d= -f2)" \
  --password "$(grep MONGO_PASSWORD /home/ubuntu/app/.env | cut -d= -f2)" \
  --authenticationDatabase admin \
  --archive > ~/psc-$(date +%F).archive
```

**Restore** from a snapshot:

```bash
cat ~/psc-2026-02-15.archive | docker compose exec -T mongo mongorestore \
  --username "..." --password "..." --authenticationDatabase admin --archive --drop
```

**Nightly S3 upload** — `crontab -e` and add:

```
0 2 * * * cd /home/ubuntu/app && \
  docker compose exec -T mongo mongodump \
    --username pscAdmin --password YOUR_PASSWORD --authenticationDatabase admin --archive \
  | gzip > /home/ubuntu/psc-$(date +\%F).archive.gz && \
  aws s3 cp /home/ubuntu/psc-$(date +\%F).archive.gz s3://your-bucket/psc-backups/ && \
  find /home/ubuntu -maxdepth 1 -name "psc-*.archive.gz" -mtime +14 -delete
```

Install AWS CLI first: `sudo apt install -y awscli && aws configure`.

---

## 9. Troubleshooting

- **`docker compose ps` shows a container `unhealthy` or restarting** → `docker compose logs <service>`.
- **`Bad Gateway` when opening the site** → backend container not up: `docker compose logs backend`.
- **Login page never loads** → check `docker compose logs frontend` for build errors.
- **CORS error in browser console** → set `CORS_ORIGINS=https://your-domain.com` in `.env`, then `docker compose up -d`.
- **Ran out of disk** → `docker system prune -a --volumes` frees old images and dangling data (**this deletes anonymous volumes — the named `mongo-data` volume is safe**).
- **Forgot the mongo password** → it's in your `/home/ubuntu/app/.env` file.

---

## 10. Cost sketch

| Item                     | Approx / month |
| ------------------------ | -------------- |
| EC2 `t3.small` on-demand | $15            |
| 20 GB gp3 EBS            | $2             |
| Route 53 hosted zone     | $0.50          |
| S3 backups (< 1 GB)      | $0.03          |
| **Total**                | **≈ $18**      |

Reserve the instance for 1 year to bring EC2 down to about $9/mo.

---

## 11. Wiping the app back to a fresh state

```bash
cd /home/ubuntu/app
docker compose down -v      # -v also drops the mongo-data volume
docker compose up -d --build
```

Because `SEED_DEMO_DATA=false`, the app comes back completely empty — 0 brands, 0 dealers, 0 units — ready for your first real record.

---

That's the whole thing. One `.env` file, one `docker compose up -d --build`, one Nginx port on the host, everything else on an isolated internal network.
