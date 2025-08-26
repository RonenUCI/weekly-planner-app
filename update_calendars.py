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
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from unified_calendar_scraper import UnifiedCalendarScraper

def main():
    """Main function to update all calendars"""
    print("="*70)
    print("CALENDAR UPDATE AUTOMATION")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize unified scraper
        scraper = UnifiedCalendarScraper()
        
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
