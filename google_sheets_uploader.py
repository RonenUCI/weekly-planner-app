#!/usr/bin/env python3
"""Upload merged calendar CSV data to a Google Sheets tab."""

from __future__ import annotations

import json
import os
from typing import Optional

import pandas as pd

from config import DATA_CONFIG


def _credentials_path() -> str:
    return DATA_CONFIG.get("google_credentials_file", "google_credentials.json")


def upload_merged_calendars(df: pd.DataFrame, tab_name: Optional[str] = None) -> Optional[str]:
    """
    Replace the Calendars tab with merged calendar rows.

    Returns the worksheet gid on success, or None if upload was skipped/failed.
    Requires google_credentials.json (service account) shared on the spreadsheet.
    """
    creds_file = _credentials_path()
    if not os.path.exists(creds_file):
        print(f"   ⚠ Google upload skipped: {creds_file} not found")
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("   ⚠ Google upload skipped: install gspread and google-auth (see scraper_requirements.txt)")
        return None

    tab_name = tab_name or DATA_CONFIG.get("merged_calendars_tab_name", "Calendars")
    sheet_id = DATA_CONFIG["google_sheet_id"]

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=max(len(df) + 1, 100), cols=20)

    upload_df = df.copy()
    if "days_of_week" in upload_df.columns:
        upload_df["days_of_week"] = upload_df["days_of_week"].apply(
            lambda x: json.dumps(x) if not isinstance(x, str) else x
        )

    values = [upload_df.columns.tolist()] + upload_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(values, value_input_option="RAW")

    gid = str(worksheet.id)
    print(f"   ✓ Uploaded {len(df)} rows to Google Sheets tab '{tab_name}' (gid={gid})")
    return gid


def upload_merged_calendars_from_file(csv_path: Optional[str] = None) -> Optional[str]:
    csv_path = csv_path or DATA_CONFIG["merged_calendars_file"]
    if not os.path.exists(csv_path):
        print(f"   ⚠ Google upload skipped: {csv_path} not found")
        return None
    df = pd.read_csv(csv_path, keep_default_na=False)
    return upload_merged_calendars(df)
