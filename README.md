# Weekly Planner - Afterschool Activities

A comprehensive Streamlit application for managing afterschool activities for multiple kids, including driver scheduling and weekly planning.

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

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
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

## File Structure

- `app.py`: Main Streamlit application
- `requirements.txt`: Python dependencies
- `activities.csv`: Data storage file (created automatically)
- `README.md`: This documentation file 