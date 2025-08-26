#!/bin/bash
# Calendar Update Shell Script
# Use this script for cron jobs or manual execution

# Set the working directory to the script's location
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the calendar update
echo "Starting calendar update at $(date)"
python3 update_calendars.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "Calendar update completed successfully at $(date)"
else
    echo "Calendar update failed at $(date)"
    exit 1
fi
