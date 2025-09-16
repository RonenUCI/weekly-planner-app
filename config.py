"""
Configuration file for Weekly Planner App
Contains all constants and settings for navigation, filtering, and display
"""

# Navigation Settings
NAVIGATION_CONFIG = {
    # Time window for looking ahead for activities (in minutes)
    'look_ahead_minutes': 30,
    
    # Home address for fallback navigation
    'home_address': "628 Wellsbury Way, Palo Alto, CA 94306",
    
    # Driver types to exclude from navigation (case-insensitive)
    'excluded_drivers': ['walk', 'chabad'],
    
    # Activity types to exclude from navigation (case-insensitive)
    'excluded_activities': [],
    
    # Maximum number of navigation options to show
    'max_navigation_options': 5,
}

# Display Settings
DISPLAY_CONFIG = {
    # Date format for display
    'date_format': '%m/%d',
    'time_format': '%I:%M%p',
    'month_format': '%b.',
    
    # Table settings
    'address_truncate_length': 50,
    'time_truncate_length': 15,
    
    # Schedule settings
    'schedule_days_ahead': 7,  # How many days ahead to show in schedule
}

# Data Sources
DATA_CONFIG = {
    # Google Drive settings
    'google_drive_url': "https://docs.google.com/spreadsheets/d/1TS4zfU5BT1e80R5VMoZFkbLlH-yj2ZWGWHMd0qMO4wA/export?format=csv",
    'google_drive_timeout': 10,
    
    # CSV file names
    'school_events_file': 'school_events.csv',
    'jewish_holidays_file': 'jewish_holidays.csv',
    'activities_file': 'activities.csv',
}

# Timezone Settings
TIMEZONE_CONFIG = {
    # Pacific time offset from UTC (in hours)
    'pacific_offset_hours': -7,  # UTC-7 for Pacific Daylight Time
    
    # Timezone display name
    'timezone_name': 'Pacific Time',
}

# UI Settings
UI_CONFIG = {
    # Button styling
    'button_padding': '0.3rem 0.8rem',
    'button_gap': '10px',
    
    # Table styling
    'table_min_width': '600px',
    'table_cell_padding': '8px',
    
    # Spacing
    'day_header_padding': '0.2rem',
    'tip_container_padding': '0.2rem 0',
    'tip_margin_top': '-0.5rem',
}

# Required DataFrame columns
REQUIRED_COLUMNS = [
    'kid_name', 'activity', 'time', 'duration', 'frequency', 
    'days_of_week', 'start_date', 'end_date', 'address', 'pickup_driver', 'return_driver'
]

# Day abbreviations for schedule
DAY_ABBREV_MAP = {
    'monday': 'M', 
    'tuesday': 'T', 
    'wednesday': 'W', 
    'thursday': 'Th',
    'friday': 'F', 
    'saturday': 'S', 
    'sunday': 'S'
}

# Day order for display
DAYS_ORDER = ['M', 'T', 'W', 'Th', 'F', 'S', 'S']
