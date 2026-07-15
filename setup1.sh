#!/bin/bash

clear

# Set the path to the file uploads directory.
UPLOADS_PATH="/mnt/storage/personal-drive/uploads"

# Set the port for the application to listen on.
PORT=2926

# Verify Root Permissions.
if [ "$EUID" -ne 0 ]
then
    echo "Error: Run as root."
    exit 1
fi

# Check if Python packages are installed.
echo "Start package installation..."
python3 -m pip install -r modules.txt
echo "Package installation complete."

# Check if the database needs to be migrated.
echo "Start database migration..."
if [ ! "$(ls -A migrations/versions/)" ]
then
    echo "Creating migration files..."
    alembic revision --autogenerate -m "init"
fi
echo "Applying migrations..."
alembic upgrade head
echo "Database migration complete."

# Check if the uploads directory exists, if not create it.
if [ ! -d "$UPLOADS_PATH" ]
then
    echo "Creating uploads directory..."
    mkdir -p "$UPLOADS_PATH"
    echo "Uploads directory created at $UPLOADS_PATH."
else
    echo "Uploads directory already exists at $UPLOADS_PATH."
fi

# Start the application using uvicorn and cloudflared.
echo "Starting the application..."
echo "Run the \`setup2.sh\` file in a new terminal to complete the web server setup."
uvicorn main:app --host 127.0.0.1 --port $PORT --reload
