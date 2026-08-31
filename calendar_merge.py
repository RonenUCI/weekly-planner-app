#!/usr/bin/env python3
"""Merge scraped calendar DataFrames into a single planner CSV."""

import json
from typing import Dict

import pandas as pd

from config import REQUIRED_COLUMNS


def normalize_calendar_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure calendar_source and required columns exist."""
    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ['calendar_source'])

    normalized = df.copy()
    for col in REQUIRED_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = None
    if 'calendar_source' not in normalized.columns:
        normalized['calendar_source'] = None
    return normalized


def merge_calendar_dataframes(calendar_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine school, jewish, sports (and optional other) frames into one DataFrame."""
    frames = []
    for source_name, df in calendar_data.items():
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            continue
        frame = normalize_calendar_df(df)
        if frame['calendar_source'].isna().all() or (frame['calendar_source'] == '').all():
            default_source = {
                'school_events': 'School',
                'jewish_holidays': 'Jewish',
                'sports_events': 'Sports',
            }.get(source_name, source_name.replace('_', ' ').title())
            frame['calendar_source'] = default_source
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ['calendar_source'])

    merged = pd.concat(frames, ignore_index=True)
    if 'start_date' in merged.columns:
        merged = merged.sort_values('start_date', na_position='last')
    return merged.reset_index(drop=True)


def save_merged_calendars(df: pd.DataFrame, filename: str) -> None:
    """Save merged calendars to CSV with the same escaping rules as other scrapers."""
    df_copy = df.copy()
    if 'days_of_week' in df_copy.columns:
        df_copy['days_of_week'] = df_copy['days_of_week'].apply(
            lambda x: x if isinstance(x, str) else json.dumps(x)
        )
    if 'address' in df_copy.columns:
        df_copy['address'] = (
            df_copy['address'].astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
        )
    df_copy.to_csv(filename, index=False, quoting=0)
