# 📅 Calendar Update Automation Guide

This guide explains how to keep your weekly planner app's calendars up to date automatically.

## 🚀 **Update Options**

### **Option 1: Manual Updates (Simplest)**
```bash
# Update all calendars at once
python3 update_calendars.py

# Or update individual calendars
python3 kid_school_scraper.py        # School events only
python3 jewish_holidays_scraper.py   # Jewish holidays only
```

### **Option 2: Automated Weekly Updates (Recommended)**

#### **Setup Cron Job (macOS/Linux)**

1. **Open crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add one of these lines:**

   **Weekly updates (every Sunday at 6 AM):**
   ```bash
   0 6 * * 0 /Users/ronenvaisenberg/Desktop/weekly_planner/update_calendars.sh >> /Users/ronenvaisenberg/Desktop/weekly_planner/cron.log 2>&1
   ```

   **Twice weekly updates (Sunday and Wednesday at 6 AM):**
   ```bash
   0 6 * * 0,3 /Users/ronenvaisenberg/Desktop/weekly_planner/update_calendars.sh >> /Users/ronenvaisenberg/Desktop/weekly_planner/cron.log 2>&1
   ```

   **Daily updates (every day at 6 AM):**
   ```bash
   0 6 * * * /Users/ronenvaisenberg/Desktop/weekly_planner/update_calendars.sh >> /Users/ronenvaisenberg/Desktop/weekly_planner/cron.log 2>&1
   ```

3. **Save and exit** (usually Ctrl+X, then Y, then Enter)

#### **Setup Cron Job (Windows)**

1. **Open Task Scheduler** (search for "Task Scheduler" in Start menu)
2. **Create Basic Task:**
   - Name: "Weekly Calendar Update"
   - Trigger: Weekly, Sunday at 6:00 AM
   - Action: Start a program
   - Program: `python.exe`
   - Arguments: `update_calendars.py`
   - Start in: `C:\path\to\your\weekly_planner`

### **Option 3: GitHub Actions (Fully Automated)**

Create `.github/workflows/update_calendars.yml`:

```yaml
name: Update Calendars

on:
  schedule:
    # Run every Sunday at 6 AM UTC
    - cron: '0 6 * * 0'
  workflow_dispatch: # Allow manual trigger

jobs:
  update-calendars:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r scraper_requirements.txt
    
    - name: Update calendars
      run: |
        python3 update_calendars.py
    
    - name: Commit and push changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add *.csv
        git commit -m "Auto-update calendars $(date +'%Y-%m-%d')" || exit 0
        git push
```

## 📊 **Update Frequency Recommendations**

| Calendar Type | Recommended Frequency | Reason |
|---------------|----------------------|---------|
| **School Events** | Weekly (Sunday) | New events added regularly |
| **Jewish Holidays** | Monthly | Rarely change, 18-month limit |
| **Family Activities** | Manual | Only when you add/change activities |

## 🔧 **Testing Your Setup**

### **Test Manual Update:**
```bash
python3 update_calendars.py
```

### **Test Shell Script:**
```bash
./update_calendars.sh
```

### **Check Cron Logs:**
```bash
tail -f cron.log
```

### **Verify CSV Files:**
```bash
ls -la *.csv
wc -l *.csv  # Count lines in each CSV
```

## 📝 **Monitoring and Troubleshooting**

### **Check Update Logs:**
```bash
# View recent updates
tail -20 calendar_update.log

# View cron execution logs
tail -20 cron.log
```

### **Common Issues:**

1. **Permission Denied:**
   ```bash
   chmod +x update_calendars.sh
   ```

2. **Python Path Issues:**
   ```bash
   # Make sure you're in the right directory
   cd /Users/ronenvaisenberg/Desktop/weekly_planner
   python3 update_calendars.py
   ```

3. **Dependencies Missing:**
   ```bash
   pip3 install -r scraper_requirements.txt
   ```

4. **Cron Not Working:**
   ```bash
   # Check if cron is running
   sudo launchctl list | grep cron
   
   # Check cron logs
   grep CRON /var/log/syslog
   ```

## 🎯 **Recommended Setup**

For most users, I recommend:

1. **Start with manual updates** to test everything works
2. **Set up weekly cron job** (Sunday 6 AM) for school events
3. **Use GitHub Actions** if you want fully automated updates

### **Quick Start Commands:**
```bash
# Test the update system
python3 update_calendars.py

# Set up weekly cron job
crontab -e
# Add: 0 6 * * 0 /Users/ronenvaisenberg/Desktop/weekly_planner/update_calendars.sh

# Check if it's working
tail -f calendar_update.log
```

## 🔄 **What Gets Updated**

- **`school_events.csv`**: JLS and Ohlone school calendars
- **`jewish_holidays.csv`**: Jewish holidays (limited to 18 months)
- **`activities.csv`**: Your family activities (unchanged)

The app automatically combines all three sources when displaying schedules!
