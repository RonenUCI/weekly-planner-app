#!/usr/bin/env python3
"""
Jewish Holidays Scraper
Downloads Jewish holidays and observances from Hebcal ICS feed and converts them to weekly planner CSV format
"""

from datetime import datetime, date, timedelta
from ics_calendar_scraper import ICSCalendarScraper

class JewishHolidaysScraper(ICSCalendarScraper):
    def __init__(self):
        super().__init__("Jewish Holidays")
        self.hebcal_url = "https://download.hebcal.com/v4/CAEQARgBIAEoATABQAGAAQGYAQGgAQH4AQU/hebcal.ics"
    
    def _get_max_date(self, current_date):
        """Jewish holidays limited to 18 months from current date"""
        return current_date + timedelta(days=18*30)  # Approximately 18 months

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
        print("\n" + "="*50)
        print("SCRAPING COMPLETE")
        print("="*50)
        print(f"Successfully processed Jewish holidays from Hebcal")
        print(f"Converted to {len(planner_df)} planner activities")
        print(f"Saved to jewish_holidays.csv")
    else:
        print("Failed to process Jewish holidays from Hebcal")

if __name__ == "__main__":
    main()
