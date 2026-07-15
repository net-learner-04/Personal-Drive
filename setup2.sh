#!/bin/bash

clear

# Set the port for the application to listen on.
PORT=2926

# Enter your Discord Webhook URL here to receive notifications when the tunnel starts.
DISCORD_WEBHOOK_URL=""

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

# Create a temporary Named Pipe (FIFO) to intercept the live stream without blocking.
FIFO_PIPE="/tmp/cf_tunnel_pipe"
rm -f "$FIFO_PIPE"
mkfifo "$FIFO_PIPE"

# Launch cloudflared in the background, redirecting stderr (2) to the named pipe.
# Cloudflared outputs its operational logs strictly through stderr.
cloudflared tunnel --url http://localhost:$PORT 2> "$FIFO_PIPE" &
TUNNEL_PID=$!

# Read the stream line-by-line via sed until the trycloudflare URL matches.
# Using 'head -n 1' ensures this block breaks immediately once the first match is found.
TUNNEL_URL=$(sed -n 's|.*\(https://[a-zA-Z0-9-]\+\.trycloudflare\.com\).*|\1|p' "$FIFO_PIPE" | head -n 1)

# Clean up the named pipe asset as it is no longer required.
rm -f "$FIFO_PIPE"

# If the URL was parsed successfully, broadcast it to the console and Discord.
if [ ! -z "$TUNNEL_URL" ]; then
    # 1. Output directly to the local terminal console (Bold Green for Success, Bold Red for the URL).
    echo -e "\n\e[1;32m[Success] Cloudflare Tunnel is running!\e[0m"
    echo -e "Your Web Server URL: \e[1;31m$TUNNEL_URL\e[0m\n"
    
    # 2. Transmit the payload payload asynchronously to Discord via Webhook API if configured.
    if [ "$DISCORD_WEBHOOK_URL" != "YOUR_DISCORD_WEBHOOK_URL_HERE" ]; then
        PAYLOAD=$(printf '{"content": "**Cloudflare Tunnel Started!**\\n URL: %s"}' "$TUNNEL_URL")
        curl -H "Content-Type: application/json" -X POST -d "$PAYLOAD" "$DISCORD_WEBHOOK_URL" &> /dev/null &
    fi
else
    echo "Error: Failed to extract Cloudflare Tunnel URL."
fi

# Hand over process flow execution back to the background tunnel thread.
wait $TUNNEL_PID
