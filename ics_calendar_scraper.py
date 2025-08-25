#!/usr/bin/env python3
"""
Generalized ICS Calendar Scraper Base Class
Base class for downloading and parsing ICS calendar feeds and converting them to weekly planner CSV format
"""

import requests
import pandas as pd
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from icalendar import Calendar
import pytz

class ICSCalendarScraper:
    """Base class for scraping ICS calendar feeds"""
    
    def __init__(self, calendar_name: str):
        self.calendar_name = calendar_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def download_ics_feed(self, url: str) -> Optional[str]:
        """Download ICS content from a URL"""
        try:
            print(f"Downloading {self.calendar_name} ICS feed...")
            response = self.session.get(url)
            response.raise_for_status()
            
            print(f"Successfully downloaded {self.calendar_name} feed ({len(response.content)} bytes)")
            return response.content.decode('utf-8')
            
        except Exception as e:
            print(f"Error downloading {self.calendar_name} feed: {e}")
            return None
    
    def parse_ics_feed(self, ics_content: str, feed_identifier: str = "") -> List[Dict]:
        """Parse ICS content and extract events"""
        events = []
        
        try:
            # Parse ICS content
            cal = Calendar.from_ical(ics_content)
            
            print(f"Parsing {self.calendar_name} calendar with {len(cal.walk('VEVENT'))} events...")
            
            # Get current date for filtering
            current_date = datetime.now().date()
            print(f"Filtering {self.calendar_name} events from {current_date} onwards...")
            
            for component in cal.walk('VEVENT'):
                event = self._parse_ics_event(component, feed_identifier)
                if event:
                    # Filter out past events
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    if event_date >= current_date:
                        events.append(event)
            
            print(f"Successfully parsed {len(events)} current/future events from {self.calendar_name}")
            
        except Exception as e:
            print(f"Error parsing {self.calendar_name} ICS feed: {e}")
            # Fallback: create sample events
            events = self._create_sample_events(2025, feed_identifier)
        
        return events
    
    def _parse_ics_event(self, component, feed_identifier: str = "") -> Optional[Dict]:
        """Parse individual ICS event component - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _parse_ics_event")
    
    def _categorize_event(self, event_name: str) -> str:
        """Categorize events based on their names - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _categorize_event")
    
    def _get_event_location(self, event_name: str, feed_identifier: str = "") -> str:
        """Get event location - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _get_event_location")
    
    def _create_sample_events(self, year: int, feed_identifier: str = "") -> List[Dict]:
        """Create sample events - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _create_sample_events")
    
    def _calculate_duration(self, start_dt: datetime, end_dt: datetime) -> float:
        """Calculate duration between start and end times in hours"""
        try:
            # Handle overnight events
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            duration = (end_dt - start_dt).total_seconds() / 3600
            return round(duration, 2)
        except:
            return 1.0  # Default 1 hour
    
    def convert_to_planner_format(self, events: List[Dict], prefix: str = "") -> pd.DataFrame:
        """Convert parsed events to weekly planner CSV format"""
        planner_events = []
        
        for event in events:
            try:
                # Parse date
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                
                # Get start time and duration
                start_time = event['start_time']
                duration = event['duration']
                
                # Determine frequency and days
                if event.get('is_recurring', False):
                    frequency = 'weekly'
                    days_of_week = event.get('days_of_week', '["' + event_date.strftime('%A').lower() + '"]')
                else:
                    frequency = 'one-time'
                    days_of_week = '["' + event_date.strftime('%A').lower() + '"]'
                
                # Create activity name with prefix
                activity_name = event['name']
                if prefix:
                    activity_name = f"{prefix}: {activity_name}"
                
                # Create planner event
                planner_event = {
                    'kid_name': 'All',  # Calendar events typically affect all family members
                    'activity': activity_name,
                    'time': start_time,
                    'duration': duration,
                    'frequency': frequency,
                    'days_of_week': days_of_week,
                    'start_date': event['date'],
                    'end_date': event['date'],  # One-time events
                    'address': event['location'],
                    'pickup_driver': 'N/A',
                    'return_driver': 'N/A'
                }
                
                planner_events.append(planner_event)
                
            except Exception as e:
                print(f"Error converting event {event}: {e}")
                continue
        
        return pd.DataFrame(planner_events)
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """Save events to CSV file"""
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} events to {filename}")
    
    def merge_with_existing_csv(self, new_events_df: pd.DataFrame, existing_csv: str = 'activities.csv'):
        """Merge new events with existing CSV, avoiding duplicates"""
        try:
            # Load existing CSV
            existing_df = pd.read_csv(existing_csv)
            print(f"Loaded existing CSV with {len(existing_df)} activities")
            
            # Create a key for duplicate detection
            existing_df['event_key'] = existing_df['activity'] + existing_df['start_date']
            new_events_df['event_key'] = new_events_df['activity'] + new_events_df['start_date']
            
            # Find new events (not in existing CSV)
            existing_keys = set(existing_df['event_key'])
            new_events_filtered = new_events_df[~new_events_df['event_key'].isin(existing_keys)]
            
            print(f"Found {len(new_events_filtered)} new events to add")
            
            if len(new_events_filtered) > 0:
                # Remove the temporary key column
                new_events_filtered = new_events_filtered.drop('event_key', axis=1)
                existing_df = existing_df.drop('event_key', axis=1)
                
                # Combine dataframes
                combined_df = pd.concat([existing_df, new_events_filtered], ignore_index=True)
                
                # Save back to CSV
                combined_df.to_csv(existing_csv, index=False)
                print(f"Successfully merged {len(new_events_filtered)} new events into {existing_csv}")
                print(f"Total activities: {len(combined_df)}")
            else:
                print("No new events to add")
                
        except FileNotFoundError:
            print(f"Existing CSV {existing_csv} not found, saving as new file")
            new_events_df.to_csv(existing_csv, index=False)
        except Exception as e:
            print(f"Error merging with existing CSV: {e}")
    
    def scrape_and_convert(self, url: str, output_filename: str, prefix: str = "") -> pd.DataFrame:
        """Main method to scrape ICS feed and convert to planner format"""
        print(f"Scraping {self.calendar_name} calendar...")
        
        # Download ICS feed
        ics_content = self.download_ics_feed(url)
        
        if ics_content:
            # Parse events from ICS
            events = self.parse_ics_feed(ics_content)
            
            if events:
                # Convert to planner format
                planner_df = self.convert_to_planner_format(events, prefix)
                
                if not planner_df.empty:
                    # Save to file
                    self.save_to_csv(planner_df, output_filename)
                    print(f"Successfully processed {len(events)} events from {self.calendar_name}")
                    return planner_df
                else:
                    print("No events could be converted to planner format")
            else:
                print(f"No events were parsed from {self.calendar_name} feed")
        else:
            print(f"Failed to download {self.calendar_name} feed")
        
        return pd.DataFrame()
