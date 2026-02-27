#!/bin/bash
# deploy.sh — run this on your LOCAL machine to push updates to the server
# Usage: bash deploy.sh YOUR_SERVER_IP

SERVER_IP=$1
SSH_KEY=~/.ssh/oracle_dataslate   # update this path if your key is elsewhere

if [ -z "$SERVER_IP" ]; then
  echo "Usage: bash deploy.sh YOUR_SERVER_IP"
  exit 1
fi

echo "==> Building frontend..."
cd frontend
npm run build
cd ..

echo "==> Uploading backend..."
scp -i $SSH_KEY -r backend ubuntu@$SERVER_IP:/home/ubuntu/dataslate/

echo "==> Uploading frontend build..."
ssh -i $SSH_KEY ubuntu@$SERVER_IP "sudo rm -rf /var/www/dataslate/*"
scp -i $SSH_KEY -r frontend/dist/* ubuntu@$SERVER_IP:/tmp/dataslate_frontend/
ssh -i $SSH_KEY ubuntu@$SERVER_IP "sudo cp -r /tmp/dataslate_frontend/* /var/www/dataslate/"

echo "==> Restarting backend..."
ssh -i $SSH_KEY ubuntu@$SERVER_IP "cd /home/ubuntu/dataslate/backend && source ../venv/bin/activate && python update_data.py && python scrape_cyrac.py && sudo systemctl restart dataslate"

echo "==> Done! Visit http://$SERVER_IP"
