#!/usr/bin/env python3
"""
Kid School Calendar Scraper
Downloads calendar events from multiple school ICS feeds and converts them to weekly planner CSV format
"""

from datetime import datetime
import pandas as pd
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
    
    def _enhance_event(self, event: dict, school_code: str = "") -> dict:
        """Add school-specific information to the event"""
        if school_code in self.school_feeds:
            event['school'] = school_code
            # Override location with school address
            event['location'] = self.school_feeds[school_code]['address']
        return event
    
    def scrape_all_schools(self) -> pd.DataFrame:
        """Scrape all schools and combine them into one DataFrame"""
        all_events = []
        
        # Use parent class methods to scrape each school
        for school_code, school_info in self.school_feeds.items():
            print(f"Scraping {school_info['name']}...")
            
            # Download and parse the ICS feed directly
            ics_content = self.download_ics_feed(school_info['url'])
            if ics_content:
                school_events = self.parse_ics_feed(ics_content, school_code)
                if school_events:
                    all_events.extend(school_events)
        
        if all_events:
            # Convert all events to planner format
            combined_df = self.convert_to_planner_format(all_events, prefix="School")
            combined_df = combined_df.sort_values('start_date')
            
            # Save combined file
            self.save_to_csv(combined_df, 'school_events.csv')
            print(f"✓ Combined {len(combined_df)} school events saved to school_events.csv")
            return combined_df
        
        return pd.DataFrame()

def main():
    """Main function to run the school calendar scraper"""
    scraper = SchoolCalendarScraper()
    
    # Download and parse school calendars
    print("="*60)
    print("SCHOOL CALENDAR SCRAPER")
    print("="*60)
    print("Scraping school calendars...")
    
    # Use the simplified method
    planner_df = scraper.scrape_all_schools()
    
    if not planner_df.empty:
        print("\n" + "="*50)
        print("SCRAPING COMPLETE")
        print("="*50)
        print(f"Successfully processed school calendars")
        print(f"Converted to {len(planner_df)} planner activities")
        print(f"Saved to school_events.csv")
    else:
        print("Failed to process school calendars")

if __name__ == "__main__":
    main()
