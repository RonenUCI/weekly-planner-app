#!/usr/bin/env python3
"""
Unified Calendar Scraper
Downloads and combines calendar events from multiple sources:
- School ICS feeds (JLS, Ohlone)
- Jewish holidays from Hebcal
- Converts all to weekly planner CSV format
"""

import pandas as pd
from typing import List, Dict
from ics_calendar_scraper import ICSCalendarScraper
from kid_school_scraper import SchoolCalendarScraper
from jewish_holidays_scraper import JewishHolidaysScraper

class UnifiedCalendarScraper:
    """Unified scraper that combines multiple calendar sources"""
    
    def __init__(self):
        self.school_scraper = SchoolCalendarScraper()
        self.jewish_scraper = JewishHolidaysScraper()
        
    def scrape_all_calendars(self) -> Dict[str, pd.DataFrame]:
        """Scrape all calendar sources and return DataFrames"""
        results = {}
        
        print("="*70)
        print("UNIFIED CALENDAR SCRAPER")
        print("="*70)
        
        # Scrape school events
        print("\n1. Scraping school calendars...")
        school_events = self.school_scraper.scrape_all_schools()
        if school_events:
            school_df = self.school_scraper.convert_to_planner_format(school_events)
            results['school_events'] = school_df
            print(f"   ✓ School events: {len(school_df)} activities")
        else:
            print("   ✗ No school events found")
        
        # Scrape Jewish holidays
        print("\n2. Scraping Jewish holidays...")
        jewish_df = self.jewish_scraper.scrape_and_convert(
            url=self.jewish_scraper.hebcal_url,
            output_filename='jewish_holidays.csv',
            prefix='Jewish'
        )
        if not jewish_df.empty:
            results['jewish_holidays'] = jewish_df
            print(f"   ✓ Jewish holidays: {len(jewish_df)} activities")
        else:
            print("   ✗ No Jewish holidays found")
        
        return results
    
    def combine_all_events(self, calendar_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Combine all calendar events into a single DataFrame"""
        all_events = []
        
        for source_name, df in calendar_data.items():
            if not df.empty:
                print(f"Adding {len(df)} events from {source_name}")
                all_events.append(df)
        
        if all_events:
            combined_df = pd.concat(all_events, ignore_index=True)
            print(f"\nCombined total: {len(combined_df)} events from all sources")
            return combined_df
        else:
            print("No events to combine")
            return pd.DataFrame()
    
    def save_combined_events(self, combined_df: pd.DataFrame, filename: str = 'all_calendar_events.csv'):
        """Save combined events to CSV"""
        if not combined_df.empty:
            combined_df.to_csv(filename, index=False)
            print(f"Saved combined events to {filename}")
        else:
            print("No events to save")
    
    def merge_with_activities(self, combined_df: pd.DataFrame, activities_file: str = 'activities.csv'):
        """Merge combined calendar events with existing activities"""
        try:
            # Load existing activities
            existing_df = pd.read_csv(activities_file)
            print(f"Loaded existing activities: {len(existing_df)} entries")
            
            # Create a key for duplicate detection
            existing_df['event_key'] = existing_df['activity'] + existing_df['start_date']
            combined_df['event_key'] = combined_df['activity'] + combined_df['start_date']
            
            # Find new events (not in existing CSV)
            existing_keys = set(existing_df['event_key'])
            new_events_filtered = combined_df[~combined_df['event_key'].isin(existing_keys)]
            
            print(f"Found {len(new_events_filtered)} new calendar events to add")
            
            if len(new_events_filtered) > 0:
                # Remove the temporary key column
                new_events_filtered = new_events_filtered.drop('event_key', axis=1)
                existing_df = existing_df.drop('event_key', axis=1)
                
                # Combine dataframes
                final_df = pd.concat([existing_df, new_events_filtered], ignore_index=True)
                
                # Save back to CSV
                final_df.to_csv(activities_file, index=False)
                print(f"Successfully merged {len(new_events_filtered)} new events into {activities_file}")
                print(f"Total activities: {len(final_df)}")
                return final_df
            else:
                print("No new events to add")
                return existing_df
                
        except FileNotFoundError:
            print(f"Existing activities file {activities_file} not found, saving as new file")
            combined_df.to_csv(activities_file, index=False)
            return combined_df
        except Exception as e:
            print(f"Error merging with existing activities: {e}")
            return combined_df

def main():
    """Main function to run the unified calendar scraper"""
    unified_scraper = UnifiedCalendarScraper()
    
    # Scrape all calendars
    calendar_data = unified_scraper.scrape_all_calendars()
    
    if calendar_data:
        # Combine all events
        combined_df = unified_scraper.combine_all_events(calendar_data)
        
        if not combined_df.empty:
            # Save combined events
            unified_scraper.save_combined_events(combined_df, 'all_calendar_events.csv')
            
            # Ask user what to do next
            print("\n" + "="*60)
            print("SCRAPING COMPLETE")
            print("="*60)
            print(f"Successfully processed events from all calendar sources")
            print(f"Total combined events: {len(combined_df)}")
            print("\nOptions:")
            print("1. Merge with existing activities.csv")
            print("2. Save as separate all_calendar_events.csv only")
            print("3. View combined events summary")
            print("4. View events by source")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                final_df = unified_scraper.merge_with_activities(combined_df)
                print(f"Final activities file contains {len(final_df)} total entries")
            elif choice == '3':
                print("\nCombined Events Summary:")
                print(f"Total events: {len(combined_df)}")
                print(f"Date range: {combined_df['start_date'].min()} to {combined_df['start_date'].max()}")
                print(f"Unique activities: {combined_df['activity'].nunique()}")
            elif choice == '4':
                print("\nEvents by Source:")
                for source_name, df in calendar_data.items():
                    print(f"{source_name}: {len(df)} events")
                    if not df.empty:
                        print(f"  Date range: {df['start_date'].min()} to {df['start_date'].max()}")
        else:
            print("No events could be combined from any source")
    else:
        print("No calendar data was scraped from any source")

if __name__ == "__main__":
    main()
