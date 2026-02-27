# Deploying Dataslate on Oracle Cloud (Free Forever)

**Stack:**
- Oracle Cloud VM — runs nginx (frontend) + FastAPI backend
- Supabase — free PostgreSQL database

**Total cost: $0. No credit card tricks.**

---

## Part 1 — Get a free database (Supabase)

1. Go to https://supabase.com, sign up (free, no card)
2. Click **New project**, name it `dataslate`, set a password, pick your nearest region
3. Wait ~2 minutes for it to provision
4. Go to **Project Settings → Database**
5. Scroll to **Connection string → URI**, copy it:
   ```
   postgresql://postgres:YOUR-PASSWORD@db.xxxx.supabase.co:5432/postgres
   ```
   Save this — you'll need it in Part 3.

---

## Part 2 — Create Oracle Cloud VM

1. Go to https://cloud.oracle.com and sign up
   - You need a credit card to verify identity but **will not be charged**
   - Choose the **Always Free** tier throughout

2. Once in the dashboard, go to **Compute → Instances → Create Instance**

3. Configure:
   - **Name:** `dataslate`
   - **Image:** Ubuntu 22.04 (click Change Image to select)
   - **Shape:** VM.Standard.E2.1.Micro (Always Free) — or Ampere A1 for more power
   - **SSH Keys:** click **Generate a key pair** and **download both keys**
     - Save `ssh-key-XXXX.key` somewhere safe (e.g. `~/.ssh/oracle_dataslate`)
   - Leave everything else default

4. Click **Create** — VM is ready in ~2 minutes

5. Copy the **Public IP address** from the instance details page

6. Open port 80 (HTTP) in the firewall:
   - Go to the instance → **Subnet → Security List → Add Ingress Rule**
   - Source CIDR: `0.0.0.0/0`, Protocol: TCP, Port: `80`
   - Click **Add**

---

## Part 3 — Connect to your server

Open a terminal on your local machine:

```bash
# Fix key permissions (required)
chmod 600 ~/.ssh/oracle_dataslate

# Connect
ssh -i ~/.ssh/oracle_dataslate ubuntu@YOUR_SERVER_IP
```

You're now inside your server. Run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, nginx, and tools
sudo apt install -y python3 python3-pip python3-venv nginx

# Create app directory
mkdir -p /home/ubuntu/dataslate
```

---

## Part 4 — Upload the app

Back on your **local machine** (open a new terminal, leave the server one open):

```bash
cd kt_selector_v2

# Upload backend
scp -i ~/.ssh/oracle_dataslate -r backend ubuntu@YOUR_SERVER_IP:/home/ubuntu/dataslate/

# Build and upload frontend
cd frontend
npm install && npm run build
cd ..
scp -i ~/.ssh/oracle_dataslate -r frontend/dist ubuntu@YOUR_SERVER_IP:/home/ubuntu/dataslate/frontend_dist
```

---

## Part 5 — Set up the backend on the server

Back in your **server terminal**:

```bash
cd /home/ubuntu/dataslate

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Create environment variables file
nano .env
```

In nano, paste and fill in your values:
```
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.xxxx.supabase.co:5432/postgres
SECRET_KEY=paste-a-long-random-string-here
```
Save with `Ctrl+O`, Enter, `Ctrl+X`.

To generate a good SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Run the startup scripts once to verify everything works:
```bash
cd backend
source ../venv/bin/activate
python update_data.py
python scrape_cyrac.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
curl http://127.0.0.1:8000/api/meta/cyrac-info
```
You should see JSON with tier list info. Kill the test server: `kill %1`

---

## Part 6 — Set up the backend as a service (auto-starts on reboot)

Back on your local machine, upload the service file:
```bash
scp -i ~/.ssh/oracle_dataslate dataslate.service ubuntu@YOUR_SERVER_IP:/tmp/
```

On the server:
```bash
sudo cp /tmp/dataslate.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dataslate
sudo systemctl start dataslate

# Check it's running
sudo systemctl status dataslate
```

---

## Part 7 — Set up nginx (serves frontend + proxies API)

Upload the nginx config from your local machine:
```bash
scp -i ~/.ssh/oracle_dataslate nginx.conf ubuntu@YOUR_SERVER_IP:/tmp/
```

On the server:
```bash
# Install frontend files
sudo mkdir -p /var/www/dataslate
sudo cp -r /home/ubuntu/dataslate/frontend_dist/* /var/www/dataslate/

# Install nginx config
sudo cp /tmp/nginx.conf /etc/nginx/sites-available/dataslate
sudo ln -s /etc/nginx/sites-available/dataslate /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test config and restart
sudo nginx -t
sudo systemctl restart nginx
```

---

## Done

Visit `http://YOUR_SERVER_IP` in your browser — Dataslate is live.

---

## Updating in future

From your local machine, just run:
```bash
bash deploy.sh YOUR_SERVER_IP
```

This builds the frontend, uploads everything, and restarts the backend automatically.

---

## Optional: Free custom domain + HTTPS

1. Buy a domain (Cloudflare Registrar is cheapest) or use a free one from https://freedns.afraid.org
2. Point it to your Oracle IP (A record)
3. On the server, install Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d yourdomain.com
   ```
   Free HTTPS, auto-renews.
