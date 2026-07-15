#!/bin/bash

clear

# Set the port for the application to listen on.
PORT=2926

# Verify Root Permissions.
if [ "$EUID" -ne 0 ]
then
    echo "Error: Run as root."
    exit 1
fi

# Registering and Installing the Cloudflare Package Repository.
echo "Installing CloudFlare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    echo "Installing Cloudflare Tunnel..."
    curl -L https://pkg.cloudflare.com/cloudflare-main.repo | tee /etc/yum.repos.d/cloudflare-main.repo
    dnf install cloudflared -y
    echo "Cloudflare Tunnel installed."
else
    echo "Cloudflare Tunnel already installed."
fi

# CloudFlare Tunnel execution code.
echo "Starting the application..."
cloudflared tunnel --url http://localhost:$PORT
