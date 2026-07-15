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
if ! command -v cloudflared &> /dev/null
then
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
    
    if command -v cloudflared &> /dev/null
    then
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

# Create a temporary log file to capture the live Cloudflared output.
LOG_FILE=$(mktemp)

# Start Cloudflared while displaying logs on the console and writing them to the log file.
cloudflared tunnel --url http://localhost:$PORT 2>&1 | tee "$LOG_FILE" &
PIPE_PID=$!

# Wait until the first TryCloudflare URL appears in the log file.
TUNNEL_URL=""
while [ -z "$TUNNEL_URL" ]
do
    TUNNEL_URL=$(grep -m1 -oE 'https://[[:alnum:]-]+\.trycloudflare\.com' "$LOG_FILE" | tr -d '\r\n')

    if ! kill -0 "$PIPE_PID" 2>/dev/null
    then
        break
    fi

    sleep 0.2
done

# If the URL was parsed successfully, broadcast it to the console and Discord.
if [ -n "$TUNNEL_URL" ]
then
    # 1. Output directly to the local terminal console (Bold Green for Success, Bold Red for the URL).
    echo -e "\n\e[1;32mCloudflare Tunnel is running...\e[0m"
    echo -e "Web Server URL: \e[1;31m$TUNNEL_URL\e[0m\n"

    # 2. Transmit the payload asynchronously to Discord via Webhook API if configured.
    if [ -n "$DISCORD_WEBHOOK_URL" ]
    then
        PAYLOAD=$(printf '{"content":"**Cloudflare Tunnel**\\n\nURL: %s"}' "$TUNNEL_URL")

        curl -H "Content-Type: application/json" \
             -X POST \
             -d "$PAYLOAD" \
             "$DISCORD_WEBHOOK_URL"
        
        echo ""
    fi
else
    echo "Failed to extract Cloudflare Tunnel URL."
fi

# Wait for the Cloudflared process to exit and remove the temporary log file.
wait "$PIPE_PID"
rm -f "$LOG_FILE"
