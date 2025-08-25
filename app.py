import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import webbrowser
import os
from typing import Dict, List, Tuple
import json

# Add this function at the top level, before the main() function
def make_address_clickable(address):
    """Convert address to clickable Google Maps link with truncated display text"""
    # Handle NaN/None values
    if pd.isna(address) or address is None:
        return "No address"
    
    # Convert to string if it's not already
    address_str = str(address)
    
    # Truncate address to 15 characters for display
    display_text = address_str[:15] + "..." if len(address_str) > 15 else address_str
    return f'<a href="https://www.google.com/maps/search/?api=1&query={address_str.replace(" ", "+")}" target="_blank">{display_text}</a>'

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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'activities_df' not in st.session_state:
    st.session_state.activities_df = pd.DataFrame(columns=[
        'kid_name', 'activity', 'time', 'duration', 'frequency', 
        'days_of_week', 'start_date', 'end_date', 'address', 'pickup_driver', 'return_driver'
    ])

if 'csv_file' not in st.session_state:
    st.session_state.csv_file = 'activities.csv'

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
    """Load and combine activities.csv with school_events.csv and jewish_holidays.csv for display purposes"""
    # Load main activities
    activities_df = load_data_from_csv('activities.csv')
    
    # Load school events if available
    school_events_df = pd.DataFrame()
    if os.path.exists('school_events.csv'):
        try:
            school_events_df = pd.read_csv('school_events.csv')
            if 'days_of_week' in school_events_df.columns:
                school_events_df['days_of_week'] = school_events_df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            
            # Convert date columns to proper date objects (same as load_data_from_csv)
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
            
            # Convert date columns to proper date objects
            if 'start_date' in jewish_holidays_df.columns:
                jewish_holidays_df['start_date'] = pd.to_datetime(jewish_holidays_df['start_date']).dt.date
            if 'end_date' in jewish_holidays_df.columns:
                jewish_holidays_df['end_date'] = pd.to_datetime(jewish_holidays_df['end_date']).dt.date
            
            print(f"Loaded {len(jewish_holidays_df)} Jewish holidays")
        except Exception as e:
            print(f"Warning: Could not load Jewish holidays: {e}")
    
    # Combine all dataframes
    all_dataframes = [activities_df]
    total_events = len(activities_df)
    
    if not school_events_df.empty:
        all_dataframes.append(school_events_df)
        total_events += len(school_events_df)
    
    if not jewish_holidays_df.empty:
        all_dataframes.append(jewish_holidays_df)
        total_events += len(jewish_holidays_df)
    
    if len(all_dataframes) > 1:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        print(f"Combined {len(activities_df)} activities + {len(school_events_df)} school events + {len(jewish_holidays_df)} Jewish holidays = {len(combined_df)} total")
        return combined_df
    else:
        print(f"Using only activities: {len(activities_df)} events")
        return activities_df

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
    if df.empty:
        return pd.DataFrame()
    
    weekly_data = []
    
    for _, activity in df.iterrows():
        if not is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end):
            continue
            
        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
        
        for day in days:
            # Calculate the actual date for this day in the week
            day_index = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(day.lower())
            day_date = week_start + timedelta(days=day_index)
            
            # Only show activity if it's active on this specific day
            if activity['start_date'] <= day_date <= activity['end_date']:
                start_time = pd.to_datetime(activity['time']).time()
                duration_hours = float(activity['duration'])
                duration_minutes = int(duration_hours * 60)
                
                start_datetime = datetime.combine(date.today(), start_time)
                end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                end_time = end_datetime.time().strftime('%H:%M')
                
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
                    'Time': f"{activity['time'][:5]}-{end_time}",
                    'Address': activity['address'],
                    'Pickup': activity['pickup_driver'],
                    'Return': activity['return_driver'],
                    'Start Date': activity['start_date'],
                    'End Date': activity['end_date']
                })
    
    weekly_df = pd.DataFrame(weekly_data)
    if not weekly_df.empty:
        weekly_df = weekly_df.sort_values(['Day', 'Time'])
    
    return weekly_df

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

# Main application
def main():
    # Define day order and abbreviations for schedule display
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_abbrev = ['M', 'T', 'W', 'Th', 'F', 'S', 'Su']
    
    st.markdown('<h1 class="main-header"> Weekly Planner</h1>', unsafe_allow_html=True)
    
    # Load data - keep original for editing, use combined for display
    st.session_state.activities_df = load_data_from_csv(st.session_state.csv_file)
    display_df = load_combined_data_for_display()  # Combined data for display
    
    # Mobile-optimized navigation
    st.sidebar.title("Menu")
    
    # Use radio buttons for cleaner mobile experience
    page = st.sidebar.radio(
        "Choose:",
        ["📋 Schedule", "👶 Kids", "🚗 Drivers", "⚙️ Data"],
        label_visibility="collapsed"  # Hide the label to save space
    )
    
    # Set default page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📋 Schedule"
    
    # Weekly View Section (landing page)
    if page == "📋 Schedule":
        if display_df.empty:
            st.info("No activities available. Add some activities first!")
        else:
            # Display the table first (with smart week selection)
            current_week_start, current_week_end = get_current_week_dates()
            
            # Use server time converted to Pacific timezone
            server_now = datetime.now()
            pacific_time = server_now - timedelta(hours=7)  # UTC-7 for Pacific Daylight Time
            today = pacific_time.date()  # Use Pacific date for filtering
            
            # Determine which week to show
            if today.weekday() >= 5:  # Saturday (5) or Sunday (6)
                # Show next week
                next_week_start = current_week_end + timedelta(days=1)  # Monday of next week
                week_start, week_end = get_week_dates(next_week_start)
                week_description = f"next week"
            else:
                # Show current week
                week_start, week_end = get_current_week_dates()
                week_description = f"current week"
            
            # Also get the following week for extended view
            following_week_start = week_end + timedelta(days=1)  # Monday of following week
            following_week_end = following_week_start + timedelta(days=6)  # Sunday of following week
            
            weekly_schedule = create_weekly_schedule(display_df, week_start, week_end)
            following_week_schedule = create_weekly_schedule(display_df, following_week_start, following_week_end)
            
            # Display the table first
            if not weekly_schedule.empty:
                # Show what date range the schedule is for
                st.info(f"📅 **{week_description}:** {week_start.strftime('%m %d')} - {week_end.strftime('%m %d, %Y')} ({today.strftime('%d')}-{pacific_time.strftime('%I:%M %p')})")
                
                # Display current week schedule
                st.subheader(f"📋 {week_description.title()} Schedule")
                display_weekly_schedule(weekly_schedule, week_start, week_end, today)
                
                # Display following week schedule
                if not following_week_schedule.empty:
                    st.subheader(f"📋 Following Week Schedule ({following_week_start.strftime('%B %d')} - {following_week_end.strftime('%B %d, %Y')})")
                    st.info(f"📅 **Upcoming:** {len(following_week_schedule)} activities in the following week")
                    display_weekly_schedule(following_week_schedule, following_week_start, following_week_end, today)
                else:
                    st.caption("🔮 **Following week:** No activities scheduled")
            
            # Controls after the table
            st.markdown("---")
            st.subheader("Controls")
            
            col1, col2 = st.columns(2)
            with col1:
                selected_week_date = st.date_input(
                    "Select week:",
                    value=date.today(),
                    help="Select week"
                )
            
            with col2:
                kids = st.session_state.activities_df['kid_name'].unique()
                selected_kid_filter = st.selectbox(
                    "Filter by kid:",
                    ["All Kids"] + list(kids),
                    help="Filter by kid"
                )
            
            # Show the selected week info
            week_start, week_end = get_week_dates(selected_week_date)
            st.caption(f"📅 {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")
            
            # Recalculate and display filtered schedule
            if selected_kid_filter != "All Kids" or selected_week_date != date.today():
                st.subheader("Filtered Schedule")
                
                # Recalculate schedule with new filters
                new_weekly_schedule = create_weekly_schedule(display_df, week_start, week_end)
                
                if selected_kid_filter != "All Kids":
                    new_weekly_schedule = new_weekly_schedule[new_weekly_schedule['Kid'] == selected_kid_filter[0].upper()]
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
                        kids_in_schedule = weekly_schedule['Kid'].unique()
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
                        st.metric("Activities", len(weekly_schedule))
                        st.metric("Kids", len(kids_in_schedule))
                    with col2:
                        total_hours = sum(kids_hours.values())
                        st.metric("Hours", f"{total_hours:.1f}h")
                        st.metric("Drivers", len(set(weekly_schedule['Pickup'].tolist() + weekly_schedule['Return'].tolist())))
                    
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
    
    # Kid Manager Section
    elif page == "👶 Kids":
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
    elif page == "🚗 Drivers":
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
    elif page == "⚙️ Data":
        st.header("⚙️ Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Import")
            uploaded_file = st.file_uploader("Upload CSV:", type=['csv'])
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    df = migrate_dataframe(df)
                    st.session_state.activities_df = df
                    if save_data_to_csv(st.session_state.activities_df, st.session_state.csv_file):
                        st.success("Imported!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            st.subheader("Export")
            if not st.session_state.activities_df.empty:
                csv_data = st.session_state.activities_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="activities.csv",
                    mime="text/csv"
                )
        
        if not st.session_state.activities_df.empty:
            st.subheader("Current Data")
            st.dataframe(st.session_state.activities_df, use_container_width=True)
        else:
            st.info("No data available.")

if __name__ == "__main__":
    main() 