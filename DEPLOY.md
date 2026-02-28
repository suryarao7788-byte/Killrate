# Running Dataslate from Your Computer

Uses Cloudflare Tunnel — free, no server, no port forwarding needed.
Your PC needs to be on for others to access it.

---

## Step 1 — One-time setup

**Install Cloudflare Tunnel:**
1. Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
2. Get the Windows `.msi` installer and run it

**Create a `.env` file** in the `backend/` folder:
```
SECRET_KEY=any-long-random-string-you-make-up
```
To generate one, run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 2 — Start the backend

Open a terminal in `kt_selector_v2/backend/` and run:
```bash
pip install -r requirements.txt
python update_data.py
python scrape_cyrac.py
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Leave this running.

---

## Step 3 — Start the frontend

Open a second terminal in `kt_selector_v2/frontend/` and run:
```bash
npm install
npm run dev
```

This starts the frontend on http://localhost:5173 with the API proxy built in.
Leave this running too.

---

## Step 4 — Open the tunnel

Open a third terminal and run:
```bash
cloudflared tunnel --url http://localhost:5173
```

Cloudflare prints a public URL like:
```
https://something-random.trycloudflare.com
```

Share that URL — anyone can access Dataslate from it.

---

## That's it

Three terminals, one command each. The tunnel URL changes every time you restart
cloudflared — that's the only downside of the free anonymous tunnel.

**To get a permanent URL (still free):**
1. Sign up at https://dash.cloudflare.com
2. Go to Zero Trust → Networks → Tunnels → Create tunnel
3. Follow the setup — you get a stable `something.yourdomain.com` URL forever

---

## Updating CYRAC data each quarter

Stop the backend (Ctrl+C), run:
```bash
python scrape_cyrac.py
```
Then restart it.
