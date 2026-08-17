#!/usr/bin/env python3
"""
Sports Calendar Scraper
Downloads TeamSnap (and similar) ICS feeds and converts them to weekly planner CSV format
"""

import pandas as pd
from ics_calendar_scraper import ICSCalendarScraper
from config import SPORTS_FEEDS


class SportsCalendarScraper(ICSCalendarScraper):
    def __init__(self):
        super().__init__("Sports Calendar")
        self.feeds = SPORTS_FEEDS

    def _enhance_event(self, event: dict, feed_identifier: str = "") -> dict:
        """Flatten TeamSnap multiline locations into a single address."""
        location = str(event.get('location') or '').replace('\n', ', ').replace('\r', ' ')
        event['location'] = ' '.join(location.split())
        return event

    def scrape_all_sports(self) -> pd.DataFrame:
        """Scrape all configured sports feeds and combine them into one DataFrame."""
        all_planner_events = []

        for feed_name, feed_info in self.feeds.items():
            print(f"Scraping {feed_name}...")
            ics_content = self.download_ics_feed(feed_info['url'])
            if not ics_content:
                continue
            events = self.parse_ics_feed(ics_content, feed_name)
            if not events:
                continue
            events_df = self.convert_to_planner_format(
                events,
                prefix='Sports',
                kid_name=feed_info.get('kid_name', 'All'),
            )
            if events_df is not None and not events_df.empty:
                all_planner_events.append(events_df)

        if not all_planner_events:
            return pd.DataFrame()

        combined_df = pd.concat(all_planner_events, ignore_index=True)
        combined_df = combined_df.sort_values('start_date')
        self.save_to_csv(combined_df, 'sports_events.csv')
        print(f"✓ Combined {len(combined_df)} sports events saved to sports_events.csv")
        return combined_df


def main():
    """Main function to run the sports calendar scraper"""
    scraper = SportsCalendarScraper()

    print("=" * 60)
    print("SPORTS CALENDAR SCRAPER")
    print("=" * 60)

    planner_df = scraper.scrape_all_sports()

    if not planner_df.empty:
        print("\n" + "=" * 50)
        print("SCRAPING COMPLETE")
        print("=" * 50)
        print(f"Converted to {len(planner_df)} planner activities")
        print("Saved to sports_events.csv")
    else:
        print("Failed to process sports calendars")


if __name__ == "__main__":
    main()
