# Weekly Planner - Afterschool Activities

A Streamlit app for managing afterschool activities for multiple kids, with automatic calendar integration from school events and Jewish holidays.

## 🚀 **Quick Start**

### **Run the App**
```bash
streamlit run app.py
```

### **Update Calendars & Deploy**
```bash
python3 update_calendars.py && git add . && git status && echo "Type 'yes' to commit and push:" && read confirm && [ "$confirm" = "yes" ] && git commit -m "Weekly calendar update $(date +'%Y-%m-%d')" && git push origin main || echo "Update aborted."
```

### **Commit All Pending Changes**
```bash
git add . && git commit -m "Update: $(date +'%Y-%m-%d %H:%M')" && git push origin main
```

## 🌐 **Live App**

**URL**: https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/

## ⚙️ **URL Parameters**

The app supports several URL parameters for different views and testing:

### **Time Override (Testing)**
Test the app at different times by adding the `?time=` parameter:

```
# Test at 2:30 PM
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?time=14:30

# Test at 8:00 AM
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?time=08:00

# Test at 6:00 PM
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?time=18:00

# Test with seconds
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?time=14:30:45
```

**What it does:**
- Overrides the current time for smart navigation logic
- Shows activities for the day corresponding to your test time
- Displays "Testing Mode" indicator in the sidebar
- Works in both weekly and monthly views

### **Monitor Mode (Wall Dashboard)**
Display a 30-day wall dashboard by adding the `?mode=monitor` parameter:

```
# Wall dashboard view
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?mode=monitor

# Wall dashboard with time override
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?mode=monitor&time=14:30
```

**What it does:**
- Shows a compact 30-day calendar view
- Optimized for wall displays and tablets
- Auto-refreshes every 30 seconds
- Perfect for family room or kitchen displays

### **Combined Parameters**
You can combine multiple parameters:

```
# Monitor mode with time override
https://weekly-planner-app-k9qrftskhzdsbxmd9ppxfr.streamlit.app/?mode=monitor&time=09:00
```

## ✨ **Features**

- **Kid Manager**: Add/manage individual schedules with activity tracking
- **Driver View**: View schedules organized by driver with clickable addresses
- **Weekly View**: Complete weekly schedule with Google Maps integration
- **Calendar Integration**: School events + Jewish holidays from ICS feeds
- **Real-time Stats**: Daily/weekly hour calculations per kid
- **Mobile Optimized**: Responsive design for all devices

## 📊 **Data Schema**

CSV columns: `kid_name`, `activity`, `time`, `duration`, `frequency`, `days_of_week`, `address`, `pickup_driver`, `return_driver`, `start_date`, `end_date`

## 🛠️ **Installation**

```bash
# Main app
pip install -r requirements.txt

# Calendar scrapers
pip install -r scraper_requirements.txt
```

## 📅 **Calendar Sources**

- **JLS Middle School**: `https://jls.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=7`
- **Ohlone Elementary**: `https://ohlone.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=45`
- **Jewish Holidays**: `https://download.hebcal.com/v4/CAEQARgBIAEoATABQAGAAQGYAQGgAQH4AQU/hebcal.ics`

## 🔄 **Updating Calendars**

### **Manual Update**
```bash
python3 update_calendars.py
```

### **Individual Updates**
```bash
python3 kid_school_scraper.py        # School events only
python3 jewish_holidays_scraper.py   # Jewish holidays only
```

### **Automated Updates (Optional)**
```bash
# Weekly cron job (Sunday 6 AM)
0 6 * * 0 /Users/ronenvaisenberg/Desktop/weekly_planner/update_calendars.sh

# Or use GitHub Actions (see .github/workflows/update_calendars.yml)
```

## 📁 **Key Files**

- `app.py`: Main Streamlit application
- `update_calendars.py`: Calendar update script (consolidated)
- `activities.csv`: Family activities (editable)
- `school_events.csv`: School calendar events (auto-generated)
- `jewish_holidays.csv`: Jewish holidays (auto-generated)

## 🚨 **Troubleshooting**

- **Missing modules**: `pip install -r scraper_requirements.txt`
- **App crashes**: Delete generated CSV files and re-run scrapers
- **No calendar events**: Run `python3 update_calendars.py` first

## 🎯 **Weekly Workflow**

1. **Update calendars**: `python3 update_calendars.py`
2. **Review changes**: `git status`
3. **Commit & push**: Use the one-command update above
4. **Streamlit app updates automatically** from GitHub

---

**Need help?** Check the logs: `tail -20 calendar_update.log` 