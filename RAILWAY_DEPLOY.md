# Deploy PSC Stock Control to Railway

You don't need Docker, Node, Python, or MongoDB on your PC.
Railway builds and runs everything in the cloud. You just need:
- a free Railway account: https://railway.com
- your project pushed to GitHub

---

## 1) Push this project to GitHub

If you don't already have it on GitHub, use the **"Save to Github"** button
inside Emergent's chat. It will create a repo and push your code.

---

## 2) Create the Railway project

1. Go to https://railway.com and click **New Project**.
2. Choose **Deploy from GitHub repo** and pick your PSC repo.
3. Railway will read `railway.json` and start building from the `Dockerfile`.
   First build takes about 5-8 minutes (Node install + React build + Python deps).

Do **not** deploy yet — first add the database (next step) or the app will
crash on startup because `MONGO_URL` is missing.

---

## 3) Add MongoDB

1. In the same Railway project, click **+ New** -> **Database** -> **Add MongoDB**.
2. Railway spins up a Mongo instance and exposes its connection details as
   variables on the Mongo service (`MONGO_URL`, `MONGOHOST`, `MONGOPORT`, ...).

---

## 4) Wire the backend to Mongo

Open your **PSC app service** (the one built from your repo) -> **Variables**
-> **+ New Variable** and add:

| Variable          | Value                                        |
| ----------------- | -------------------------------------------- |
| `MONGO_URL`       | `${{MongoDB.MONGO_URL}}` (reference)         |
| `DB_NAME`         | `psc_stock`                                  |
| `CORS_ORIGINS`    | `*`                                          |
| `SEED_DEMO_DATA`  | `false`                                      |

The `${{MongoDB.MONGO_URL}}` syntax pulls the value straight from the Mongo
service - no copy-pasting secrets.

Save. Railway will redeploy automatically.

---

## 5) Get your public URL

On the PSC service -> **Settings** -> **Networking** -> **Generate Domain**.
You'll get something like `psc-stock-production.up.railway.app`.

Open it in a browser - the React app loads, talks to `/api/...` on the same
host, and Mongo is already connected. Done.

---

## 6) Everyday use

- **View the app**: just visit your Railway domain from any device.
- **Deploy changes**: `git push` to GitHub -> Railway auto-rebuilds.
- **Watch logs**: Railway dashboard -> your service -> **Deployments** ->
  **View logs**.
- **Backup data**: Mongo service -> **Data** tab, or use
  `mongodump` against the public Mongo URL that Railway exposes.

---

## Troubleshooting

**Build fails on `yarn install`**
The `Dockerfile` already retries without `--frozen-lockfile` if the lockfile
is out of date, so this is rare. If it still fails, check the top of the
build log for the exact package - it's usually a peer-dep on React 19.

**App boots but 502 / "Application failed to respond"**
Check the deploy log. Most common cause: `MONGO_URL` variable not set on the
PSC service. Re-check Step 4.

**Health check keeps failing**
Railway hits `/api/dashboard`. If Mongo isn't reachable that endpoint will
5xx and Railway will restart the container. Fix the `MONGO_URL` and it
recovers on its own.

**I want a custom domain**
Service -> **Settings** -> **Networking** -> **Custom Domain**. Add a CNAME
in your DNS to the value Railway shows.
