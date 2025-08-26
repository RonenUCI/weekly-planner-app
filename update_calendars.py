#!/usr/bin/env python3
"""
Calendar Update Automation Script
Run this script to automatically update all calendars:
- School events (weekly updates)
- Jewish holidays (monthly updates)
- Can be run manually or as a cron job
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from ics_calendar_scraper import ICSCalendarScraper
from kid_school_scraper import SchoolCalendarScraper
from jewish_holidays_scraper import JewishHolidaysScraper

class UpdateCalendars:
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
        school_df = self.school_scraper.scrape_all_schools()
        if isinstance(school_df, pd.DataFrame) and not school_df.empty:
            results['school_events'] = school_df
            print(f"   ✓ School events: {len(school_df)} activities saved to school_events.csv")
        else:
            print("   ✗ No school events found")
        
        # Scrape Jewish holidays and save to jewish_holidays.csv
        print("\n2. Scraping Jewish holidays...")
        jewish_df = self.jewish_scraper.scrape_and_convert(
            url=self.jewish_scraper.hebcal_url,
            output_filename='jewish_holidays.csv',
            prefix='Jewish'
        )
        if isinstance(jewish_df, pd.DataFrame) and not jewish_df.empty:
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
    """Main function to update all calendars"""
    print("="*70)
    print("CALENDAR UPDATE AUTOMATION")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize calendar updater
        scraper = UpdateCalendars()
        
        # Scrape all calendars
        calendar_data = scraper.scrape_all_calendars()
        
        if calendar_data:
            # Display summary
            summary = scraper.get_summary(calendar_data)
            print(summary)
            
            # Log successful update
            log_update(True, "All calendars updated successfully")
            print("\n✅ Calendar update completed successfully!")
            return 0
        else:
            print("❌ No calendar data was scraped from any source")
            log_update(False, "No calendar data scraped")
            return 1
            
    except Exception as e:
        error_msg = f"Error updating calendars: {e}"
        print(f"❌ {error_msg}")
        log_update(False, error_msg)
        return 1

def log_update(success: bool, message: str):
    """Log update results to a file"""
    log_file = "calendar_update.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "SUCCESS" if success else "ERROR"
    
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {status}: {message}\n")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
