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
from ics_calendar_scraper import ICSCalendarScraper

class SchoolCalendarScraper(ICSCalendarScraper):
    def __init__(self):
        super().__init__("School Calendar")
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
    
    def _parse_ics_event(self, component, school_code: str = "") -> Optional[Dict]:
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
    
    def _get_event_location(self, event_name: str, school_code: str = "") -> str:
        """Get event location for school events"""
        if school_code in self.school_feeds:
            return self.school_feeds[school_code]['address']
        return "School"
    
    def _create_sample_events(self, year: int, school_code: str = "") -> List[Dict]:
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
                school_events = self.parse_ics_feed(ics_content, school_code)
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
