#!/usr/bin/env python3
"""
Test script to verify Jewish holidays integration
"""

import pandas as pd
import json
import os
from datetime import datetime, date

def test_jewish_holidays_integration():
    """Test if Jewish holidays are properly loaded and integrated"""
    
    print("Testing Jewish Holidays Integration")
    print("="*50)
    
    # Check if files exist
    files_to_check = ['activities.csv', 'school_events.csv', 'jewish_holidays.csv']
    
    for filename in files_to_check:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            print(f"✓ {filename}: {len(df)} entries")
            
            # Show sample data
            if len(df) > 0:
                print(f"  Sample: {df.iloc[0]['activity'] if 'activity' in df.columns else 'No activity column'}")
        else:
            print(f"✗ {filename}: File not found")
    
    print("\nTesting combined data loading...")
    
    # Simulate the load_combined_data_for_display function
    try:
        # Load main activities
        activities_df = pd.read_csv('activities.csv')
        print(f"Loaded {len(activities_df)} activities")
        
        # Load school events
        school_events_df = pd.DataFrame()
        if os.path.exists('school_events.csv'):
            school_events_df = pd.read_csv('school_events.csv')
            if 'days_of_week' in school_events_df.columns:
                school_events_df['days_of_week'] = school_events_df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            
            # Convert date columns
            if 'start_date' in school_events_df.columns:
                school_events_df['start_date'] = pd.to_datetime(school_events_df['start_date']).dt.date
            if 'end_date' in school_events_df.columns:
                school_events_df['end_date'] = pd.to_datetime(school_events_df['end_date']).dt.date
            
            print(f"Loaded {len(school_events_df)} school events")
        
        # Load Jewish holidays
        jewish_holidays_df = pd.DataFrame()
        if os.path.exists('jewish_holidays.csv'):
            jewish_holidays_df = pd.read_csv('jewish_holidays.csv')
            if 'days_of_week' in jewish_holidays_df.columns:
                jewish_holidays_df['days_of_week'] = jewish_holidays_df['days_of_week'].apply(
                    lambda x: json.loads(x) if isinstance(x, str) else x
                )
            
            # Convert date columns
            if 'start_date' in jewish_holidays_df.columns:
                jewish_holidays_df['start_date'] = pd.to_datetime(jewish_holidays_df['start_date']).dt.date
            if 'end_date' in jewish_holidays_df.columns:
                jewish_holidays_df['end_date'] = pd.to_datetime(jewish_holidays_df['end_date']).dt.date
            
            print(f"Loaded {len(jewish_holidays_df)} Jewish holidays")
        
        # Combine all dataframes
        all_dataframes = [activities_df]
        total_events = len(activities_df)
        
        if not school_events_df.empty:
            all_dataframes.append(school_events_df)
            total_events += len(school_events_df)
        
        if not jewish_holidays_df.empty:
            all_dataframes.append(jewish_holidays_df)
            total_events += len(jewish_holidays_df)
        
        if len(all_dataframes) > 1:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            print(f"\n✓ SUCCESS: Combined {len(activities_df)} activities + {len(school_events_df)} school events + {len(jewish_holidays_df)} Jewish holidays = {len(combined_df)} total")
            
            # Show some Jewish holidays in the combined data
            jewish_activities = combined_df[combined_df['activity'].str.contains('Jewish:', na=False)]
            if len(jewish_activities) > 0:
                print(f"\nFound {len(jewish_activities)} Jewish holidays in combined data:")
                for i, (_, row) in enumerate(jewish_activities.head(5).iterrows()):
                    print(f"  {i+1}. {row['activity']} on {row['start_date']}")
                if len(jewish_activities) > 5:
                    print(f"  ... and {len(jewish_activities) - 5} more")
            
            return True
        else:
            print("✗ No data to combine")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_jewish_holidays_integration()
    if success:
        print("\n🎉 Jewish holidays integration test PASSED!")
    else:
        print("\n❌ Jewish holidays integration test FAILED!")
