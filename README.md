# Weekly Planner - Afterschool Activities

A comprehensive Streamlit application for managing afterschool activities for multiple kids, including driver scheduling, weekly planning, and automatic calendar integration from multiple sources.

## Features

- **Kid Manager**: Add and manage individual kid schedules with activity tracking
- **Driver View**: View schedules organized by driver with clickable addresses
- **Weekly View**: Complete weekly schedule table with Google Maps integration
- **Data Management**: Import/export CSV data with the specified schema
- **Calendar Integration**: Automatic loading of school events and Jewish holidays from ICS feeds
- **Unified Schedule**: Combined view of family activities, school events, and religious observances

## Features

- **Kid Manager**: Add and manage individual kid schedules with activity tracking
- **Driver View**: View schedules organized by driver with clickable addresses
- **Weekly View**: Complete weekly schedule table with Google Maps integration
- **Data Management**: Import/export CSV data with the specified schema

## Data Schema

The application uses a CSV file with the following columns:
- `kid_name`: Name of the child
- `activity`: Name of the activity
- `time`: Time of the activity (HH:MM format)
- `duration`: Duration in hours
- `frequency`: daily, weekly, or bi-weekly
- `days_of_week`: List of days (monday, tuesday, etc.)
- `address`: Location address
- `pickup_driver`: Driver for pickup
- `return_driver`: Driver for return

## Installation

### **Main Application**
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

### **Calendar Scrapers**
1. Install scraper dependencies:
```bash
pip install -r scraper_requirements.txt
```

2. Verify scrapers work:
```bash
# Test school scraper
python3 kid_school_scraper.py

# Test Jewish holidays scraper
python3 jewish_holidays_scraper.py

# Test unified scraper
python3 unified_calendar_scraper.py
```

## Usage

1. **Data Management**: Start by importing existing CSV data or create new activities
2. **Kid Manager**: Add activities for each kid and view their daily/weekly hour totals
3. **Driver View**: Select a driver to see their pickup/return schedule
4. **Weekly View**: View the complete weekly schedule with clickable addresses

## Features

- **Real-time Statistics**: Daily and weekly hour calculations for each kid
- **Interactive Charts**: Visual representation of daily hours
- **Google Maps Integration**: Clickable addresses that open in Google Maps
- **CSV Import/Export**: Full data persistence and backup capabilities
- **Responsive Design**: Works on desktop and mobile devices

## Calendar Integration

The app automatically integrates calendar events from multiple ICS feeds:

### **School Calendars**
- **JLS Middle School**: `https://jls.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=7`
- **Ohlone Elementary**: `https://ohlone.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=45`

### **Jewish Holidays**
- **Hebcal Feed**: `https://download.hebcal.com/v4/CAEQARgBIAEoATABQAGAAQGYAQGgAQH4AQU/hebcal.ics`

### **Updating Calendar Data**

#### **Option 1: Individual Scrapers**
```bash
# Update school events only
python3 kid_school_scraper.py

# Update Jewish holidays only
python3 jewish_holidays_scraper.py
```

#### **Option 2: Unified Scraper (Recommended)**
```bash
# Update all calendar sources at once
python3 unified_calendar_scraper.py
```

The unified scraper will:
1. Download and parse all ICS feeds
2. Convert events to the planner's CSV format
3. Save to separate files (`school_events.csv`, `jewish_holidays.csv`)
4. Optionally merge with existing `activities.csv`

#### **Option 3: Manual ICS Feed Updates**
If you need to update the ICS feed URLs:

1. **Edit `kid_school_scraper.py`**:
   ```python
   self.school_feeds = {
       'JLS': {
           'name': 'Jane Lathrop Stanford Middle School',
           'url': 'YOUR_NEW_JLS_ICS_URL',
           'address': 'YOUR_SCHOOL_ADDRESS'
       },
       'Ohlone': {
           'name': 'Ohlone Elementary School',
           'url': 'YOUR_NEW_OHLONE_ICS_URL',
           'address': 'YOUR_SCHOOL_ADDRESS'
       }
   }
   ```

2. **Edit `jewish_holidays_scraper.py`**:
   ```python
   self.hebcal_url = "YOUR_NEW_HEBCAL_ICS_URL"
   ```

3. **Add New Calendar Sources**:
   - Create a new scraper class inheriting from `ICSCalendarScraper`
   - Implement the required abstract methods
   - Add to the unified scraper if desired

### **Calendar Data Files**
- `activities.csv`: Family activities (editable)
- `school_events.csv`: School calendar events (auto-generated)
- `jewish_holidays.csv`: Jewish holidays and observances (auto-generated)

### **Scheduling Calendar Updates**
For automatic updates, consider setting up a cron job or scheduled task:

```bash
# Example: Update calendars daily at 6 AM
0 6 * * * cd /path/to/weekly_planner && python3 unified_calendar_scraper.py

# Example: Update calendars weekly on Sunday at 2 AM
0 2 * * 0 cd /path/to/weekly_planner && python3 unified_calendar_scraper.py
```

## File Structure

- `app.py`: Main Streamlit application
- `requirements.txt`: Python dependencies for the main app
- `scraper_requirements.txt`: Python dependencies for calendar scrapers
- `activities.csv`: Family activities data storage (created automatically)
- `school_events.csv`: School calendar events (auto-generated)
- `jewish_holidays.csv`: Jewish holidays (auto-generated)
- `ics_calendar_scraper.py`: Base class for ICS calendar scraping
- `kid_school_scraper.py`: School calendar scraper
- `jewish_holidays_scraper.py`: Jewish holidays scraper
- `unified_calendar_scraper.py`: Combined calendar scraper
- `README.md`: This documentation file

## Troubleshooting

### **Common Issues**

#### **Calendar Scrapers Not Working**
- **Error**: `ModuleNotFoundError: No module named 'icalendar'`
  - **Solution**: Install scraper requirements: `pip install -r scraper_requirements.txt`

- **Error**: `requests.exceptions.ConnectionError`
  - **Solution**: Check internet connection and ICS feed URLs

- **Error**: `KeyError: 'days_of_week'`
  - **Solution**: Ensure CSV files have the correct column structure

#### **App Not Loading Calendar Events**
- **Issue**: Only family activities showing, no school/Jewish events
  - **Solution**: Run the calendar scrapers first to generate the required CSV files

- **Issue**: App crashes with `TypeError: object of type 'float' has no len()`
  - **Solution**: This usually indicates corrupted data in CSV files. Delete the generated CSV files and re-run scrapers.

#### **Performance Issues**
- **Issue**: App loads slowly with many calendar events
  - **Solution**: Consider filtering events by date range in the scrapers
  - **Solution**: Use the individual scrapers instead of the unified scraper for specific updates

### **Getting Help**

1. **Check the logs**: Look for error messages in the terminal when running scrapers
2. **Verify ICS feeds**: Test ICS URLs in a web browser to ensure they're accessible
3. **Test individual components**: Run scrapers one by one to isolate issues
4. **Check file permissions**: Ensure the app can read/write CSV files in the project directory

### **Data Backup**

Before running calendar updates, consider backing up your data:
```bash
# Backup family activities
cp activities.csv activities_backup_$(date +%Y%m%d).csv

# Backup calendar events
cp school_events.csv school_events_backup_$(date +%Y%m%d).csv
cp jewish_holidays.csv jewish_holidays_backup_$(date +%Y%m%d).csv
``` 