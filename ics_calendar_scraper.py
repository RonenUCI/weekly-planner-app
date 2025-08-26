#!/usr/bin/env python3
"""
Generic ICS Calendar Scraper Base Class
Base class for downloading and parsing ICS calendar feeds and converting them to weekly planner CSV format
"""

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from icalendar import Calendar

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
        """Parse ICS content and extract events - generic implementation"""
        events = []
        
        try:
            # Parse ICS content
            cal = Calendar.from_ical(ics_content)
            
            print(f"Parsing {self.calendar_name} calendar with {len(cal.walk('VEVENT'))} events...")
            
            # Get current date for filtering
            current_date = datetime.now().date()
            
            # Let subclasses define their own date filtering logic
            max_date = self._get_max_date(current_date)
            if max_date:
                print(f"Filtering {self.calendar_name} events from {current_date} to {max_date}...")
            else:
                print(f"Filtering {self.calendar_name} events from {current_date} onwards...")
            
            for component in cal.walk('VEVENT'):
                event = self._parse_ics_event(component, feed_identifier)
                if event:
                    # Filter out past events
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    if event_date >= current_date:
                        # Let subclasses define their own date filtering
                        if max_date and event_date > max_date:
                            continue
                        events.append(event)
            
            print(f"Successfully parsed {len(events)} current/future events from {self.calendar_name}")
            
        except Exception as e:
            print(f"Error parsing {self.calendar_name} ICS feed: {e}")
            return []
        
        return events
    
    def _get_max_date(self, current_date: date) -> Optional[date]:
        """Get maximum date for filtering - subclasses can override for specific limits"""
        return None  # No limit by default
    
    def _parse_ics_event(self, component, feed_identifier: str = "") -> Optional[Dict]:
        """Parse individual ICS event component - generic implementation"""
        try:
            # Extract event details
            summary = str(component.get('summary', ''))
            description = str(component.get('description', ''))
            
            # Get start date/time
            start_dt = component.get('dtstart')
            if hasattr(start_dt, 'dt'):
                start_dt = start_dt.dt
            else:
                start_dt = start_dt
            
            # Get end date/time
            end_dt = component.get('dtend')
            if hasattr(end_dt, 'dt'):
                end_dt = end_dt.dt
            else:
                end_dt = end_dt
            
            # Handle all-day events
            if isinstance(start_dt, date) and not isinstance(start_dt, datetime):
                # All-day event
                start_date = start_dt
                start_time = '00:00:00'
                end_time = '00:00:00'
                duration = 0
                is_all_day = True
            else:
                # Timed event
                start_date = start_dt.date()
                start_time = start_dt.strftime('%H:%M:%S')
                
                if end_dt:
                    if isinstance(end_dt, date) and not isinstance(end_dt, datetime):
                        end_time = '23:59:59'
                        duration = 24.0
                    else:
                        end_time = end_dt.strftime('%H:%M:%S')
                        duration = self._calculate_duration(start_dt, end_dt)
                else:
                    end_time = start_time
                    duration = 1.0  # Default 1 hour
                
                is_all_day = False
            
            # Get location from ICS or use default - let subclasses override if needed
            location = str(component.get('location', 'Location TBD'))
            
            # Get category from ICS or use default - let subclasses override if needed
            category = str(component.get('categories', 'Event')) if component.get('categories') else 'Event'
            
            # Build base event structure
            event = {
                'date': start_date.strftime('%Y-%m-%d'),
                'name': summary,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'is_all_day': is_all_day,
                'location': location,
                'category': category
            }
            
            # Let subclasses add additional fields or override defaults
            event = self._enhance_event(event, feed_identifier)
            
            return event
            
        except Exception as e:
            print(f"Error parsing ICS event: {e}")
            return None
    
    def _enhance_event(self, event: Dict, feed_identifier: str = "") -> Dict:
        """Allow subclasses to add additional fields to the event"""
        return event  # Default: no enhancement
    
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
        """Convert parsed events to weekly planner CSV format - generic implementation"""
        planner_events = []
        
        for event in events:
            try:
                # Parse date
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                
                # Get start time and duration
                start_time = event['start_time']
                duration = event['duration']
                
                # Determine frequency and days - let subclasses override
                frequency, days_of_week = self._determine_frequency_and_days(event, event_date)
                
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
    
    def _determine_frequency_and_days(self, event: Dict, event_date: date) -> tuple:
        """Determine frequency and days of week - subclasses can override"""
        # Check for common recurring patterns in event names
        event_name_lower = event['name'].lower()
        
        # Weekly patterns
        if any(word in event_name_lower for word in ['shabbat', 'sabbath', 'sunday service', 'weekly meeting']):
            frequency = 'weekly'
            # Try to determine the day from the event name or use the event date
            if 'friday' in event_name_lower or 'saturday' in event_name_lower:
                days_of_week = '["friday", "saturday"]'
            elif 'sunday' in event_name_lower:
                days_of_week = '["sunday"]'
            else:
                # Default to the day of the event
                days_of_week = '["' + event_date.strftime('%A').lower() + '"]'
        else:
            # Default: one-time event on the specific day
            frequency = 'one-time'
            days_of_week = '["' + event_date.strftime('%A').lower() + '"]'
        
        return frequency, days_of_week
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """Save events to CSV file with proper escaping for addresses"""
        try:
            # Ensure addresses are properly escaped
            df_copy = df.copy()
            if 'address' in df_copy.columns:
                df_copy['address'] = df_copy['address'].astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
            
            # Save with minimal quoting to avoid deployment issues
            df_copy.to_csv(filename, index=False, quoting=0)  # quoting=0 uses QUOTE_MINIMAL
            print(f"Saved {len(df)} events to {filename}")
        except Exception as e:
            print(f"Error saving CSV: {e}")
            # Fallback to basic CSV saving
            df.to_csv(filename, index=False)
    
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
