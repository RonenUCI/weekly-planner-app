#!/usr/bin/env python3
"""
Unified Calendar Scraper
Downloads and saves calendar events from multiple sources to separate CSV files:
- School ICS feeds (JLS, Ohlone) -> school_events.csv
- Jewish holidays from Hebcal -> jewish_holidays.csv
- Converts all to weekly planner CSV format
"""

import pandas as pd
from typing import List, Dict
from ics_calendar_scraper import ICSCalendarScraper
from kid_school_scraper import SchoolCalendarScraper
from jewish_holidays_scraper import JewishHolidaysScraper

class UnifiedCalendarScraper:
    """Unified scraper that downloads and saves multiple calendar sources to separate files"""
    
    def __init__(self):
        self.school_scraper = SchoolCalendarScraper()
        self.jewish_scraper = JewishHolidaysScraper()
        
    def scrape_all_calendars(self) -> Dict[str, pd.DataFrame]:
        """Scrape all calendar sources and save to separate CSV files"""
        results = {}
        
        print("="*70)
        print("UNIFIED CALENDAR SCRAPER")
        print("="*70)
        
        # Scrape school events and save to school_events.csv
        print("\n1. Scraping school calendars...")
        school_events = self.school_scraper.scrape_all_schools()
        if school_events:
            school_df = self.school_scraper.convert_to_planner_format(school_events)
            if not school_df.empty:
                # Always save to school_events.csv
                self.school_scraper.save_to_csv(school_df, 'school_events.csv')
                results['school_events'] = school_df
                print(f"   ✓ School events: {len(school_df)} activities saved to school_events.csv")
            else:
                print("   ✗ No school events could be converted to planner format")
        else:
            print("   ✗ No school events found")
        
        # Scrape Jewish holidays and save to jewish_holidays.csv
        print("\n2. Scraping Jewish holidays...")
        jewish_df = self.jewish_scraper.scrape_and_convert(
            url=self.jewish_scraper.hebcal_url,
            output_filename='jewish_holidays.csv',
            prefix='Jewish'
        )
        if not jewish_df.empty:
            results['jewish_holidays'] = jewish_df
            print(f"   ✓ Jewish holidays: {len(jewish_df)} activities saved to jewish_holidays.csv")
        else:
            print("   ✗ No Jewish holidays found")
        
        return results
    
    def get_summary(self, calendar_data: Dict[str, pd.DataFrame]) -> str:
        """Get a summary of all scraped calendar data"""
        summary_lines = []
        summary_lines.append("\n" + "="*60)
        summary_lines.append("SCRAPING COMPLETE")
        summary_lines.append("="*60)
        
        total_events = 0
        for source_name, df in calendar_data.items():
            if not df.empty:
                event_count = len(df)
                total_events += event_count
                summary_lines.append(f"{source_name}: {event_count} events")
                
                # Show date range if available
                if 'start_date' in df.columns:
                    try:
                        min_date = df['start_date'].min()
                        max_date = df['start_date'].max()
                        summary_lines.append(f"  Date range: {min_date} to {max_date}")
                    except:
                        pass
        
        summary_lines.append(f"\nTotal events across all sources: {total_events}")
        summary_lines.append("\nFiles created/updated:")
        summary_lines.append("- school_events.csv (school calendar events)")
        summary_lines.append("- jewish_holidays.csv (Jewish holidays)")
        summary_lines.append("- activities.csv (family activities - unchanged)")
        
        return "\n".join(summary_lines)

def main():
    """Main function to run the unified calendar scraper"""
    unified_scraper = UnifiedCalendarScraper()
    
    # Scrape all calendars and save to separate files
    calendar_data = unified_scraper.scrape_all_calendars()
    
    if calendar_data:
        # Display summary
        summary = unified_scraper.get_summary(calendar_data)
        print(summary)
    else:
        print("No calendar data was scraped from any source")

if __name__ == "__main__":
    main()
