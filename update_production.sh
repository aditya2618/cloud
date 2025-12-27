#!/bin/bash
# Production Cloud Server Update Script
# Run this on your cloud server via SSH

echo "🚀 Updating Production Cloud Server..."
cd ~/cloud

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git stash
git pull origin main

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart smarthome-cloud

# Check status
echo "✅ Checking status..."
sleep 3
sudo systemctl status smarthome-cloud --no-pager -n 20

echo ""
echo "🎉 Update complete! Gateway WebSocket endpoint is now available at:"
echo "   ws://35.209.239.164:9000/ws/gateway/"
echo ""
echo "Check logs with:"
echo "   sudo journalctl -u smarthome-cloud -f"
