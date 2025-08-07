import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import webbrowser
import os
from typing import Dict, List, Tuple
import json

# Page configuration
st.set_page_config(
    page_title="Weekly Planner - Afterschool Activities",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
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

# Helper functions
def migrate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Migrate old dataframe to new schema with start_date and end_date"""
    if df.empty:
        return df
    
    # Check if start_date and end_date columns exist
    if 'start_date' not in df.columns:
        df['start_date'] = date.today()
    if 'end_date' not in df.columns:
        df['end_date'] = date.today() + timedelta(days=365)
    
    # Convert date columns to proper format
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
            # Convert days_of_week from string back to list if needed
            if 'days_of_week' in df.columns:
                df['days_of_week'] = df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            
            # Migrate dataframe to new schema
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

def save_data_to_csv(df: pd.DataFrame, filename: str):
    """Save activities data to CSV file"""
    try:
        # Convert days_of_week list to JSON string for CSV storage
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
        st.success("✅ Activity saved automatically!")

def get_week_dates(selected_date: date) -> Tuple[date, date]:
    """Get start and end of week for a given date"""
    # Get Monday of the week
    days_since_monday = selected_date.weekday()
    monday = selected_date - timedelta(days=days_since_monday)
    # Get Sunday of the week
    sunday = monday + timedelta(days=6)
    return monday, sunday

def get_current_week_dates() -> Tuple[date, date]:
    """Get current week's Monday and Sunday"""
    today = date.today()
    return get_week_dates(today)

def is_activity_active_in_week(activity_start: date, activity_end: date, week_start: date, week_end: date) -> bool:
    """Check if activity is active during the specified week"""
    # Activity is active if it overlaps with the week
    return activity_start <= week_end and activity_end >= week_start

def calculate_hours_by_day(df: pd.DataFrame, kid_name: str, week_start: date = None, week_end: date = None) -> Dict[str, float]:
    """Calculate daily hours for a specific kid within a date range"""
    kid_activities = df[df['kid_name'] == kid_name]
    # Exclude school activities from hours calculation
    kid_activities = kid_activities[kid_activities['activity'].str.lower() != 'school']
    
    daily_hours = {day: 0.0 for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']}
    
    for _, activity in kid_activities.iterrows():
        # Check if activity is active in the specified week
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
    
    # Exclude school activities from drive calculations
    filtered_df = df[df['activity'].str.lower() != 'school']
    
    for _, activity in filtered_df.iterrows():
        # Check if activity is active in the specified week
        if not is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end):
            continue
            
        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
        num_days = len(days)
        
        # Count pickup drives
        pickup_driver = activity['pickup_driver']
        if pickup_driver not in drives_count:
            drives_count[pickup_driver] = 0
        drives_count[pickup_driver] += num_days
        
        # Count return drives
        return_driver = activity['return_driver']
        if return_driver not in drives_count:
            drives_count[return_driver] = 0
        drives_count[return_driver] += num_days
    
    return drives_count

def open_google_maps(address: str):
    """Open Google Maps with the given address"""
    encoded_address = address.replace(' ', '+')
    url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
    webbrowser.open(url)

def create_weekly_schedule(df: pd.DataFrame, week_start: date, week_end: date) -> pd.DataFrame:
    """Create a weekly schedule table organized by day and driver for a specific week"""
    if df.empty:
        return pd.DataFrame()
    
    # Keep all activities (including school) in the schedule display
    weekly_data = []
    
    for _, activity in df.iterrows():
        # Check if activity is active in the specified week
        if not is_activity_active_in_week(activity['start_date'], activity['end_date'], week_start, week_end):
            continue
            
        days = activity['days_of_week'] if isinstance(activity['days_of_week'], list) else []
        
        for day in days:
            # Calculate end time
            start_time = pd.to_datetime(activity['time']).time()
            duration_hours = float(activity['duration'])
            duration_minutes = int(duration_hours * 60)
            
            # Calculate end time
            start_datetime = datetime.combine(date.today(), start_time)
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            end_time = end_datetime.time().strftime('%H:%M')
            
            weekly_data.append({
                'Day': day.capitalize(),
                'Kid': activity['kid_name'],
                'Activity': activity['activity'],
                'Time': f"{activity['time'][:5]} - {end_time}",
                'Duration': f"{activity['duration']}h",
                'Address': activity['address'],
                'Pickup Driver': activity['pickup_driver'],
                'Return Driver': activity['return_driver'],
                'Start Date': activity['start_date'],
                'End Date': activity['end_date']
            })
    
    weekly_df = pd.DataFrame(weekly_data)
    if not weekly_df.empty:
        weekly_df = weekly_df.sort_values(['Day', 'Time'])
    
    return weekly_df

# Main application
def main():
    st.markdown('<h1 class="main-header"> Weekly Planner - Afterschool Activities</h1>', unsafe_allow_html=True)
    
    # Load data
    st.session_state.activities_df = load_data_from_csv(st.session_state.csv_file)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Weekly View", "Kid Manager", "Driver View", "Data Management"]
    )
    
    # Weekly View Section (now the landing page)
    if page == "Weekly View":
        if st.session_state.activities_df.empty:
            st.info("No activities available. Add some activities first!")
        else:
            # Title and selectors on the same line
            col1, col2, col3 = st.columns([2, 2, 2])
            
            with col1:
                st.header(" Weekly Schedule")
            
            with col2:
                # Week selector
                current_week_start, current_week_end = get_current_week_dates()
                selected_week_date = st.date_input(
                    "Select week:",
                    value=date.today(),
                    help="Select any date in the week you want to view"
                )
            
            with col3:
                # Kid filter
                kids = st.session_state.activities_df['kid_name'].unique()
                selected_kid_filter = st.selectbox(
                    "Filter by kid:",
                    ["All Kids"] + list(kids),
                    help="Select a specific kid to filter the schedule, or 'All Kids' to see everyone"
                )
            
            week_start, week_end = get_week_dates(selected_week_date)
            st.info(f"📅 Viewing week: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
            
            weekly_schedule = create_weekly_schedule(st.session_state.activities_df, week_start, week_end)
            
            # Apply kid filter if selected
            if selected_kid_filter != "All Kids":
                weekly_schedule = weekly_schedule[weekly_schedule['Kid'] == selected_kid_filter]
                st.info(f"👶 Showing schedule for: {selected_kid_filter}")
            
            if not weekly_schedule.empty:
                # Toggle to show/hide past days
                show_past_days = st.checkbox("Show past days", value=False, help="Toggle to show or hide days that have already passed")
                
                # Create clickable address links
                def make_address_clickable(address):
                    return f'<a href="https://www.google.com/maps/search/?api=1&query={address.replace(" ", "+")}" target="_blank">{address}</a>'
                
                weekly_schedule['Address'] = weekly_schedule['Address'].apply(make_address_clickable)
                
                # Display schedule by day
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                today = date.today()
                
                for day in days_order:
                    day_activities = weekly_schedule[weekly_schedule['Day'] == day]
                    if not day_activities.empty:
                        # Check if this day has passed (for current week only)
                        day_date = None
                        if week_start <= today <= week_end:  # Current week
                            day_index = days_order.index(day)
                            day_date = week_start + timedelta(days=day_index)
                            
                            # Skip past days unless show_past_days is True
                            if day_date < today and not show_past_days:
                                continue
                        
                        st.markdown(f"### {day}")
                        st.markdown(day_activities.to_html(escape=False, index=False), unsafe_allow_html=True)
                        st.markdown("---")
                
                # Summary statistics AFTER the schedule
                st.markdown('<div class="summary-stats">', unsafe_allow_html=True)
                st.subheader("📊 Weekly Summary")
                
                # Calculate summary statistics
                kids_in_schedule = weekly_schedule['Kid'].unique()
                kids_hours = {}
                for kid in kids_in_schedule:
                    kids_hours[kid] = calculate_weekly_hours(st.session_state.activities_df, kid, week_start, week_end)
                
                drives_per_driver = calculate_drives_per_driver(st.session_state.activities_df, week_start, week_end)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_activities = len(weekly_schedule)
                    st.metric("Total Activities", total_activities)
                
                with col2:
                    unique_kids = weekly_schedule['Kid'].nunique()
                    st.metric("Kids Involved", unique_kids)
                
                with col3:
                    unique_drivers = len(set(weekly_schedule['Pickup Driver'].tolist() + weekly_schedule['Return Driver'].tolist()))
                    st.metric("Drivers Involved", unique_drivers)
                
                with col4:
                    total_hours = sum(kids_hours.values())
                    st.metric("Total Hours", f"{total_hours:.1f}h")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display hours per kid
                st.subheader("👶 Hours per Kid")
                kids_hours_df = pd.DataFrame(list(kids_hours.items()), columns=['Kid', 'Hours'])
                kids_hours_df = kids_hours_df.sort_values('Hours', ascending=False)
                st.dataframe(kids_hours_df, use_container_width=True, hide_index=True)
                
                # Display drives per driver
                st.subheader("🚗 Drives per Driver")
                drives_df = pd.DataFrame(list(drives_per_driver.items()), columns=['Driver', 'Number of Drives'])
                drives_df = drives_df.sort_values('Number of Drives', ascending=False)
                st.dataframe(drives_df, use_container_width=True, hide_index=True)
                
            else:
                if selected_kid_filter != "All Kids":
                    st.info(f"No activities scheduled for {selected_kid_filter} in the selected week")
                else:
                    st.info("No activities scheduled for the selected week")
    
    # Data Management Section
    elif page == "Data Management":
        st.header(" Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Import Data")
            uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    # Migrate imported data
                    df = migrate_dataframe(df)
                    st.session_state.activities_df = df
                    if save_data_to_csv(st.session_state.activities_df, st.session_state.csv_file):
                        st.success("Data imported and saved successfully!")
                except Exception as e:
                    st.error(f"Error importing file: {e}")
        
        with col2:
            st.subheader("Export Data")
            if not st.session_state.activities_df.empty:
                csv_data = st.session_state.activities_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="activities.csv",
                    mime="text/csv"
                )
        
        # Display current data
        st.subheader("Current Data")
        if not st.session_state.activities_df.empty:
            st.dataframe(st.session_state.activities_df, use_container_width=True)
        else:
            st.info("No data available. Add activities to get started!")
    
    # Kid Manager Section
    elif page == "Kid Manager":
        st.header("👶 Kid Manager")
        
        # Kid selection
        kids = st.session_state.activities_df['kid_name'].unique() if not st.session_state.activities_df.empty else []
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_kid = st.selectbox("Select a kid:", ["Add New Kid"] + list(kids))
        
        with col2:
            if st.button("💾 Manual Save"):
                if save_data_to_csv(st.session_state.activities_df, st.session_state.csv_file):
                    st.success("Data saved manually!")
        
        # Add new kid or manage existing kid
        if selected_kid == "Add New Kid":
            st.subheader("Add New Kid")
            with st.form("add_kid_form"):
                new_kid_name = st.text_input("Kid Name:")
                new_activity = st.text_input("Activity Name:")
                new_time = st.time_input("Time:")
                new_duration = st.number_input("Duration (hours):", min_value=0.5, step=0.5, value=1.0)
                new_frequency = st.selectbox("Frequency:", ["daily", "weekly", "bi-weekly"])
                
                # Days selection
                st.write("Select days:")
                days_options = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                selected_days = st.multiselect("Days of week:", days_options)
                
                # Date range selection
                col1, col2 = st.columns(2)
                with col1:
                    new_start_date = st.date_input("Start Date:", value=date.today())
                with col2:
                    new_end_date = st.date_input("End Date:", value=date.today() + timedelta(days=365))
                
                new_address = st.text_input("Address:")
                new_pickup_driver = st.text_input("Pickup Driver:")
                new_return_driver = st.text_input("Return Driver:")
                
                submitted = st.form_submit_button("➕ Add Activity")
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
                    
                    # Auto-save after adding activity
                    auto_save_activities()
        
        # Manage existing kid
        elif selected_kid in kids:
            st.subheader(f"Managing: {selected_kid}")
            
            # Week selector for kid manager
            current_week_start, current_week_end = get_current_week_dates()
            selected_week_date = st.date_input(
                "Select week for calculations:",
                value=date.today(),
                help="Select any date in the week you want to view"
            )
            week_start, week_end = get_week_dates(selected_week_date)
            st.info(f"📅 Viewing week: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
            
            # Display statistics
            daily_hours = calculate_hours_by_day(st.session_state.activities_df, selected_kid, week_start, week_end)
            weekly_hours = calculate_weekly_hours(st.session_state.activities_df, selected_kid, week_start, week_end)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Weekly Hours", f"{weekly_hours:.1f}h")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Daily hours chart
                daily_df = pd.DataFrame(list(daily_hours.items()), columns=['Day', 'Hours'])
                fig = px.bar(daily_df, x='Day', y='Hours', title=f"Daily Hours for {selected_kid} ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})")
                st.plotly_chart(fig, use_container_width=True)
            
            # Display activities
            st.subheader("Activities")
            kid_activities = st.session_state.activities_df[st.session_state.activities_df['kid_name'] == selected_kid]
            
            for idx, activity in kid_activities.iterrows():
                with st.expander(f"{activity['activity']} - {activity['time']} ({activity['start_date']} to {activity['end_date']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Duration:** {activity['duration']} hours")
                        st.write(f"**Frequency:** {activity['frequency']}")
                        st.write(f"**Days:** {', '.join(activity['days_of_week'])}")
                        st.write(f"**Date Range:** {activity['start_date']} to {activity['end_date']}")
                    with col2:
                        st.write(f"**Address:** {activity['address']}")
                        st.write(f"**Pickup:** {activity['pickup_driver']}")
                        st.write(f"**Return:** {activity['return_driver']}")
                    
                    if st.button(f"️ Delete Activity {idx}"):
                        st.session_state.activities_df = st.session_state.activities_df.drop(idx).reset_index(drop=True)
                        # Auto-save after deleting activity
                        auto_save_activities()
                        st.rerun()
    
    # Driver View Section
    elif page == "Driver View":
        st.header("🚗 Driver View")
        
        if st.session_state.activities_df.empty:
            st.info("No activities available. Add some activities first!")
        else:
            # Week selector for driver view
            current_week_start, current_week_end = get_current_week_dates()
            selected_week_date = st.date_input(
                "Select week for driver schedule:",
                value=date.today(),
                help="Select any date in the week you want to view"
            )
            week_start, week_end = get_week_dates(selected_week_date)
            st.info(f"📅 Viewing week: {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
            
            # Get unique drivers
            pickup_drivers = st.session_state.activities_df['pickup_driver'].unique()
            return_drivers = st.session_state.activities_df['return_driver'].unique()
            all_drivers = list(set(list(pickup_drivers) + list(return_drivers)))
            
            selected_driver = st.selectbox("Select Driver:", all_drivers)
            
            if selected_driver:
                st.subheader(f"Schedule for {selected_driver}")
                
                # Filter activities for this driver and week
                driver_activities = st.session_state.activities_df[
                    ((st.session_state.activities_df['pickup_driver'] == selected_driver) |
                     (st.session_state.activities_df['return_driver'] == selected_driver)) &
                    (st.session_state.activities_df['start_date'] <= week_end) &
                    (st.session_state.activities_df['end_date'] >= week_start)
                ]
                
                if not driver_activities.empty:
                    # Create driver schedule
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
                    
                    # Display schedule
                    for _, item in driver_df.iterrows():
                        st.markdown(f"""
                        <div class="driver-schedule">
                            <strong>{item['Day']} - {item['Time']}</strong><br>
                            {item['Type']}: {item['Kid']} - {item['Activity']}<br>
                            Address: <a href="#" onclick="window.open('https://www.google.com/maps/search/?api=1&query={item['Address'].replace(' ', '+')}', '_blank')" class="address-link">{item['Address']}</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"No activities found for {selected_driver} in the selected week")

if __name__ == "__main__":
    main() 