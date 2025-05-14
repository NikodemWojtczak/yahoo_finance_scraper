#!/bin/sh
set -e

# Load environment variables from .env file if it exists in /app
if [ -f /app/.env ]; then
  echo "Loading environment variables from /app/.env"
  # Source the .env file so its variables are exported to the environment
  set -a # Automatically export all variables subsequently defined or modified
  . /app/.env
  set +a
else
  echo "/app/.env file not found, skipping."
fi

# Start Xvfb in the background
echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Optionally, check if Xvfb started and give it a moment
if ps -p $XVFB_PID > /dev/null; then
    echo "Xvfb started successfully with PID $XVFB_PID."
else
    # This is not a fatal error for the entrypoint itself,
    # scraper.py might fail later if it truly needs Xvfb.
    echo "Xvfb may not have started correctly (PID $XVFB_PID not found). Continuing..."
fi
sleep 2 # Give Xvfb a moment to initialize regardless

# Execute the python scraper script, passing all arguments received by this entrypoint script
echo "Executing python /app/scraper.py $@ "
exec python /app/scraper.py "$@" 