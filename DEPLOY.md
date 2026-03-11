# Deploying Killrate — Full Guide

Deploy killrate.info on a cheap Ubuntu VPS with automatic HTTPS.

**Architecture:**
```
Internet -> Cloudflare (DNS) -> Your VPS
                                 |-- Caddy (reverse proxy, auto-HTTPS)
                                 |    |-- /         -> React static build
                                 |    |-- /api/*    -> FastAPI :8000
                                 |-- uvicorn (FastAPI backend)
                                 |-- SQLite (database file)
```

**Cost:**
| Resource                        | Cost           |
|---------------------------------|----------------|
| Hetzner CAX11 VPS               | ~$4/month      |
| Oracle Cloud Free Tier (alt)    | $0             |
| Caddy + Let's Encrypt           | $0             |
| Cloudflare DNS                  | $0             |
| killrate.info domain renewal    | ~$10/year      |

---

## Step 1 — Get a VPS

### Option A: Hetzner (recommended — $4/month, simple)

1. Go to [hetzner.com/cloud](https://hetzner.com/cloud) and create an account
2. Click **Add Server**
   - Location: Pick closest to your users (Falkenstein/Nuremberg for EU, Ashburn for US)
   - Image: **Ubuntu 22.04** or **24.04**
   - Type: **Shared vCPU → Arm64 → CAX11** (2 vCPU, 4 GB RAM, 40 GB disk)
   - SSH Key: Paste your public key (generate one with `ssh-keygen -t ed25519` if needed)
3. Click **Create & Buy Now**
4. Note the **public IP** from the server list

**Open firewall ports:**
- Go to your server → **Firewalls** tab → Create firewall
- Add inbound rules for **TCP port 80** and **TCP port 443** (source: any)
- Apply to your server

### Option B: Oracle Cloud (free forever, more setup)

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and create an account (credit card needed, never charged)
2. Go to **Compute → Instances → Create Instance**
   - Image: **Ubuntu 22.04**
   - Shape: **VM.Standard.A1.Flex** (Ampere ARM) — **2 OCPUs, 12 GB RAM**
   - Make sure **Assign public IPv4** is checked
   - Add your SSH public key
3. Note the **public IP** from the instance details

**Open firewall ports (two places!):**

In the OCI Console:
- Go to instance → click Subnet → Security List → **Add Ingress Rules**
- Add TCP port 80 (source `0.0.0.0/0`)
- Add TCP port 443 (source `0.0.0.0/0`)

In the VM itself (after SSH):
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 2 — Cloudflare DNS

1. Log into [Cloudflare](https://dash.cloudflare.com) → select **killrate.info**
2. Go to **DNS → Records**
3. Add two records:

| Type | Name  | Content           | Proxy status              |
|------|-------|-------------------|---------------------------|
| A    | `@`   | `<YOUR_VM_IP>`    | DNS only (grey cloud)     |
| A    | `www` | `<YOUR_VM_IP>`    | DNS only (grey cloud)     |

**Important:** Must be **grey cloud (DNS only)**, not orange. Caddy needs direct access to get Let's Encrypt certificates.

4. Go to **SSL/TLS** → set encryption mode to **Full**

---

## Step 3 — Push Code to GitHub

On your local machine, make sure the repo is clean and pushed:

```bash
cd c:\Users\Surya\Downloads\kt_selector_v2

# Verify .gitignore is working (should NOT show node_modules, .db, .env, .rar)
git status

# Stage and commit
git add .gitignore Caddyfile killrate-api.service deploy.sh DEPLOY.md
git add backend/main.py backend/database.py
git commit -m "Add deployment configs for killrate.info"

# Push (create the repo on GitHub first if needed)
git remote add origin https://github.com/<YOUR_USERNAME>/kt_selector_v2.git
git push -u origin main
```

**Never commit:** `.env`, `dataslate.db`, `node_modules/`, `*.rar`

---

## Step 4 — Deploy

SSH into your VPS:

```bash
# Hetzner (default user: root)
ssh root@<YOUR_VM_IP>

# Oracle (default user: ubuntu)
ssh ubuntu@<YOUR_VM_IP>
```

Clone and run the deploy script:

```bash
git clone https://github.com/<YOUR_USERNAME>/kt_selector_v2.git /opt/killrate
cd /opt/killrate
bash deploy.sh
```

The script will automatically:
- Install Python 3, Node.js, Caddy
- Install backend pip dependencies
- Build the React frontend
- Generate a random `SECRET_KEY` (stored in `/opt/killrate/.env`)
- Configure and start the Caddy reverse proxy (with auto-HTTPS)
- Configure and start the FastAPI backend as a systemd service
- Set up a daily SQLite backup cron (3am, keeps 7 days)

---

## Step 5 — Verify

```bash
# Check services are running
systemctl status killrate-api
systemctl status caddy

# Test backend directly
curl http://localhost:8000/api/killteams | head -c 200

# Test through Caddy
curl https://killrate.info/api/meta | head -c 200
```

Then open **https://killrate.info** in your browser.

---

## Updating (Future Deploys)

When you push new code to GitHub:

```bash
ssh root@<YOUR_VM_IP>     # or ubuntu@ for Oracle
cd /opt/killrate
bash deploy.sh
```

That's it — the script pulls latest code, rebuilds frontend, and restarts services.

For backend-only changes (faster):
```bash
cd /opt/killrate && git pull
sudo systemctl restart killrate-api
```

---

## Troubleshooting

### View logs
```bash
# Backend logs (live)
sudo journalctl -u killrate-api -f

# Caddy logs (live)
sudo journalctl -u caddy -f
```

### Restart services
```bash
sudo systemctl restart killrate-api
sudo systemctl restart caddy
```

### HTTPS not working
- Verify Cloudflare DNS records are **grey cloud** (DNS only), not orange
- Check Caddy logs: `sudo journalctl -u caddy --no-pager -n 50`
- Make sure ports 80 and 443 are open (test with `curl http://<YOUR_VM_IP>`)

### Database issues
```bash
# Check database exists
ls -la /opt/killrate/backend/data/dataslate.db

# Manual backup
sqlite3 /opt/killrate/backend/data/dataslate.db ".backup /opt/killrate/backups/manual-backup.db"

# Check backup cron is installed
crontab -l
```

### "database is locked" errors
This shouldn't happen (WAL mode is enabled), but if it does:
```bash
# Check no stale processes
sudo systemctl restart killrate-api
```

---

## File Reference

| What              | Path                                          |
|-------------------|-----------------------------------------------|
| App directory     | `/opt/killrate`                               |
| SQLite database   | `/opt/killrate/backend/data/dataslate.db`     |
| Secret key        | `/opt/killrate/.env`                          |
| Backups           | `/opt/killrate/backups/` (daily, 7-day keep)  |
| Caddy config      | `/etc/caddy/Caddyfile`                        |
| Backend service   | `/etc/systemd/system/killrate-api.service`    |
| Backend logs      | `sudo journalctl -u killrate-api`             |
| Caddy logs        | `sudo journalctl -u caddy`                    |
