# Kid School Calendar Scraper

This script automatically downloads calendar events from multiple school ICS feeds and converts them to your weekly planner CSV format. Currently supports JLS Middle School and Ohlone Elementary.

## Features

- **Multi-School Support**: Downloads events from multiple PAUSD schools
- **Automatic ICS Download**: Uses official school calendar feeds
- **Smart Event Categorization**: Automatically categorizes events by type
- **Date Filtering**: Only downloads current/future events (no past events)
- **CSV Conversion**: Converts events to your weekly planner format
- **Duplicate Prevention**: Automatically avoids adding duplicate events
- **Fallback Data**: Includes sample events if feeds are unavailable

## Supported Schools

### JLS Middle School
- **URL**: https://jls.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=7
- **Address**: 480 E Meadow Dr, Palo Alto, CA
- **Grades**: 6-8

### Ohlone Elementary
- **URL**: https://ohlone.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=45
- **Address**: 950 Amarillo Ave, Palo Alto, CA 94303
- **Grades**: K-5

## Installation

1. Install the required dependencies:
```bash
pip install -r scraper_requirements.txt
```

## Usage

### Basic Usage
```bash
python3 kid_school_scraper.py
```

### What It Does

1. **Downloads Multiple Feeds**: Downloads ICS feeds from all configured schools
2. **Parses Events**: Extracts all event details using the iCalendar standard
3. **Filters by Date**: Only includes current/future events
4. **Combines Results**: Merges events from all schools into one dataset
5. **Converts Format**: Transforms events to match your CSV schema:
   - `kid_name`: Set to "All" (school events affect all kids)
   - `activity`: School prefix + event name (e.g., "JLS: First Day of School")
   - `time`: Start time in 24-hour format
   - `duration`: Calculated duration in hours
   - `frequency`: Set to "one-time" for school events
   - `days_of_week`: Day of the week the event occurs
   - `start_date` & `end_date`: Same date (one-time events)
   - `address`: School address or event location
   - `pickup_driver` & `return_driver`: Set to "N/A"

### Event Categories

The scraper automatically categorizes events:
- **Holiday**: No school days (Labor Day, Veterans Day, etc.)
- **Minimum Day**: Early dismissal days
- **Staff Development**: Teacher training days
- **School Event**: Picture day, assemblies, etc.
- **Parent Event**: Back to School Night, PTA meetings, coffee hours
- **School Year**: First/last day of school

### Output Options

After parsing, you'll be prompted to choose:

1. **Merge with existing activities.csv**: Adds new events to your main CSV
2. **Save as separate school_events.csv only**: Creates a separate file
3. **View parsed events**: Shows the events without saving

## Example Events

The scraper will find events like:

### JLS Events
- First Day of School (August 14)
- Back to School Night (August 27)
- Staff Development Days
- Holidays and breaks

### Ohlone Events
- Back to School Night (August 28)
- Minimum Days
- PTA meetings and events
- Farm-related activities
- Community events

## Advantages of Multi-School ICS Feeds

- ✅ **Comprehensive Coverage**: Get events from all your kids' schools
- ✅ **More Reliable**: Standard format, less likely to break
- ✅ **Complete Data**: Includes all event details, times, descriptions
- ✅ **Official Source**: Direct from school calendar systems
- ✅ **Easier Maintenance**: No need to update parsing logic
- ✅ **Better Accuracy**: Exact times, durations, and locations

## Troubleshooting

### If ICS Feeds Fail
The script includes fallback data with known events for both schools.

### Common Issues
- **Network Issues**: Check your internet connection
- **Feed Changes**: Schools may update their ICS feed URLs
- **Authentication**: Some feeds require login (not expected for public schools)

## Integration with Weekly Planner

Once events are added to your CSV:
- They'll appear in the "Weekly View" as school activities
- They'll be included in driver schedules
- They'll show up in weekly summaries
- Addresses will link to school locations in Google Maps
- School prefixes will help identify which school each event is from

## Maintenance

- **Regular Updates**: Run monthly to get new events
- **School Year Changes**: Update the year parameter for new school years
- **Manual Review**: Always review parsed events before merging
- **Adding Schools**: Easy to add new schools by updating the `school_feeds` dictionary

## Legal Notes

- This script uses the official public ICS feeds
- Respects website terms of service
- Uses standard calendar data exchange protocols
- For personal use only

## Files

- `kid_school_scraper.py`: Main multi-school scraper script
- `scraper_requirements.txt`: Python dependencies
- `KID_SCHOOL_SCRAPER_README.md`: This documentation
- `school_events.csv`: Output file (created when run)
- `activities.csv`: Your main weekly planner CSV (updated when merging)

## Technical Details

The script uses the `icalendar` library to parse ICS feeds, which is the same format used by:
- Google Calendar
- Apple Calendar
- Microsoft Outlook
- Most calendar applications

This ensures maximum compatibility and reliability across all supported schools.

## Adding More Schools

To add more schools, simply update the `school_feeds` dictionary in the script:

```python
self.school_feeds = {
    'JLS': { ... },
    'Ohlone': { ... },
    'NewSchool': {
        'name': 'New School Name',
        'url': 'https://newschool.org/calendar.ics',
        'address': 'School Address'
    }
}
```
