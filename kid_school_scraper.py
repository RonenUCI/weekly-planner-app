#!/usr/bin/env python3
"""
Kid School Calendar Scraper
Downloads calendar events from multiple school ICS feeds and converts them to weekly planner CSV format
"""

import requests
import pandas as pd
import json
from datetime import datetime, date, timedelta
import re
from typing import List, Dict, Optional
from icalendar import Calendar
import pytz

class SchoolCalendarScraper:
    def __init__(self):
        # Define school ICS feeds
        self.school_feeds = {
            'JLS': {
                'name': 'Jane Lathrop Stanford Middle School',
                'url': 'https://jls.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=7',
                'address': '480 E Meadow Dr, Palo Alto, CA'
            },
            'Ohlone': {
                'name': 'Ohlone Elementary School',
                'url': 'https://ohlone.pausd.org/fs/calendar-manager/events.ics?calendar_ids[]=45',
                'address': '950 Amarillo Ave, Palo Alto, CA 94303'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def download_all_school_feeds(self) -> Dict[str, Optional[str]]:
        """Download ICS feeds from all schools"""
        feeds = {}
        
        for school_code, school_info in self.school_feeds.items():
            try:
                print(f"Downloading {school_info['name']} ICS feed...")
                response = self.session.get(school_info['url'])
                response.raise_for_status()
                
                feeds[school_code] = response.content.decode('utf-8')
                print(f"Successfully downloaded {school_code} feed ({len(response.content)} bytes)")
                
            except Exception as e:
                print(f"Error downloading {school_code} feed: {e}")
                feeds[school_code] = None
        
        return feeds
    
    def parse_school_feed(self, ics_content: str, school_code: str) -> List[Dict]:
        """Parse ICS content for a specific school and extract events"""
        events = []
        
        try:
            # Parse ICS content
            cal = Calendar.from_ical(ics_content)
            
            print(f"Parsing {school_code} calendar with {len(cal.walk('VEVENT'))} events...")
            
            # Get current date for filtering
            current_date = datetime.now().date()
            print(f"Filtering {school_code} events from {current_date} onwards...")
            
            for component in cal.walk('VEVENT'):
                event = self._parse_ics_event(component, school_code)
                if event:
                    # Filter out past events
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    if event_date >= current_date:
                        events.append(event)
            
            print(f"Successfully parsed {len(events)} current/future events from {school_code}")
            
        except Exception as e:
            print(f"Error parsing {school_code} ICS feed: {e}")
            # Fallback: create sample events for this school
            events = self._create_sample_events(2025, school_code)
        
        return events
    
    def _parse_ics_event(self, component, school_code: str) -> Optional[Dict]:
        """Parse individual ICS event component for a specific school"""
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
            
            # Get location
            location = str(component.get('location', self.school_feeds[school_code]['address']))
            
            # Determine category based on event name
            category = self._categorize_event(summary)
            
            return {
                'school': school_code,
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
            
        except Exception as e:
            print(f"Error parsing {school_code} ICS event: {e}")
            return None
    
    def _categorize_event(self, event_name: str) -> str:
        """Categorize events based on their names"""
        event_lower = event_name.lower()
        
        if any(word in event_lower for word in ['holiday', 'no school', 'closed']):
            return 'Holiday'
        elif any(word in event_lower for word in ['minimum day', 'early release', 'dismissal']):
            return 'Minimum Day'
        elif any(word in event_lower for word in ['staff development', 'teacher', 'professional']):
            return 'Staff Development'
        elif any(word in event_lower for word in ['picture day', 'photo']):
            return 'School Event'
        elif any(word in event_lower for word in ['back to school', 'open house', 'coffee']):
            return 'Parent Event'
        elif any(word in event_lower for word in ['first day', 'last day', 'start', 'end']):
            return 'School Year'
        elif any(word in event_lower for word in ['pta', 'parent']):
            return 'Parent Event'
        elif any(word in event_lower for word in ['farm', 'garden']):
            return 'School Event'
        else:
            return 'School Event'
    
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
    
    def _create_sample_events(self, year: int, school_code: str) -> List[Dict]:
        """Create sample events based on known school calendar structure"""
        print(f"Creating sample events for {school_code} based on known calendar...")
        
        if school_code == 'JLS':
            sample_events = [
                {
                    'school': 'JLS',
                    'date': f'{year}-08-11',
                    'name': 'District Day',
                    'description': 'District-wide professional development day',
                    'start_time': '00:00:00',
                    'end_time': '00:00:00',
                    'duration': 0,
                    'is_all_day': True,
                    'location': '480 E Meadow Dr, Palo Alto, CA',
                    'category': 'Staff Development'
                },
                {
                    'school': 'JLS',
                    'date': f'{year}-08-14',
                    'name': 'First Day of School 2025-26 School Year',
                    'description': 'First day of the new school year',
                    'start_time': '08:30:00',
                    'end_time': '14:20:00',
                    'duration': 5.83,
                    'is_all_day': False,
                    'location': '480 E Meadow Dr, Palo Alto, CA',
                    'category': 'School Year'
                }
            ]
        else:  # Ohlone
            sample_events = [
                {
                    'school': 'Ohlone',
                    'date': f'{year}-08-28',
                    'name': 'Back to School Night',
                    'description': 'Meet teachers and learn about curriculum',
                    'start_time': '17:30:00',
                    'end_time': '19:00:00',
                    'duration': 1.5,
                    'is_all_day': False,
                    'location': '950 Amarillo Ave, Palo Alto, CA 94303',
                    'category': 'Parent Event'
                },
                {
                    'school': 'Ohlone',
                    'date': f'{year}-09-01',
                    'name': 'Minimum Day',
                    'description': 'Early dismissal for all students',
                    'start_time': '00:00:00',
                    'end_time': '00:00:00',
                    'duration': 0,
                    'is_all_day': True,
                    'location': '950 Amarillo Ave, Palo Alto, CA 94303',
                    'category': 'Minimum Day'
                }
            ]
        
        return sample_events
    
    def scrape_all_schools(self) -> List[Dict]:
        """Scrape events from all schools and combine them"""
        all_events = []
        
        # Download all feeds
        feeds = self.download_all_school_feeds()
        
        # Parse each school's feed
        for school_code, ics_content in feeds.items():
            if ics_content:
                school_events = self.parse_school_feed(ics_content, school_code)
                all_events.extend(school_events)
            else:
                print(f"Using fallback data for {school_code}")
                fallback_events = self._create_sample_events(2025, school_code)
                all_events.extend(fallback_events)
        
        # Sort all events by date
        all_events.sort(key=lambda x: x['date'])
        
        print(f"\nTotal events across all schools: {len(all_events)}")
        return all_events
    
    def convert_to_planner_format(self, events: List[Dict]) -> pd.DataFrame:
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
                if event['category'] == 'Holiday':
                    frequency = 'one-time'
                else:
                    frequency = 'one-time'
                
                days_of_week = '["' + event_date.strftime('%A').lower() + '"]'
                
                # Create planner event
                planner_event = {
                    'kid_name': 'All',  # School events affect all kids
                    'activity': f"{event['school']}: {event['name']}",  # Include school prefix
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
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = 'school_events.csv'):
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

def main():
    """Main function to run the scraper"""
    scraper = SchoolCalendarScraper()
    
    # Scrape events from all schools
    print("="*60)
    print("KID SCHOOL CALENDAR SCRAPER")
    print("="*60)
    print("Scraping events from multiple schools...")
    
    all_events = scraper.scrape_all_schools()
    
    if all_events:
        # Convert to planner format
        planner_df = scraper.convert_to_planner_format(all_events)
        
        if not planner_df.empty:
            # Save to separate file first
            scraper.save_to_csv(planner_df, 'school_events.csv')
            
            # Ask user if they want to merge with existing CSV
            print("\n" + "="*50)
            print("SCRAPING COMPLETE")
            print("="*50)
            print(f"Downloaded and parsed {len(all_events)} events from all schools")
            print(f"Converted to {len(planner_df)} planner activities")
            print("\nOptions:")
            print("1. Merge with existing activities.csv")
            print("2. Save as separate school_events.csv only")
            print("3. View parsed events")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                scraper.merge_with_existing_csv(planner_df)
            elif choice == '3':
                print("\nParsed Events:")
                print(planner_df.to_string(index=False))
        else:
            print("No events could be converted to planner format")
    else:
        print("No events were parsed from any school feeds")

if __name__ == "__main__":
    main()
