#!/bin/bash
# Calendar Update and Auto-Push Script
# This script updates calendars and pushes changes to GitHub automatically

# Set the working directory to the script's location
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting calendar update and push at $(date)"

# Step 1: Update calendars
echo "Step 1: Updating calendars..."
python3 update_calendars.py
UPDATE_EXIT_CODE=$?

if [ $UPDATE_EXIT_CODE -eq 0 ]; then
    echo "✅ Calendar update successful"
    
    # Step 2: Check if there are changes to commit
    if git diff --quiet *.csv; then
        echo "ℹ️  No changes to commit - CSV files are up to date"
    else
        echo "Step 2: Committing and pushing changes..."
        
        # Add CSV files
        git add *.csv
        
        # Commit with timestamp
        COMMIT_MESSAGE="Auto-update calendars $(date +'%Y-%m-%d %H:%M')"
        git commit -m "$COMMIT_MESSAGE"
        
        # Push to GitHub
        if git push origin main; then
            echo "✅ Successfully pushed to GitHub"
            echo "📱 Streamlit app will now show updated data"
        else
            echo "❌ Failed to push to GitHub"
            exit 1
        fi
    fi
else
    echo "❌ Calendar update failed"
    exit 1
fi

echo "Calendar update and push completed at $(date)"
