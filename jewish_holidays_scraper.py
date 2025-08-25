#!/usr/bin/env python3
"""
Jewish Holidays Scraper
Downloads Jewish holidays and observances from Hebcal ICS feed and converts them to weekly planner CSV format
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

class JewishHolidaysScraper(ICSCalendarScraper):
    def __init__(self):
        super().__init__("Jewish Holidays")
        self.hebcal_url = "https://download.hebcal.com/v4/CAEQARgBIAEoATABQAGAAQGYAQGgAQH4AQU/hebcal.ics"
        
    def _parse_ics_event(self, component, feed_identifier: str = "") -> Optional[Dict]:
        """Parse individual Jewish holiday event component"""
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
            
            # Handle all-day events (Jewish holidays are typically all-day)
            if isinstance(start_dt, date) and not isinstance(start_dt, datetime):
                # All-day event
                start_date = start_dt
                start_time = '00:00:00'
                end_time = '00:00:00'
                duration = 0
                is_all_day = True
            else:
                # Timed event (unlikely for Jewish holidays)
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
            
            # Determine location (Jewish holidays are typically observed at home/synagogue)
            location = self._get_event_location(summary)
            
            # Determine category based on holiday type
            category = self._categorize_event(summary)
            
            return {
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
            print(f"Error parsing Jewish holiday event: {e}")
            return None
    
    def _get_event_location(self, event_name: str, feed_identifier: str = "") -> str:
        """Determine appropriate location for Jewish holidays"""
        holiday_lower = event_name.lower()
        
        if any(word in holiday_lower for word in ['shabbat', 'sabbath']):
            return 'Home/Synagogue'
        elif any(word in holiday_lower for word in ['chanukah', 'hanukkah', 'purim', 'passover', 'pesach']):
            return 'Home'
        elif any(word in holiday_lower for word in ['rosh hashanah', 'yom kippur', 'sukkot']):
            return 'Synagogue'
        elif any(word in holiday_lower for word in ['fast', 'taanit']):
            return 'Home'
        else:
            return 'Home/Synagogue'
    
    def _categorize_event(self, event_name: str) -> str:
        """Categorize Jewish holidays based on their names"""
        holiday_lower = event_name.lower()
        
        if any(word in holiday_lower for word in ['shabbat', 'sabbath']):
            return 'Weekly Observance'
        elif any(word in holiday_lower for word in ['rosh hashanah', 'yom kippur', 'passover', 'pesach', 'sukkot', 'shavuot']):
            return 'Major Holiday'
        elif any(word in holiday_lower for word in ['chanukah', 'hanukkah', 'purim', 'tu bishvat']):
            return 'Minor Holiday'
        elif any(word in holiday_lower for word in ['fast', 'taanit']):
            return 'Fast Day'
        elif any(word in holiday_lower for word in ['rosh chodesh']):
            return 'New Month'
        else:
            return 'Jewish Observance'
    
    def _create_sample_events(self, year: int, feed_identifier: str = "") -> List[Dict]:
        """Create sample Jewish holiday events based on known calendar"""
        print("Creating sample Jewish holiday events based on known calendar...")
        
        sample_events = [
            {
                'date': f'{year}-01-01',
                'name': '🕎8️⃣ Chanukah: 8 Candles',
                'description': 'Hanukkah, the Jewish festival of rededication. Also known as the Festival of Lights',
                'start_time': '00:00:00',
                'end_time': '00:00:00',
                'duration': 0,
                'is_all_day': True,
                'location': 'Home',
                'category': 'Minor Holiday'
            },
            {
                'date': f'{year}-01-10',
                'name': '✡️ Asara B\'Tevet',
                'description': 'Fast commemorating the siege of Jerusalem',
                'start_time': '00:00:00',
                'end_time': '00:00:00',
                'duration': 0,
                'is_all_day': True,
                'location': 'Home',
                'category': 'Fast Day'
            },
            {
                'date': f'{year}-02-13',
                'name': '🌳 Tu BiShvat',
                'description': 'New Year for Trees. Tu BiShvat is one of four "New Years" mentioned in the Mishnah',
                'start_time': '00:00:00',
                'end_time': '00:00:00',
                'duration': 0,
                'is_all_day': True,
                'location': 'Home',
                'category': 'Minor Holiday'
            }
        ]
        
        return sample_events
    
    def convert_to_planner_format(self, events: List[Dict], prefix: str = "") -> pd.DataFrame:
        """Convert parsed Jewish holidays to weekly planner CSV format"""
        planner_events = []
        
        for event in events:
            try:
                # Parse date
                event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                
                # Get start time and duration
                start_time = event['start_time']
                duration = event['duration']
                
                # Determine frequency and days
                if event['category'] == 'Weekly Observance':
                    frequency = 'weekly'
                    days_of_week = '["friday", "saturday"]'  # Shabbat
                else:
                    frequency = 'one-time'
                    days_of_week = '["' + event_date.strftime('%A').lower() + '"]'
                
                # Create planner event
                planner_event = {
                    'kid_name': 'All',  # Jewish holidays affect all family members
                    'activity': f"Jewish: {event['name']}",  # Include Jewish prefix
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
                print(f"Error converting Jewish holiday {event}: {e}")
                continue
        
        return pd.DataFrame(planner_events)

def main():
    """Main function to run the Jewish holidays scraper"""
    scraper = JewishHolidaysScraper()
    
    # Download and parse Jewish holidays
    print("="*60)
    print("JEWISH HOLIDAYS SCRAPER")
    print("="*60)
    print("Scraping Jewish holidays from Hebcal...")
    
    # Use the base class method to scrape and convert
    planner_df = scraper.scrape_and_convert(
        url=scraper.hebcal_url,
        output_filename='jewish_holidays.csv',
        prefix='Jewish'
    )
    
    if not planner_df.empty:
        # Ask user if they want to merge with existing CSV
        print("\n" + "="*50)
        print("SCRAPING COMPLETE")
        print("="*50)
        print(f"Successfully processed Jewish holidays from Hebcal")
        print(f"Converted to {len(planner_df)} planner activities")
        print("\nOptions:")
        print("1. Merge with existing activities.csv")
        print("2. Save as separate jewish_holidays.csv only")
        print("3. View parsed Jewish holidays")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            scraper.merge_with_existing_csv(planner_df)
        elif choice == '3':
            print("\nParsed Jewish Holidays:")
            print(planner_df.to_string(index=False))
    else:
        print("Failed to process Jewish holidays from Hebcal")

if __name__ == "__main__":
    main()
