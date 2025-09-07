import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import webbrowser
import os
from typing import Dict, List, Tuple
import json

def load_activities_from_google_drive():
    """Load activities from Google Drive - no fallback to local file"""
    # Google Drive shareable URL for your activities spreadsheet
    google_drive_url = "https://docs.google.com/spreadsheets/d/1TS4zfU5BT1e80R5VMoZFkbLlH-yj2ZWGWHMd0qMO4wA/export?format=csv"
    
    try:
        import requests
        from io import StringIO
        import time
        
        print("Attempting to load activities from Google Drive...")
        # Add timestamp to prevent caching
        timestamp = int(time.time())
        cache_bust_url = f"{google_drive_url}&t={timestamp}"
        
        response = requests.get(cache_bust_url, timeout=10)
        response.raise_for_status()
        
        # Read CSV content from Google Drive
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty:
            raise ValueError("Google Sheet is empty - no activities found")
        
        # Convert date columns to datetime objects
        if 'start_date' in df.columns:
            df['start_date'] = pd.to_datetime(df['start_date']).dt.date
        if 'end_date' in df.columns:
            df['end_date'] = pd.to_datetime(df['end_date']).dt.date
        
        # Process days_of_week column if it exists
        if 'days_of_week' in df.columns:
            df['days_of_week'] = df['days_of_week'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.strip() else []
            )
        
        print(f"✅ Successfully loaded {len(df)} activities from Google Drive")
        
        # Debug: Show date ranges of activities
        if not df.empty and 'start_date' in df.columns and 'end_date' in df.columns:
            print(f"DEBUG: Activity date ranges:")
            for idx, row in df.iterrows():
                print(f"  {row.get('activity', 'Unknown')}: {row['start_date']} to {row['end_date']}")
        
        return df
        
    except Exception as e:
        error_msg = f"❌ Failed to load activities from Google Drive: {str(e)}"
        print(error_msg)
        raise RuntimeError(error_msg)

# Add this function at the top level, before the main() function
def make_address_clickable(address):
    """Convert address to clickable Google Maps link with truncated display text"""
    # Handle NaN/None values
    if pd.isna(address) or address is None:
        print(f"DEBUG: Address is NaN/None: {address}")
        return "No address"
    
    # Convert to string if it's not already
    address_str = str(address)
    print(f"DEBUG: Processing address: '{address_str}' (type: {type(address)})")
    
    # Truncate address to 15 characters for display
    display_text = address_str[:15] + "..." if len(address_str) > 15 else address_str
    return f'<a href="https://www.google.com/maps/search/?api=1&query={address_str.replace(" ", "+")}" target="_blank">{display_text}</a>'

def analyze_navigation_context(weekly_schedule, current_time):
    """Analyze current navigation context and return navigation options"""
    home_address = "628 Wellsbury Way, Palo Alto"
    navigation_options = []
    
    if weekly_schedule.empty:
        return "home", home_address, "No activities scheduled", []
    
    # Get current day from the passed current_time
    today = current_time.date()
    current_day_name = today.strftime('%A').lower()
    
    # Get today's activities - convert current day to abbreviated format
    day_abbrev_map = {
        'monday': 'M', 'tuesday': 'T', 'wednesday': 'W', 'thursday': 'Th',
        'friday': 'F', 'saturday': 'S', 'sunday': 'S'
    }
    current_day_abbrev = day_abbrev_map.get(current_day_name, current_day_name.capitalize())
    print(f"DEBUG: Looking for activities on {current_day_abbrev} (from {current_day_name})")
    print(f"DEBUG: Available days in weekly_schedule: {weekly_schedule['Day'].unique() if not weekly_schedule.empty else 'Empty'}")
    
    today_activities = weekly_schedule[weekly_schedule['Day'] == current_day_abbrev]
    print(f"DEBUG: Found {len(today_activities)} activities for {current_day_abbrev}")
    
    if today_activities.empty:
        return "home", home_address, "No activities today", []
    
    # Find activities within the next 30 minutes
    thirty_minutes_later = (current_time + timedelta(minutes=30)).time()
    
    current_activities = []
    upcoming_activities = []
    
    for _, activity in today_activities.iterrows():
        try:
            # Skip activities with "walk" or "chabad" as driver
            driver = str(activity.get('Driver', '')).lower()
            if 'walk' in driver or 'chabad' in driver:
                continue
                
            # Parse start and end times
            start_time_str = activity['Time'].split('-')[0]
            end_time_str = activity['Time'].split('-')[1]
            start_time = pd.to_datetime(start_time_str, format='%H:%M').time()
            end_time = pd.to_datetime(end_time_str, format='%H:%M').time()
            
            # Check if we're currently in this activity
            if start_time <= current_time.time() <= end_time:
                current_activities.append({
                    'activity': activity,
                    'type': 'current',
                    'time_info': f"Now until {end_time_str}"
                })
            
            # Check if this activity starts within the next 30 minutes
            elif start_time <= thirty_minutes_later and start_time > current_time.time():
                upcoming_activities.append({
                    'activity': activity,
                    'type': 'upcoming',
                    'time_info': f"Starts at {start_time_str}"
                })
                
        except Exception as e:
            print(f"Error parsing time for activity {activity.get('Activity', 'Unknown')}: {e}")
            continue
    
    # Determine navigation logic
    total_relevant_activities = len(current_activities) + len(upcoming_activities)
    
    if total_relevant_activities == 0:
        # No activities within 30 minutes, go home
        return "home", home_address, "No activities within 30 minutes", []
    
    elif total_relevant_activities == 1:
        # Only one relevant activity, navigate there
        if current_activities:
            activity = current_activities[0]['activity']
            address = str(activity['Address']) if pd.notna(activity['Address']) else home_address
            return "activity", address, f"Current: {activity['Activity']}", []
        else:
            activity = upcoming_activities[0]['activity']
            address = str(activity['Address']) if pd.notna(activity['Address']) else home_address
            return "activity", address, f"Next: {activity['Activity']}", []
    
    else:
        # Multiple options, return all for user selection
        options = []
        seen_addresses = set()  # Track addresses to avoid duplicates
        
        # Add home option
        options.append({
            'type': 'home',
            'address': home_address,
            'description': '🏠 Home (628 Wellsbury Way, Palo Alto)',
            'reason': 'No clear next destination'
        })
        seen_addresses.add(home_address)
        
        # Add current activities (deduplicated by address)
        for item in current_activities:
            activity = item['activity']
            address = str(activity['Address']) if pd.notna(activity['Address']) else home_address
            
            # Skip if driver is "walk" or "chabad"
            driver = str(activity.get('Driver', '')).lower()
            if 'walk' in driver or 'chabad' in driver:
                print(f"DEBUG: Skipping activity {activity['Activity']} due to driver: {driver}")
                continue
                
            if address not in seen_addresses:
                print(f"DEBUG: Adding current activity: {activity['Activity']} at {address}")
                options.append({
                    'type': 'current',
                    'address': address,
                    'description': f"🔄 {activity['Activity']} (Current - {item['time_info']})",
                    'reason': 'Currently in progress'
                })
                seen_addresses.add(address)
            else:
                print(f"DEBUG: Skipping duplicate address: {address}")
        
        # Add upcoming activities (deduplicated by address)
        for item in upcoming_activities:
            activity = item['activity']
            address = str(activity['Address']) if pd.notna(activity['Address']) else home_address
            
            # Skip if driver is "walk" or "chabad"
            driver = str(activity.get('Driver', '')).lower()
            if 'walk' in driver or 'chabad' in driver:
                print(f"DEBUG: Skipping upcoming activity {activity['Activity']} due to driver: {driver}")
                continue
                
            if address not in seen_addresses:
                print(f"DEBUG: Adding upcoming activity: {activity['Activity']} at {address}")
                options.append({
                    'type': 'upcoming',
                    'address': address,
                    'description': f"⏰ {activity['Activity']} (Next - {item['time_info']})",
                    'reason': 'Starting soon'
                })
                seen_addresses.add(address)
            else:
                print(f"DEBUG: Skipping duplicate address: {address}")
        
        # Count unique destinations (excluding home)
        unique_destinations = len(options) - 1  # Subtract 1 for the home option
        total_options = len(options)
        
        if unique_destinations == 0:
            return "multiple", None, f"Multiple options available (Home only)", options
        elif unique_destinations == 1:
            return "multiple", None, f"Multiple options available (Home + 1 destination)", options
        else:
            destination_text = "destinations" if unique_destinations > 1 else "destination"
            return "multiple", None, f"Multiple options available (Home + {unique_destinations} {destination_text})", options

# Page configuration optimized for mobile
st.set_page_config(
    page_title="Weekly Planner",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapse sidebar on mobile
)

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
            margin-bottom: 1rem !important;
        }
        .metric-card {
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .activity-card {
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .driver-schedule {
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        .summary-stats {
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        /* Ultra-compact tables for mobile */
        .dataframe {
            font-size: 0.7rem !important;
        }
        .dataframe th, .dataframe td {
            padding: 0.2rem !important;
            text-align: left !important;
        }
        /* Reduce padding in expanders */
        .streamlit-expanderHeader {
            padding: 0.5rem !important;
        }
        /* Compact form elements */
        .stSelectbox, .stDateInput, .stTimeInput {
            margin-bottom: 0.5rem !important;
        }
        /* Force horizontal layout for selectors */
        [data-testid="column"] {
            flex-direction: row !important;
            display: flex !important;
        }
        [data-testid="column"] > div {
            flex: 1 !important;
            min-width: 0 !important;
        }
        /* Override Streamlit's mobile stacking */
        .row-widget.stHorizontal {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        .row-widget.stHorizontal > div {
            flex: 1 !important;
            min-width: 0 !important;
        }
        /* Fix dropdown and button styling on mobile */
        .stSelectbox > div > div {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox > div > div > div {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox [data-baseweb="select"] {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox [data-baseweb="select"] > div {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox [data-baseweb="select"] > div > div {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox [data-baseweb="popover"] {
            background-color: #f8f9fa !important;
        }
        .stSelectbox [data-baseweb="popover"] > div {
            background-color: #f8f9fa !important;
        }
        .stSelectbox [data-baseweb="popover"] li {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stSelectbox [data-baseweb="popover"] li:hover {
            background-color: #e9ecef !important;
            color: #000000 !important;
        }
        .stLinkButton {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stLinkButton > a {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .stButton > button {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        /* Force navigation buttons to stay on same row on mobile */
        [data-testid="column"]:nth-child(2),
        [data-testid="column"]:nth-child(3) {
            flex: 0 0 auto !important;
            min-width: 120px !important;
            max-width: 150px !important;
        }
        /* Ensure buttons don't wrap on mobile */
        .stLinkButton, .stButton {
            width: 100% !important;
            margin: 0 !important;
        }
        .stLinkButton > a, .stButton > button {
            width: 100% !important;
            text-align: center !important;
            font-size: 0.8rem !important;
            padding: 0.3rem 0.5rem !important;
        }
    }
    
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .activity-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .driver-schedule {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .address-link {
        color: #007bff;
        text-decoration: none;
    }
    .address-link:hover {
        text-decoration: underline;
    }
    .summary-stats {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Ultra-compact mobile table styles */
    .mobile-table {
        font-size: 0.65rem !important;
        overflow-x: auto;
    }
    .mobile-table th, .mobile-table td {
        padding: 0.15rem !important;
        white-space: nowrap;
    }
    /* Enhanced day headers with better visibility */
    .day-header {
        background-color: #1f77b4 !important;
        color: white !important;
        padding: 0.75rem !important;
        border-radius: 0.25rem !important;
        margin-bottom: 0.5rem !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        text-align: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Monthly view styles */
    .monitor-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #0066cc !important;
        background-color: #ffffff !important;
    }
    .monitor-day {
        background-color: #f8f9fa !important;
        color: #000000 !important;
        padding: 0.15rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        border-left: 2px solid #0066cc;
        min-height: 30px;
        border: 1px solid #dee2e6;
    }
    .monitor-day-today {
        background-color: #fff3cd !important;
        color: #000000 !important;
        padding: 0.15rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        border-left: 3px solid #ffc107;
        min-height: 30px;
        box-shadow: 0 0 5px rgba(255, 193, 7, 0.3);
        border: 2px solid #ffc107;
    }
    .monitor-day-header {
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.05rem;
        color: #0066cc !important;
        background-color: transparent !important;
        text-align: center;
        padding: 0.05rem;
        line-height: 1.0;
    }
    .monitor-activity {
        background-color: transparent !important;
        color: #000000 !important;
        padding: 0.1rem 0;
        margin: 0.05rem 0;
        border: none;
        font-size: 0.6rem;
        line-height: 1.1;
    }
    .monitor-activity-time {
        font-size: 0.6rem;
        font-weight: bold;
        color: #0066cc !important;
        background-color: transparent !important;
        display: inline;
    }
    .monitor-activity-details {
        font-size: 0.6rem;
        margin-left: 0.3rem;
        color: #000000 !important;
        background-color: transparent !important;
        display: inline;
    }
    .monitor-no-activities {
        font-size: 0.6rem;
        text-align: center;
        color: #6c757d !important;
        background-color: transparent !important;
        padding: 0.2rem;
    }
    
    /* Mobile-specific fixes for monthly view */
    @media (max-width: 768px) {
        /* Force light grey background on main container */
        .main .block-container {
            background-color: #f5f5f5 !important;
            color: #1e293b !important;
        }
        
        /* Override Streamlit's default dark theme - but preserve sidebar */
        .stApp {
            background-color: #f5f5f5 !important;
            color: #1e293b !important;
        }
        
        /* Keep sidebar with light grey theme */
        .stSidebar {
            background-color: #f5f5f5 !important;
            color: #1e293b !important;
        }
        
        /* Keep main content area light grey */
        .main .block-container {
            background-color: #f5f5f5 !important;
            color: #1e293b !important;
        }
        
        .monitor-header {
            font-size: 1.5rem !important;
            color: #0066cc !important;
            background-color: #ffffff !important;
        }
        .monitor-day {
            background-color: #f8f9fa !important;
            color: #000000 !important;
        }
        .monitor-day-today {
            background-color: #fff3cd !important;
            color: #000000 !important;
        }
        .monitor-day-header {
            color: #0066cc !important;
            background-color: transparent !important;
        }
        .monitor-activity {
            color: #000000 !important;
            background-color: transparent !important;
        }
        .monitor-activity-time {
            color: #0066cc !important;
            background-color: transparent !important;
        }
        .monitor-activity-details {
            color: #000000 !important;
            background-color: transparent !important;
        }
        .monitor-no-activities {
            color: #6c757d !important;
            background-color: transparent !important;
        }
        
        /* Force all text to be visible */
        div[data-testid="stMarkdownContainer"] {
            color: #000000 !important;
            background-color: transparent !important;
        }
        
        /* Override any dark theme styles */
        .css-1d391kg {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
    }
    
    /* Additional mobile overrides */
    @media (max-width: 768px) {
        /* Target all possible Streamlit containers */
        .stApp > div {
            background-color: #f5f5f5 !important;
        }
        
        /* Force visibility on all text elements - but exclude Streamlit UI elements */
        p:not(.stButton > div > p):not(.stSelectbox > div > p):not(.stRadio > div > p), 
        div:not(.stButton):not(.stSelectbox):not(.stRadio):not(.stSidebar):not(.stSidebar > div), 
        span:not(.stButton > div > span):not(.stSelectbox > div > span), 
        td, th {
            color: #1e293b !important;
        }
        
        /* Fix Streamlit UI elements */
        .stButton > div > p, .stButton > div > span {
            color: #ffffff !important;
        }
        
        .stSelectbox > div > p, .stSelectbox > div > span {
            color: #ffffff !important;
        }
        
        .stRadio > div > p, .stRadio > div > span {
            color: #ffffff !important;
        }
        
        /* Fix sidebar text */
        .stSidebar p, .stSidebar div, .stSidebar span {
            color: #1e293b !important;
        }
        
        /* Fix mobile menu (hamburger menu) text */
        .css-1d391kg p, .css-1d391kg div, .css-1d391kg span {
            color: #1e293b !important;
        }
        
        /* Fix mobile sidebar overlay text */
        .stSidebar .css-1d391kg p, .stSidebar .css-1d391kg div, .stSidebar .css-1d391kg span {
            color: #1e293b !important;
        }
        
        /* Fix any mobile menu containers */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
            color: #1e293b !important;
        }
        
        /* Additional mobile menu fixes */
        .stSidebar .css-1d391kg, .stSidebar .css-1d391kg * {
            color: #1e293b !important;
        }
        
        /* Fix mobile menu buttons and links */
        .stSidebar button, .stSidebar .stButton, .stSidebar a {
            color: #1e293b !important;
        }
        
        /* Fix mobile menu radio buttons and selectboxes */
        .stSidebar .stRadio, .stSidebar .stSelectbox {
            color: #1e293b !important;
        }
        
        .stSidebar .stRadio label, .stSidebar .stSelectbox label {
            color: #1e293b !important;
        }
        
        /* Fix dropdown menus and selectbox options */
        .stSelectbox > div > div > div, .stSelectbox > div > div > div > div {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* Fix dropdown option text */
        .stSelectbox .css-1n76uvr, .stSelectbox .css-1n76uvr * {
            color: #1e293b !important;
        }
        
        /* Fix all selectbox elements */
        .stSelectbox, .stSelectbox *, .stSelectbox > div, .stSelectbox > div * {
            color: #1e293b !important;
        }
        
        /* Fix mobile menu when closed (<<) */
        .stSidebar .css-1d391kg, .stSidebar .css-1d391kg * {
            color: #1e293b !important;
        }
        
        /* Fix any remaining text in sidebar */
        .stSidebar *, .stSidebar * * {
            color: #1e293b !important;
        }
        
        /* Fix dropdown options specifically */
        .stSelectbox [role="listbox"], .stSelectbox [role="option"] {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* Fix mobile menu toggle button */
        .stSidebar .css-1d391kg button, .stSidebar button {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* Fix mobile menu when expanded */
        .stSidebar .css-1d391kg .css-1d391kg, .stSidebar .css-1d391kg .css-1d391kg * {
            color: #1e293b !important;
        }
        
        /* Fix any remaining Streamlit UI elements in sidebar */
        .stSidebar .stButton, .stSidebar .stButton * {
            color: #1e293b !important;
        }
        
        /* Fix mobile menu text in all states */
        .stSidebar p, .stSidebar div, .stSidebar span, .stSidebar label {
            color: #1e293b !important;
        }
        
        /* Fix button text and backgrounds */
        button, .stButton button {
            color: #ffffff !important;
            background-color: #6b7280 !important;
        }
        
        /* Fix selectbox and radio button text */
        .stSelectbox label, .stRadio label {
            color: #1e293b !important;
        }
        
        /* Fix form elements */
        .stSelectbox > div > div, .stRadio > div > div {
            color: #1e293b !important;
        }
        
        /* Fix main content area selectboxes (like Filter by kid) */
        .main .stSelectbox, .main .stSelectbox * {
            color: #1e293b !important;
        }
        
        .main .stSelectbox label {
            color: #1e293b !important;
        }
        
        .main .stSelectbox > div > div {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* Fix main content area radio buttons */
        .main .stRadio, .main .stRadio * {
            color: #1e293b !important;
        }
        
        .main .stRadio label {
            color: #1e293b !important;
        }
        
        /* Specific overrides for monitor elements */
        .monitor-day * {
            color: #1e293b !important;
        }
        
        .monitor-day-header * {
            color: #0066cc !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'activities_df' not in st.session_state:
    st.session_state.activities_df = pd.DataFrame(columns=[
        'kid_name', 'activity', 'time', 'duration', 'frequency', 
        'days_of_week', 'start_date', 'end_date', 'address', 'pickup_driver', 'return_driver'
    ])

if 'show_nav_menu' not in st.session_state:
    st.session_state.show_nav_menu = False

# Remove the CSV file path since we're using Google Sheets as primary source
# if 'csv_file' not in st.session_state:
#     st.session_state.csv_file = 'activities.csv'

# Helper functions (same as before)
def migrate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Migrate old dataframe to new schema with start_date and end_date"""
    if df.empty:
        return df
    
    if 'start_date' not in df.columns:
        df['start_date'] = date.today()
    if 'end_date' not in df.columns:
        df['end_date'] = date.today() + timedelta(days=365)
    
    if 'start_date' in df.columns:
        if df['start_date'].dtype == 'object':
            df['start_date'] = pd.to_datetime(df['start_date']).dt.date
    if 'end_date' in df.columns:
        if df['end_date'].dtype == 'object':
            df['end_date'] = pd.to_datetime(df['end_date']).dt.date
    
    return df

def load_data_from_csv(filename: str) -> pd.DataFrame:
    """Load activities data from CSV file"""
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            if 'days_of_week' in df.columns:
                df['days_of_week'] = df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            df = migrate_dataframe(df)
            return df
        except Exception as e:
            st.error(f"Error loading CSV file: {e}")
            return pd.DataFrame(columns=[
                'kid_name', 'activity', 'time', 'duration', 'frequency', 
                'days_of_week', 'start_date', 'end_date', 'address', 'pickup_driver', 'return_driver'
            ])
    return pd.DataFrame(columns=[
        'kid_name', 'activity', 'time', 'duration', 'frequency', 
        'days_of_week', 'start_date', 'end_date', 'address', 'pickup_driver', 'return_driver'
    ])

def load_combined_data_for_display() -> pd.DataFrame:
    """Load and combine Google Drive activities with school_events.csv and jewish_holidays.csv for display purposes"""
    # Load main activities from Google Drive
    try:
        activities_df = load_activities_from_google_drive()
    except Exception as e:
        st.error(f"Failed to load activities from Google Drive: {e}")
        return pd.DataFrame()
    
    # Load school events if available
    school_events_df = pd.DataFrame()
    if os.path.exists('school_events.csv'):
        try:
            school_events_df = pd.read_csv('school_events.csv')
            if 'days_of_week' in school_events_df.columns:
                school_events_df['days_of_week'] = school_events_df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            # Convert date columns to datetime objects
            if 'start_date' in school_events_df.columns:
                school_events_df['start_date'] = pd.to_datetime(school_events_df['start_date']).dt.date
            if 'end_date' in school_events_df.columns:
                school_events_df['end_date'] = pd.to_datetime(school_events_df['end_date']).dt.date
            print(f"Loaded {len(school_events_df)} school events")
        except Exception as e:
            print(f"Warning: Could not load school events: {e}")
    
    # Load Jewish holidays if available
    jewish_holidays_df = pd.DataFrame()
    if os.path.exists('jewish_holidays.csv'):
        try:
            jewish_holidays_df = pd.read_csv('jewish_holidays.csv')
            if 'days_of_week' in jewish_holidays_df.columns:
                jewish_holidays_df['days_of_week'] = jewish_holidays_df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            # Convert date columns to datetime objects
            if 'start_date' in jewish_holidays_df.columns:
                jewish_holidays_df['start_date'] = pd.to_datetime(jewish_holidays_df['start_date']).dt.date
            if 'end_date' in jewish_holidays_df.columns:
                jewish_holidays_df['end_date'] = pd.to_datetime(jewish_holidays_df['end_date']).dt.date
            print(f"Loaded {len(jewish_holidays_df)} Jewish holidays")
        except Exception as e:
            print(f"Warning: Could not load Jewish holidays: {e}")
    
    # Combine all dataframes
    combined_df = pd.concat([activities_df, school_events_df, jewish_holidays_df], ignore_index=True)
    print(f"Combined {len(activities_df)} activities + {len(school_events_df)} school events + {len(jewish_holidays_df)} Jewish holidays = {len(combined_df)} total")
    
    return combined_df

def save_data_to_csv(df: pd.DataFrame, filename: str):
    """Save activities data to CSV file"""
    try:
        df_copy = df.copy()
        if 'days_of_week' in df_copy.columns:
            df_copy['days_of_week'] = df_copy['days_of_week'].apply(json.dumps)
        df_copy.to_csv(filename, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving CSV file: {e}")
        return False

def auto_save_activities():
    """Automatically save activities to CSV"""
    if save_data_to_csv(st.session_state.activities_df, st.session_state.csv_file):
        st.success("✅ Saved!")

def get_week_dates(selected_date: date) -> Tuple[date, date]:
    """Get start and end of week for a given date"""
    days_since_monday = selected_date.weekday()
    monday = selected_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    return monday, sunday

def get_current_week_dates() -> Tuple[date, date]:
    """Get current week's Monday and Sunday"""
    today = date.today()
    return get_week_dates(today)

def is_activity_active_in_week(activity_start: date, activity_end: date, week_start: date, week_end: date) -> bool:
    """Check if activity is active during the specified week"""
    # Activity is active if it actually occurs during the week
    # It should start before or during the week AND end after or during the week
    return (activity_start <= week_end) and (activity_end >= week_start)

def calculate_hours_by_day(df: pd.DataFrame, kid_name: str, week_start: date = None, week_end: date = None) -> Dict[str, float]:
    """Calculate daily hours for a specific kid within a date range"""
    kid_activities = df[df['kid_name'] == kid_name]
    kid_activities = kid_activities[kid_activities['activity'].str.lower() != 'school']
    
    daily_hours = {day: 0.0 for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']}
    
    for _, activity in kid_activities.iterrows():
        if week_start and week_end:
            if not is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end):
                continue
        
        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
        duration = float(activity['duration'])
        
        for day in days:
            daily_hours[day.lower()] += duration
    
    return daily_hours

def calculate_weekly_hours(df: pd.DataFrame, kid_name: str, week_start: date = None, week_end: date = None) -> float:
    """Calculate total weekly hours for a specific kid within a date range"""
    daily_hours = calculate_hours_by_day(df, kid_name, week_start, week_end)
    return sum(daily_hours.values())

def calculate_drives_per_driver(df: pd.DataFrame, week_start: date, week_end: date) -> Dict[str, int]:
    """Calculate number of drives per driver for the week"""
    drives_count = {}
    filtered_df = df[df['activity'].str.lower() != 'school']
    
    for _, activity in filtered_df.iterrows():
        if not is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end):
            continue
            
        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
        num_days = len(days)
        
        pickup_driver = activity['pickup_driver']
        if pickup_driver not in drives_count:
            drives_count[pickup_driver] = 0
        drives_count[pickup_driver] += num_days
        
        return_driver = activity['return_driver']
        if return_driver not in drives_count:
            drives_count[return_driver] = 0
        drives_count[return_driver] += num_days
    
    return drives_count

def create_weekly_schedule(df: pd.DataFrame, week_start: date, week_end: date) -> pd.DataFrame:
    """Create a weekly schedule table organized by day and driver for a specific week"""
    try:
        if df.empty:
            return pd.DataFrame()
        
        weekly_data = []
        
        for idx, activity in df.iterrows():
            try:
                # Debug: Check date ranges
                print(f"DEBUG: Activity {activity.get('activity', 'Unknown')} - Start: {activity['start_date']}, End: {activity['end_date']}, Week: {week_start} to {week_end}")
                is_active = is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end)
                print(f"DEBUG: Is active in week: {is_active}")
                
                if not is_active:
                    continue
                
                # Handle different frequency types
                if activity.get('frequency') == 'one-time':
                    # For one-time events, days_of_week contains the actual day
                    days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
                else:
                    # For recurring events, days_of_week contains recurring days
                    days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
                
                # Safety check: ensure days is a list
                if not isinstance(days, list):
                    print(f"WARNING: days_of_week is not a list for activity {activity.get('activity', 'Unknown')}: {days} (type: {type(days)})")
                    days = []
                
                # Filter out any non-string days
                days = [day for day in days if isinstance(day, str)]
                
                print(f"DEBUG: Days for this activity: {days} (type: {type(days)})")
                
                for day in days:
                    try:
                        # Calculate the actual date for this day in the week
                        day_index = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(day.lower())
                        day_date = week_start + timedelta(days=day_index)
                        
                        # Only show activity if it's active on this specific day
                        if activity['start_date'] <= day_date <= activity['end_date']:
                            # Clean and format the start time consistently
                            start_time_str = str(activity['time']).strip()
                            # Remove any extra colons and ensure proper format
                            if start_time_str.count(':') > 1:
                                start_time_str = start_time_str.split(':')[0] + ':' + start_time_str.split(':')[1]
                            
                            try:
                                start_time = pd.to_datetime(start_time_str).time()
                                duration_hours = float(activity['duration'])
                                duration_minutes = int(duration_hours * 60)
                                
                                start_datetime = datetime.combine(date.today(), start_time)
                                end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                                end_time = end_datetime.time().strftime('%H:%M')
                                
                                # Format start time consistently with leading zeros
                                formatted_start_time = start_time.strftime('%H:%M')
                                
                                # Abbreviate kid name using first letter
                                kid_name = activity['kid_name'][0].upper()
                                
                                # Abbreviate day name (M, T, W, Th, F, S, Su)
                                if day.lower() == 'thursday':
                                    day_abbrev = 'Th'
                                else:
                                    day_abbrev = day[0].upper()
                                
                                weekly_data.append({
                                    'Day': day_abbrev,
                                    'Kid': kid_name,
                                    'Activity': activity['activity'],
                                    'Time': f"{formatted_start_time}-{end_time}",
                                    'Address': activity['address'],
                                    'Pickup': activity['pickup_driver'],
                                    'Return': activity['return_driver'],
                                    'Start Date': activity['start_date'],
                                    'End Date': activity['end_date']
                                })
                            except Exception as time_error:
                                print(f"WARNING: Could not process time '{start_time_str}' for activity {activity.get('activity', 'Unknown')}: {time_error}")
                                continue
                    except Exception as day_error:
                        print(f"ERROR processing day {day} for activity {activity.get('activity', 'Unknown')}: {day_error}")
                        continue
                        
            except Exception as activity_error:
                print(f"ERROR processing activity {activity.get('activity', 'Unknown')}: {activity_error}")
                continue
        
        print(f"DEBUG: Created {len(weekly_data)} weekly data entries")
        
        weekly_df = pd.DataFrame(weekly_data)
        print(f"DEBUG: DataFrame created with {len(weekly_df)} rows, type: {type(weekly_df)}")
        
        if not weekly_df.empty:
            # Sort by day first, then by start time (convert to time objects for proper sorting)
            try:
                # Extract start time and convert to time objects for proper sorting
                weekly_df['Start_Time'] = weekly_df['Time'].str.split('-').str[0].apply(
                    lambda x: pd.to_datetime(x, format='%H:%M').time()
                )
                weekly_df = weekly_df.sort_values(['Day', 'Start_Time'])
                weekly_df = weekly_df.drop('Start_Time', axis=1)
            except Exception as sort_error:
                print(f"WARNING: Could not sort by time, using default order: {sort_error}")
                # Fallback: sort by day only
                weekly_df = weekly_df.sort_values(['Day'])
        
        # Ensure we always return a DataFrame
        if not isinstance(weekly_df, pd.DataFrame):
            print(f"WARNING: weekly_df is not a DataFrame, it's {type(weekly_df)}")
            return pd.DataFrame()
        
        print(f"DEBUG: Returning DataFrame with {len(weekly_df)} rows")
        return weekly_df
        
    except Exception as e:
        print(f"CRITICAL ERROR in create_weekly_schedule: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
    
    # Final safety check - this should never be reached, but just in case
    print("WARNING: Unexpected code path reached, returning empty DataFrame")
    return pd.DataFrame()

def display_weekly_schedule(weekly_schedule, week_start, week_end, today):
    """Helper function to display weekly schedule by day"""
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_abbrev = ['M', 'T', 'W', 'Th', 'F', 'S', 'Su']
    
    for i, day in enumerate(days_order):
        # Filter activities for this specific day
        day_activities = weekly_schedule[weekly_schedule['Day'] == days_abbrev[i]]
        if not day_activities.empty:
            day_date = week_start + timedelta(days=i)
            
            # Hide past days (show only current day and future days)
            if day_date < today:
                continue
                
            # Mobile-optimized day display
            st.markdown(f'<div class="day-header">{day}</div>', unsafe_allow_html=True)
            
            # Create DataFrame for this day's activities
            day_df = pd.DataFrame(day_activities)
            
            # Check if Address column exists before processing
            if 'Address' in day_df.columns:
                day_df['Address'] = day_df['Address'].apply(make_address_clickable)
            
            # Display the day's activities as HTML table instead of dataframe
            html_table = day_df.to_html(escape=False, index=False)
            st.markdown(html_table, unsafe_allow_html=True)
            st.markdown("---")

def display_monitor_dashboard(current_time=None):
    """Display wall dashboard for monitor mode showing today and next 30 days' activities"""
    # Load data
    try:
        display_df = load_combined_data_for_display()
    except Exception as e:
        st.error(f"Failed to load activities: {e}")
        return
    
    if display_df.empty:
        st.info("No activities available for monitor display")
        return
    
    # Get today and next 30 days (use current_time if provided, otherwise use today)
    if current_time:
        today = current_time.date()
    else:
        today = date.today()
    end_date = today + timedelta(days=29)  # 30 days inclusive
    
    # Create monitor-specific CSS for large display
    st.markdown("""
    <style>
    .monitor-container {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
    }
    .monitor-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #0066cc !important;
        background-color: #ffffff !important;
    }
    .monitor-day {
        background-color: #f8f9fa !important;
        color: #000000 !important;
        padding: 0.15rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        border-left: 2px solid #0066cc;
        min-height: 30px;
        border: 1px solid #dee2e6;
    }
    .monitor-day-today {
        background-color: #fff3cd !important;
        color: #000000 !important;
        padding: 0.15rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        border-left: 3px solid #ffc107;
        min-height: 30px;
        box-shadow: 0 0 5px rgba(255, 193, 7, 0.3);
        border: 2px solid #ffc107;
    }
    .monitor-week-header {
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0 0.5rem 0;
        color: #0066cc !important;
        background-color: #e9ecef !important;
        padding: 0.25rem;
        border-radius: 0.25rem;
        border: 1px solid #dee2e6;
    }
    .monitor-day-header {
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.05rem;
        color: #0066cc !important;
        background-color: transparent !important;
        text-align: center;
        padding: 0.05rem;
        line-height: 1.0;
    }
    .monitor-activity {
        background-color: transparent !important;
        color: #000000 !important;
        padding: 0.1rem 0;
        margin: 0.05rem 0;
        border: none;
        font-size: 0.6rem;
        line-height: 1.1;
    }
    .monitor-activity-time {
        font-size: 0.6rem;
        font-weight: bold;
        color: #0066cc !important;
        background-color: transparent !important;
        display: inline;
    }
    .monitor-activity-details {
        font-size: 0.6rem;
        margin-left: 0.3rem;
        color: #000000 !important;
        background-color: transparent !important;
        display: inline;
    }
    .monitor-no-activities {
        font-size: 0.6rem;
        text-align: center;
        color: #6c757d !important;
        background-color: transparent !important;
        padding: 0.2rem;
    }
    .monitor-refresh {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display 30-day calendar view with refresh button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f'<div class="monitor-header">📅 Family Planner - {today.strftime("%B %d")} to {end_date.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
    with col3:
        if st.button("🔄 Refresh", key="monitor_refresh", type="primary"):
            st.rerun()
    
    # Create a grid layout for the 30 days
    # Group days into weeks for better organization
    current_date = today
    
    while current_date <= end_date:
        # Start a new week
        week_start = current_date
        week_end = min(current_date + timedelta(days=6), end_date)
        
        # Create columns for this week (up to 7 days)
        week_days = []
        temp_date = week_start
        while temp_date <= week_end and temp_date <= end_date:
            week_days.append(temp_date)
            temp_date += timedelta(days=1)
        
        # Create columns dynamically based on number of days in this week
        cols = st.columns(len(week_days))
        
        for i, day_date in enumerate(week_days):
            with cols[i]:
                # Highlight today
                if day_date == today:
                    day_class = "monitor-day-today"
                    day_icon = "⭐"
                    bg_color = "#fff3cd"
                else:
                    day_class = "monitor-day"
                    day_icon = "📅"
                    bg_color = "#f8f9fa"
                
                st.markdown(f'<div class="{day_class}" style="background-color: {bg_color} !important; color: #000000 !important;"><div class="monitor-day-header" style="color: #0066cc !important; background-color: transparent !important;">{day_icon} {day_date.strftime("%a %b %d")}</div>', unsafe_allow_html=True)
                display_day_activities(display_df, day_date)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Move to next week
        current_date = week_end + timedelta(days=1)
    
    # Auto-refresh every 5 minutes
    st.markdown("""
    <script>
    setTimeout(function(){
        window.location.reload();
    }, 300000); // 5 minutes
    </script>
    """, unsafe_allow_html=True)

def display_day_activities(display_df, target_date):
    """Display activities for a specific day in monitor format"""
    # Get activities for the target date
    day_activities = []
    
    for _, activity in display_df.iterrows():
        # Check if activity is active on this date
        if activity['start_date'] <= target_date <= activity['end_date']:
            # Check if this activity occurs on this day of the week
            days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
            day_name = target_date.strftime('%A').lower()
            
            if day_name in [d.lower() for d in days]:
                try:
                    # Format time
                    start_time_str = str(activity['time']).strip()
                    if start_time_str.count(':') > 1:
                        start_time_str = start_time_str.split(':')[0] + ':' + start_time_str.split(':')[1]
                    
                    start_time = pd.to_datetime(start_time_str, format='%H:%M').time()
                    duration_hours = float(activity['duration'])
                    duration_minutes = int(duration_hours * 60)
                    
                    start_datetime = datetime.combine(target_date, start_time)
                    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                    end_time = end_datetime.time().strftime('%H:%M')
                    
                    formatted_start_time = start_time.strftime('%H:%M')
                    
                    day_activities.append({
                        'time': f"{formatted_start_time}-{end_time}",
                        'activity': activity['activity'],
                        'kid': activity['kid_name'],
                        'address': activity['address'],
                        'pickup': activity['pickup_driver'],
                        'return': activity['return_driver']
                    })
                except Exception as e:
                    print(f"Error processing activity {activity.get('activity', 'Unknown')}: {e}")
                    continue
    
    # Sort by time
    day_activities.sort(key=lambda x: x['time'])
    
    if not day_activities:
        st.markdown('<div class="monitor-no-activities" style="color: #6c757d !important; background-color: transparent !important;">No activities scheduled</div>', unsafe_allow_html=True)
    else:
        for activity in day_activities:
                        # Truncate activity name if too long
                        activity_name = activity["activity"]
                        if len(activity_name) > 20:
                            activity_name = activity_name[:17] + "..."
                        
                        st.markdown(f'''
                        <div class="monitor-activity" style="color: #000000 !important; background-color: transparent !important;">
                            <span class="monitor-activity-time" style="color: #0066cc !important; background-color: transparent !important;">{activity["time"]}</span>
                            <span class="monitor-activity-details" style="color: #000000 !important; background-color: transparent !important;">
                                <strong>{activity_name}</strong> ({activity["kid"]})
                            </span>
                        </div>
                        ''', unsafe_allow_html=True)

# Main application
def main():
    # Define day order and abbreviations for schedule display
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_abbrev = ['M', 'T', 'W', 'Th', 'F', 'S', 'Su']
    
    # Check for monitor mode URL parameter
    query_params = st.query_params
    is_monitor_mode = query_params.get("mode") == "monitor"
    
    # Time and date override for testing
    time_override = query_params.get("time")
    date_override = query_params.get("date")
    
    # Start with current datetime
    current_time = datetime.now()
    
    # Define home address
    home_address = "628 Wellsbury Way, Palo Alto, CA 94306"
    
    # Apply date override if provided
    if date_override:
        try:
            # Parse date in format "YYYY-MM-DD"
            year, month, day = map(int, date_override.split('-'))
            current_time = current_time.replace(year=year, month=month, day=day)
            st.info(f"📅 **Date Override Active:** {current_time.strftime('%A, %B %d, %Y')} (for testing)")
        except ValueError:
            st.warning(f"⚠️ Invalid date format: {date_override}. Use YYYY-MM-DD format (e.g., ?date=2024-01-15)")
    
    # Apply time override if provided
    if time_override:
        try:
            # Parse time in format "HH:MM" or "HH:MM:SS"
            if len(time_override.split(':')) == 2:
                time_override += ":00"  # Add seconds if not provided
            hour, minute, second = map(int, time_override.split(':'))
            current_time = current_time.replace(hour=hour, minute=minute, second=second, microsecond=0)
            if date_override:
                st.info(f"🕐 **Time Override Active:** {current_time.strftime('%I:%M %p')} on {current_time.strftime('%A, %B %d, %Y')} (for testing)")
            else:
                st.info(f"🕐 **Time Override Active:** {current_time.strftime('%I:%M %p')} (for testing)")
        except ValueError:
            st.warning(f"⚠️ Invalid time format: {time_override}. Use HH:MM format (e.g., ?time=14:30)")
            current_time = datetime.now()
    
    if is_monitor_mode:
        # Monitor mode - wall dashboard
        display_monitor_dashboard(current_time)
        return
    
    
    # Load data - try Google Drive first, fallback to local file
    try:
        st.session_state.activities_df = load_activities_from_google_drive()
        display_df = load_combined_data_for_display()  # Combined data for display
        
    except Exception as e:
        st.error(f"🚨 **Google Drive Error:** {str(e)}")
        st.info("""
        **Troubleshooting Steps:**
        1. Check your internet connection
        2. Verify the Google Sheet is accessible: [Open Google Sheet](https://docs.google.com/spreadsheets/d/1TS4zfU5BT1e80R5VMoZFkbLlH-yj2ZWGWHMd0qMO4wA/edit)
        3. Make sure the sheet has data in the correct format
        4. Try refreshing the page
        """)
        st.stop()  # Stop execution if Google Drive fails
    
    # Mobile-optimized navigation
    st.sidebar.title("Menu")
    
    # Time and date override help
    if time_override or date_override:
        if time_override and date_override:
            st.sidebar.info(f"🕐 **Testing Mode**\nTime: {current_time.strftime('%I:%M %p')}\nDate: {current_time.strftime('%A, %B %d, %Y')}\n\nRemove `?time=` and `?date=` from URL to use real time")
        elif time_override:
            st.sidebar.info(f"🕐 **Testing Mode**\nTime: {current_time.strftime('%I:%M %p')}\n\nRemove `?time=` from URL to use real time")
        elif date_override:
            st.sidebar.info(f"📅 **Testing Mode**\nDate: {current_time.strftime('%A, %B %d, %Y')}\n\nRemove `?date=` from URL to use real date")
    else:
        st.sidebar.caption("💡 **Testing Tips:**\n• Add `?time=14:30` to test different times\n• Add `?date=2025-09-15` to test different dates\n• Combine both: `?time=14:30&date=2025-09-15`")
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "📋 Schedule"
    
    # Use radio buttons for cleaner mobile experience
    radio_options = ["📋 Schedule", "👶 Kids", "🚗 Drivers", "⚙️ Data"]
    current_page = st.session_state.page
    
    # If current page is not in radio options (like Monthly), don't change it
    # Just use the first option for the radio display
    radio_index = 0
    if current_page in radio_options:
        radio_index = radio_options.index(current_page)
    
    page = st.sidebar.radio(
        "Choose:",
        radio_options,
        label_visibility="collapsed",  # Hide the label to save space
        index=radio_index
    )
    
    # Add quick navigation buttons for calendar views
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📅 Monthly", help="View 30-day calendar", key="nav_monthly"):
            st.session_state.page = "📅 Monthly"
            st.rerun()
    with col2:
        if st.button("📋 Weekly", help="View weekly schedule", key="nav_weekly"):
            st.session_state.page = "📋 Schedule"
            st.rerun()
    
    
    # Update session state when radio button changes (only if current page is in radio options)
    if page != current_page and current_page in radio_options:
        st.session_state.page = page
        current_page = page
    
    # Use session state page
    current_page = st.session_state.page
    
    # Weekly View Section (landing page)
    if current_page == "📋 Schedule":
        if display_df.empty:
            st.info("No activities available. Add some activities first!")
        else:
            # Display the table first (with smart week selection)
            # Use overridden date if available, otherwise use current date
            if date_override or time_override:
                # Use the overridden date/time
                today = current_time.date()
                week_start, week_end = get_week_dates(today)
                week_description = f"week of {today.strftime('%B %d, %Y')}"
            else:
                # Use current date
                # Use server time converted to Pacific timezone
                server_now = datetime.now()
                pacific_time = server_now - timedelta(hours=7)  # UTC-7 for Pacific Daylight Time
                today = pacific_time.date()  # Use Pacific date for filtering
                
                # Always show current week by default
                week_start, week_end = get_current_week_dates()
                week_description = f"current week"
            
            # Check if there are activities in the remaining days of current week
            remaining_days_activities = 0
            for i in range(today.weekday(), 7):  # From today to end of week
                day_date = week_start + timedelta(days=i)
                day_activities = display_df[
                    (display_df['start_date'] <= day_date) & 
                    (display_df['end_date'] >= day_date)
                ]
                remaining_days_activities += len(day_activities)
            
            # Only show next week if no activities remain in current week
            if remaining_days_activities == 0 and today.weekday() >= 5:  # Weekend with no remaining activities
                next_week_start = week_end + timedelta(days=1)  # Monday of next week
                week_start, week_end = get_week_dates(next_week_start)
                week_description = f"next week"
                st.info(f"📅 **Note:** Showing next week because no activities remain in current week (remaining days: {remaining_days_activities} activities)")
            
            # Also get the following week for extended view
            following_week_start = week_end + timedelta(days=1)  # Monday of following week
            following_week_end = following_week_start + timedelta(days=6)  # Sunday of following week
            
            weekly_schedule = create_weekly_schedule(display_df, week_start, week_end)
            following_week_schedule = create_weekly_schedule(display_df, following_week_start, following_week_end)
            
            # Safety check: ensure weekly_schedule is a DataFrame
            if not isinstance(weekly_schedule, pd.DataFrame):
                st.error(f"Error: Expected DataFrame but got {type(weekly_schedule)}")
                weekly_schedule = pd.DataFrame()
            
            # Safety check: ensure following_week_schedule is a DataFrame
            if not isinstance(following_week_schedule, pd.DataFrame):
                st.error(f"Error: Expected DataFrame but got {type(following_week_schedule)}")
                following_week_schedule = pd.DataFrame()
            
            # SMART NAVIGATION BUTTON - FIRST AND TOP
            if not weekly_schedule.empty:
                # Smart navigation button at the very top
                # current_time is already set from the time override logic above
                nav_type, nav_address, nav_reason, nav_options = analyze_navigation_context(weekly_schedule, current_time)
                
                # Define home address for navigation
                home_address = "628 Wellsbury Way, Palo Alto, CA 94306"
                
                # Create a single-line header with navigation, status, and title
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if nav_type == "multiple":
                        # Show destination and go button for multiple options
                        non_home_options = [opt for opt in nav_options if opt['type'] != 'home']
                        if non_home_options:
                            if len(non_home_options) == 1:
                                # Single destination - show it directly
                                default_dest = non_home_options[0]
                                st.write(f"**Destination:** {default_dest['description']}")
                            else:
                                # Multiple destinations - show dropdown
                                selected_option = st.selectbox(
                                    f"Choose destination: ({len(non_home_options)} options)",
                                    options=range(len(non_home_options)),
                                    format_func=lambda x: non_home_options[x]['description'],
                                    key="nav_select"
                                )
                                default_dest = non_home_options[selected_option]
                        else:
                            st.write(f"**{nav_reason}**")
                            st.write("**Destination:** Home")
                    else:
                        # Single destination - show destination and go button
                        if nav_reason == "No activities today":
                            st.write(f"**{nav_reason}**")
                            st.write("**Destination:** Home")
                        else:
                            # Get the activity details for display
                            activity_details = ""
                            if nav_options and len(nav_options) > 0:
                                # Find the matching activity in nav_options
                                for option in nav_options:
                                    if option['address'] == nav_address:
                                        activity_details = option['description']
                                        break
                            
                            if activity_details:
                                st.write(f"**Destination:** {activity_details}")
                            else:
                                st.write(f"**Destination:** {nav_address}")
                
                with col2:
                    # Show Go button
                    if nav_type == "multiple":
                        non_home_options = [opt for opt in nav_options if opt['type'] != 'home']
                        if non_home_options:
                            if len(non_home_options) == 1:
                                selected_address = non_home_options[0]['address']
                            else:
                                # Use the selected option from dropdown
                                if 'nav_select' in st.session_state:
                                    selected_index = st.session_state.nav_select
                                    if 0 <= selected_index < len(non_home_options):
                                        selected_address = non_home_options[selected_index]['address']
                                    else:
                                        selected_address = non_home_options[0]['address']
                                else:
                                    selected_address = non_home_options[0]['address']
                        else:
                            selected_address = home_address
                    else:
                        selected_address = nav_address
                    
                    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={selected_address.replace(' ', '+')}&travelmode=driving&dir_action=navigate"
                    st.link_button("🧭 Go", maps_url, type="primary")
                
                with col3:
                    # Always show Home button
                    home_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={home_address.replace(' ', '+')}&travelmode=driving&dir_action=navigate"
                    st.link_button("🏠 Home", home_maps_url)
                
                st.markdown("---")
            
            # Display the table
            if not weekly_schedule.empty:
                # Show what date range the schedule is for
                # Use overridden time if available, otherwise use Pacific time
                if time_override or date_override:
                    display_time = current_time.strftime('%I:%M %p')
                else:
                    display_time = pacific_time.strftime('%I:%M %p')
                st.info(f"📅 **{week_description}:** {week_start.strftime('%m %d')} - {week_end.strftime('%m %d, %Y')} (Current: {today.strftime('%B %d')} at {display_time})")
                
                # Add refresh button for Google Drive updates
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("💡 **Tip:** Edit activities in [Google Sheets](https://docs.google.com/spreadsheets/d/1TS4zfU5BT1e80R5VMoZFkbLlH-yj2ZWGWHMd0qMO4wA/edit) for real-time updates")
                with col2:
                    if st.button("🔄 Refresh Data", help="Click to reload latest data from Google Drive"):
                        st.rerun()
                
                # Display current week schedule
                display_weekly_schedule(weekly_schedule, week_start, week_end, today)
                
                # Display following week schedule
                if not following_week_schedule.empty:
                    st.subheader(f"📋 Following Week Schedule ({following_week_start.strftime('%B %d')} - {following_week_end.strftime('%B %d, %Y')})")
                    display_weekly_schedule(following_week_schedule, following_week_start, following_week_end, today)
                else:
                    st.caption("🔮 **Following week:** No activities scheduled")
            
            # Controls after the table
            st.markdown("---")
            st.subheader("Controls")
            
            # Week selection with override option
            col1, col2 = st.columns(2)
            with col1:
                # Add a toggle to override automatic week selection
                override_week = st.checkbox(
                    "Override week selection",
                    help="Check to manually select a different week"
                )
                
                if override_week:
                    selected_week_date = st.date_input(
                        "Select week:",
                        value=date.today(),
                        help="Select week"
                    )
                else:
                    # Use the automatically determined week
                    selected_week_date = week_start
            
            with col2:
                kids = st.session_state.activities_df['kid_name'].unique()
                kid_options = ["All Kids"] + list(kids)
                # Use index parameter to ensure we get the string value
                selected_kid_filter = st.selectbox(
                    "Filter by kid:",
                    kid_options,
                    index=0,  # Default to "All Kids"
                    help="Filter by kid"
                )
                
                # Debug: Check what we got
                print(f"DEBUG: selected_kid_filter type: {type(selected_kid_filter)}, value: {selected_kid_filter}")
                
                # Final safety check - ensure it's a string
                if not isinstance(selected_kid_filter, str):
                    selected_kid_filter = "All Kids"
            
            # Show the selected week info
            week_start, week_end = get_week_dates(selected_week_date)
            st.caption(f"📅 {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")
            
            # Recalculate and display filtered schedule
            if selected_kid_filter != "All Kids" or override_week or selected_week_date != week_start:
                st.subheader("Filtered Schedule")
                
                # Recalculate schedule with new filters
                new_weekly_schedule = create_weekly_schedule(display_df, week_start, week_end)
                
                # Safety check: ensure new_weekly_schedule is a DataFrame
                if not isinstance(new_weekly_schedule, pd.DataFrame):
                    st.error(f"Error: Expected DataFrame but got {type(new_weekly_schedule)}")
                    new_weekly_schedule = pd.DataFrame()
                
                if selected_kid_filter != "All Kids":
                    # Get the abbreviated kid name (first letter)
                    kid_abbrev = selected_kid_filter[0].upper()
                    new_weekly_schedule = new_weekly_schedule[new_weekly_schedule['Kid'] == kid_abbrev]
                    st.info(f"👶 Showing schedule for: {selected_kid_filter}")
                
                if not new_weekly_schedule.empty:
                    # Display filtered schedule
                    new_weekly_schedule['Address'] = new_weekly_schedule['Address'].apply(make_address_clickable)
                    
                    for i, day in enumerate(days_order):
                        day_activities = new_weekly_schedule[new_weekly_schedule['Day'] == days_abbrev[i]]
                        if not day_activities.empty:
                            st.markdown(f'<div class="day-header">{day}</div>', unsafe_allow_html=True)
                            st.markdown(day_activities.to_html(escape=False, index=False), unsafe_allow_html=True)
                else:
                    st.info("No activities found with the selected filters.")
                
                # Summary statistics
                with st.expander(" Summary", expanded=False):
                    # Use the correct data source for calculations
                    if selected_kid_filter != "All Kids":
                        # If filtering by specific kid, calculate hours for that kid only
                        kids_in_schedule = [selected_kid_filter]
                        kids_hours = {selected_kid_filter: calculate_weekly_hours(st.session_state.activities_df, selected_kid_filter, week_start, week_end)}
                    else:
                        # If showing all kids, get unique kids from the weekly schedule
                        kids_in_schedule = weekly_schedule['Kid'].unique() if isinstance(weekly_schedule, pd.DataFrame) and not weekly_schedule.empty else []
                        kids_hours = {}
                        for kid in kids_in_schedule:
                            # Convert abbreviated kid name back to full name for calculation
                            full_kid_name = None
                            for _, activity in st.session_state.activities_df.iterrows():
                                if activity['kid_name'][0].upper() == kid:
                                    full_kid_name = activity['kid_name']
                                    break
                            
                            if full_kid_name:
                                kids_hours[kid] = calculate_weekly_hours(display_df, full_kid_name, week_start, week_end)
                            else:
                                kids_hours[kid] = 0.0
                    
                    drives_per_driver = calculate_drives_per_driver(display_df, week_start, week_end)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Activities", len(weekly_schedule) if isinstance(weekly_schedule, pd.DataFrame) else 0)
                        st.metric("Kids", len(kids_in_schedule))
                    with col2:
                        total_hours = sum(kids_hours.values())
                        st.metric("Hours", f"{total_hours:.1f}h")
                        # Safety check for pickup/return columns
                        if isinstance(weekly_schedule, pd.DataFrame) and not weekly_schedule.empty and 'Pickup' in weekly_schedule.columns and 'Return' in weekly_schedule.columns:
                            pickup_drivers = weekly_schedule['Pickup'].tolist()
                            return_drivers = weekly_schedule['Return'].tolist()
                            unique_drivers = len(set(pickup_drivers + return_drivers))
                        else:
                            unique_drivers = 0
                        st.metric("Drivers", unique_drivers)
                    
                    # Compact tables
                    if kids_hours:
                        st.write("**Hours per Kid:**")
                        kids_df = pd.DataFrame(list(kids_hours.items()), columns=['Kid', 'Hours'])
                        kids_df = kids_df.sort_values('Hours', ascending=False)
                        st.dataframe(kids_df, use_container_width=True, hide_index=True)
                    
                    if drives_per_driver:
                        st.write("**Drives per Driver:**")
                        drives_df = pd.DataFrame(list(drives_per_driver.items()), columns=['Driver', 'Drives'])
                        drives_df = drives_df.sort_values('Drives', ascending=False)
                        st.dataframe(drives_df, use_container_width=True, hide_index=True)
                
            else:
                st.info("No activities this week")
    
    # Monthly View Section
    elif current_page == "📅 Monthly":
        if display_df.empty:
            st.info("No activities available. Add some activities first!")
        else:
            # Display 30-day calendar view
            today = date.today()
            end_date = today + timedelta(days=29)  # 30 days inclusive
            
            st.markdown(f'<div class="monitor-header">📅 Family Planner - {today.strftime("%B %d")} to {end_date.strftime("%B %d, %Y")}</div>', unsafe_allow_html=True)
            
            # Create a grid layout for the 30 days
            # Group days into weeks for better organization
            current_date = today
            
            while current_date <= end_date:
                # Start a new week
                week_start = current_date
                week_end = min(current_date + timedelta(days=6), end_date)
                
                # Create columns for this week (up to 7 days)
                week_days = []
                temp_date = week_start
                while temp_date <= week_end and temp_date <= end_date:
                    week_days.append(temp_date)
                    temp_date += timedelta(days=1)
                
                # Create columns dynamically based on number of days in this week
                cols = st.columns(len(week_days))
                
                for i, day_date in enumerate(week_days):
                    with cols[i]:
                        # Highlight today
                        if day_date == today:
                            day_class = "monitor-day-today"
                            day_icon = "⭐"
                            bg_color = "#fff3cd"
                        else:
                            day_class = "monitor-day"
                            day_icon = "📅"
                            bg_color = "#f8f9fa"
                        
                        st.markdown(f'<div class="{day_class}" style="background-color: {bg_color} !important; color: #000000 !important;"><div class="monitor-day-header" style="color: #0066cc !important; background-color: transparent !important;">{day_icon} {day_date.strftime("%a %b %d")}</div>', unsafe_allow_html=True)
                        display_day_activities(display_df, day_date)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Move to next week
                current_date = week_end + timedelta(days=1)
    
    # Kid Manager Section
    elif current_page == "👶 Kids":
        st.header("👶 Kid Manager")
        
        kids = display_df['kid_name'].unique() if not display_df.empty else []
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_kid = st.selectbox("Select kid:", ["➕ Add New"] + list(kids))
        
        with col2:
            if st.button("💾 Save"):
                if save_data_to_csv(st.session_state.activities_df, st.session_state.csv_file):
                    st.success("Saved!")
        
        if selected_kid == "➕ Add New":
            st.subheader("Add Activity")
            with st.form("add_kid_form"):
                new_kid_name = st.text_input("Kid:")
                new_activity = st.text_input("Activity:")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_time = st.time_input("Time:")
                with col2:
                    new_duration = st.number_input("Hours:", min_value=0.5, step=0.5, value=1.0)
                
                new_frequency = st.selectbox("Frequency:", ["weekly", "bi-weekly", "daily"])
                
                days_options = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                selected_days = st.multiselect("Days:", days_options)
                
                col1, col2 = st.columns(2)
                with col1:
                    new_start_date = st.date_input("Start:", value=date.today())
                with col2:
                    new_end_date = st.date_input("End:", value=date.today() + timedelta(days=365))
                
                new_address = st.text_input("Address:")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_pickup_driver = st.text_input("Pickup:")
                with col2:
                    new_return_driver = st.text_input("Return:")
                
                submitted = st.form_submit_button("➕ Add")
                if submitted and new_kid_name and new_activity:
                    new_row = {
                        'kid_name': new_kid_name,
                        'activity': new_activity,
                        'time': str(new_time),
                        'duration': new_duration,
                        'frequency': new_frequency,
                        'days_of_week': selected_days,
                        'start_date': new_start_date,
                        'end_date': new_end_date,
                        'address': new_address,
                        'pickup_driver': new_pickup_driver,
                        'return_driver': new_return_driver
                    }
                    st.session_state.activities_df = pd.concat([
                        st.session_state.activities_df, 
                        pd.DataFrame([new_row])
                    ], ignore_index=True)
                    auto_save_activities()
        
        elif selected_kid in kids:
            st.subheader(f"Managing: {selected_kid}")
            
            selected_week_date = st.date_input("Week for stats:", value=date.today())
            week_start, week_end = get_week_dates(selected_week_date)
            
            daily_hours = calculate_hours_by_day(st.session_state.activities_df, selected_kid, week_start, week_end)
            weekly_hours = calculate_weekly_hours(st.session_state.activities_df, selected_kid, week_start, week_end)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Weekly Hours", f"{weekly_hours:.1f}h")
            with col2:
                daily_df = pd.DataFrame(list(daily_hours.items()), columns=['Day', 'Hours'])
                fig = px.bar(daily_df, x='Day', y='Hours', title=f"{selected_kid}'s Hours")
                st.plotly_chart(fig, use_container_width=True)
            
            kid_activities = st.session_state.activities_df[st.session_state.activities_df['kid_name'] == selected_kid]
            
            for idx, activity in kid_activities.iterrows():
                with st.expander(f"{activity['activity']} - {activity['time']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Duration:** {activity['duration']}h")
                        st.write(f"**Days:** {', '.join(activity['days_of_week'])}")
                        st.write(f"**Address:** {activity['address']}")
                    with col2:
                        st.write(f"**Pickup:** {activity['pickup_driver']}")
                        st.write(f"**Return:** {activity['return_driver']}")
                        st.write(f"**Dates:** {activity['start_date']} to {activity['end_date']}")
                    
                    if st.button(f"🗑️ Delete {idx}"):
                        st.session_state.activities_df = st.session_state.activities_df.drop(idx).reset_index(drop=True)
                        auto_save_activities()
                        st.rerun()
    
    # Driver View Section
    elif current_page == "🚗 Drivers":
        st.header("🚗 Driver View")
        
        if display_df.empty:
            st.info("No activities available!")
        else:
            selected_week_date = st.date_input("Week:", value=date.today())
            week_start, week_end = get_week_dates(selected_week_date)
            
            # Get unique drivers
            pickup_drivers = display_df['pickup_driver'].unique()
            return_drivers = display_df['return_driver'].unique()
            all_drivers = list(set(list(pickup_drivers) + list(return_drivers)))
            
            # Default to Ronen if available, otherwise first driver
            default_driver = "Ronen" if "Ronen" in all_drivers else all_drivers[0] if all_drivers else ""
            
            selected_driver = st.selectbox("Select driver:", all_drivers, index=all_drivers.index(default_driver) if default_driver in all_drivers else 0)
            
            if selected_driver:
                st.subheader(f"Schedule for {selected_driver}")
                
                driver_activities = display_df[
                    ((display_df['pickup_driver'] == selected_driver) |
                     (display_df['return_driver'] == selected_driver)) &
                    (display_df['start_date'] <= week_end) &
                    (display_df['end_date'] >= week_start)
                ]
                
                if not driver_activities.empty:
                    driver_schedule = []
                    for _, activity in driver_activities.iterrows():
                        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
                        
                        for day in days:
                            schedule_item = {
                                'Day': day.capitalize(),
                                'Kid': activity['kid_name'],
                                'Activity': activity['activity'],
                                'Time': activity['time'],
                                'Address': activity['address'],
                                'Type': 'Pickup' if activity['pickup_driver'] == selected_driver else 'Return'
                            }
                            driver_schedule.append(schedule_item)
                    
                    driver_df = pd.DataFrame(driver_schedule)
                    driver_df = driver_df.sort_values(['Day', 'Time'])
                    
                    # Convert day names to proper order for sorting
                    day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
                    driver_df['Day_Order'] = driver_df['Day'].map(day_order)
                    driver_df = driver_df.sort_values(['Day_Order', 'Time']).drop('Day_Order', axis=1)
                    
                    # Display schedule
                    for _, item in driver_df.iterrows():
                        with st.container():
                            st.markdown(f"**{item['Day']} - {item['Time']}**")
                            st.write(f"{item['Type']}: {item['Kid']} - {item['Activity']}")
                            st.write(f"Address: [{item['Address']}](https://www.google.com/maps/search/?api=1&query={item['Address'].replace(' ', '+')})")
                            st.markdown("---")
                else:
                    st.info(f"No activities for {selected_driver} this week")
    
    # Data Management Section
    elif current_page == "⚙️ Data":
        st.header("⚙️ Data Management")
        
        st.info("""
        **📊 Primary Data Source:** Google Sheets
        
        Your activities are now stored in Google Sheets and automatically sync with the app.
        The local CSV file is only used for backup/export purposes.
        
        **🔗 [Edit in Google Sheets](https://docs.google.com/spreadsheets/d/1TS4zfU5BT1e80R5VMoZFkbLlH-yj2ZWGWHMd0qMO4wA/edit)**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Import")
            uploaded_file = st.file_uploader("Upload CSV:", type=['csv'])
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    df = migrate_dataframe(df)
                    st.session_state.activities_df = df
                    st.success("Imported! Note: This only updates the local session. For permanent changes, edit the Google Sheet.")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            st.subheader("Export")
            if not st.session_state.activities_df.empty:
                csv_data = st.session_state.activities_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="activities_backup.csv",
                    mime="text/csv",
                    help="Download current data as backup CSV"
                )
        
        if not st.session_state.activities_df.empty:
            st.subheader("Current Data")
            st.dataframe(st.session_state.activities_df, use_container_width=True)
        else:
            st.info("No data available.")

if __name__ == "__main__":
    main() 