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
echo "Installing Cloudflare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    echo "Cloudflare Tunnel is not installed. Downloading official RPM..."
    
    # Remove any existing broken repository files that may still be present.
    rm -f /etc/yum.repos.d/cloudflare-main.repo
    
    # System Architecture Detection.
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        RPM_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm"
    elif [ "$ARCH" = "aarch64" ]; then
        RPM_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-aarch64.rpm"
    else
        # For other architectures, the system will attempt to download the default amd64 version.
        RPM_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm"
    fi

    # Downloading and Installing RPM Packages
    echo "Downloading from: $RPM_URL"
    dnf install -y "$RPM_URL"
    
    if command -v cloudflared &> /dev/null; then
        echo "Cloudflare Tunnel installed successfully."
    else
        echo "Error: Cloudflare Tunnel installation failed."
        exit 1
    fi
else
    echo "Cloudflare Tunnel already installed."
fi

# CloudFlare Tunnel execution code.
echo "Starting the application..."
cloudflared tunnel --url http://localhost:$PORT
