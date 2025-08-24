#!/bin/bash
"""
Setup script for daily cron job
Configures automated daily invoice processing
"""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEDULER_DIR="$PROJECT_DIR/scheduler"
PYTHON_PATH=$(which python3)

echo "🚀 Setting up CrewAI Invoice Processing Cron Job"
echo "================================================"
echo "Project Directory: $PROJECT_DIR"
echo "Python Path: $PYTHON_PATH"
echo ""

# Make the daily processor executable
chmod +x "$SCHEDULER_DIR/daily_processor.py"

# Create the cron job entry
CRON_ENTRY="0 9 * * 1-5 cd $SCHEDULER_DIR && $PYTHON_PATH daily_processor.py >> daily_processor.log 2>&1"

echo "📋 Cron job entry:"
echo "$CRON_ENTRY"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_processor.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove existing entry and add new one
    (crontab -l 2>/dev/null | grep -v "daily_processor.py"; echo "$CRON_ENTRY") | crontab -
else
    echo "➕ Adding new cron job..."
    # Add new entry to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
fi

echo "✅ Cron job setup complete!"
echo ""
echo "📅 Schedule: Daily at 9:00 AM (Monday-Friday)"
echo "📂 Logs: $SCHEDULER_DIR/daily_processor.log"
echo ""
echo "🔧 To modify the schedule:"
echo "   1. Edit scheduler_config.json"
echo "   2. Run: crontab -e"
echo ""
echo "📊 To check cron jobs:"
echo "   crontab -l"
echo ""
echo "🗑️  To remove cron job:"
echo "   crontab -l | grep -v daily_processor.py | crontab -"
