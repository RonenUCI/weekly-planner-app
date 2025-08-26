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
- `update_calendars.py`: Calendar update script
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