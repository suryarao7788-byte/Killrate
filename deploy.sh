#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Killrate deployment script — Ubuntu VPS (Hetzner, Oracle, DigitalOcean, etc.)
#
# PREREQUISITES (one-time manual steps):
#
#   1. Provision an Ubuntu 22.04/24.04 VPS:
#      - Hetzner CAX11 (€3.79/mo): hetzner.com/cloud → New Server → ARM
#      - Oracle Free Tier ($0): VM.Standard.A1.Flex, 2 OCPU, 12 GB RAM
#      - Any Ubuntu VPS with 1+ GB RAM works
#
#   2. Open ports 80 (HTTP) and 443 (HTTPS):
#      - Hetzner: Firewall tab in Cloud Console → add rules for 80/443
#      - Oracle:  VCN → Subnet → Security List → Add Ingress for 80/443,
#                 PLUS open in OS firewall:
#                   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
#                   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
#                   sudo netfilter-persistent save
#
#   3. Cloudflare DNS (killrate.info):
#      - A record: killrate.info → <VM_PUBLIC_IP>  (DNS only / grey cloud)
#      - A record: www           → <VM_PUBLIC_IP>  (DNS only / grey cloud)
#
#   4. Push your repo to GitHub, then run this script on the VM:
#      ssh root@<VM_IP>            # (Hetzner default user is root)
#      ssh ubuntu@<VM_IP>          # (Oracle default user is ubuntu)
#      git clone https://github.com/<YOU>/kt_selector_v2.git /opt/killrate
#      cd /opt/killrate && bash deploy.sh
# ============================================================================

APP_DIR="/opt/killrate"
ENV_FILE="$APP_DIR/.env"

echo "==> Updating system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv nodejs npm curl

# ── Install Caddy ────────────────────────────────────────────────────────────
if ! command -v caddy &>/dev/null; then
    echo "==> Installing Caddy..."
    sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt-get update -qq
    sudo apt-get install -y -qq caddy
fi

# ── Ensure app directory ─────────────────────────────────────────────────────
if [ ! -d "$APP_DIR/.git" ]; then
    echo "==> Please clone the repo to $APP_DIR first."
    echo "    git clone <your-repo-url> $APP_DIR"
    exit 1
fi

cd "$APP_DIR"
echo "==> Pulling latest code..."
git pull --ff-only

# ── Generate SECRET_KEY on first run ─────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    echo "==> Generating secret key..."
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" > "$ENV_FILE"
fi

# ── Backend setup ────────────────────────────────────────────────────────────
echo "==> Installing Python dependencies..."
cd "$APP_DIR/backend"
python3 -m pip install --break-system-packages -q -r requirements.txt

# ── Frontend build ───────────────────────────────────────────────────────────
echo "==> Building frontend..."
cd "$APP_DIR/frontend"
npm ci --silent
npm run build

# ── Deploy Caddy config ──────────────────────────────────────────────────────
echo "==> Configuring Caddy..."
sudo cp "$APP_DIR/Caddyfile" /etc/caddy/Caddyfile

# ── Deploy systemd service ───────────────────────────────────────────────────
echo "==> Setting up systemd services..."
sed "s/DEPLOY_USER/$(whoami)/" "$APP_DIR/killrate-api.service" | sudo tee /etc/systemd/system/killrate-api.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable killrate-api
sudo systemctl restart killrate-api
sudo systemctl restart caddy

# ── Daily SQLite backup (cron) ───────────────────────────────────────────────
BACKUP_DIR="$APP_DIR/backups"
mkdir -p "$BACKUP_DIR"
CRON_LINE="0 3 * * * sqlite3 $APP_DIR/backend/data/dataslate.db \".backup '$BACKUP_DIR/dataslate-\$(date +\\%Y\\%m\\%d).db'\" && find $BACKUP_DIR -name '*.db' -mtime +7 -delete"
( crontab -l 2>/dev/null | grep -v "dataslate" ; echo "$CRON_LINE" ) | crontab -
echo "==> Daily backup cron installed (3am, keeps 7 days)"

echo ""
echo "==> Deployment complete!"
echo "    Backend:  systemctl status killrate-api"
echo "    Caddy:    systemctl status caddy"
echo "    Backups:  $BACKUP_DIR (daily, 7-day retention)"
echo "    Site:     https://killrate.info"
