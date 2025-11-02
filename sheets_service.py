"""
Google Sheets service for reading and writing roster data.
"""
import os
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsService:
    """Handles all Google Sheets API interactions."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id: str, credentials_path: str):
        """
        Initialize the Sheets service.

        Args:
            spreadsheet_id: The ID of the Google Spreadsheet
            credentials_path: Path to the service account JSON key file
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet = self.service.spreadsheets()

    def get_all_sections(self) -> List[str]:
        """
        Get a list of all unique sections from the spreadsheet.
        Assumes the 'Section' column is column B (index 1).

        Returns:
            List of unique section names
        """
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:B'  # Get names and sections
            ).execute()

            values = result.get('values', [])
            if not values or len(values) < 2:  # Need at least header + 1 row
                return []

            # Skip header row, get unique sections from column B
            sections = set()
            for row in values[1:]:
                if len(row) > 1 and row[1]:  # Check if section exists
                    sections.add(row[1].strip())

            return sorted(list(sections))

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_concert_dates(self) -> List[str]:
        """
        Get concert dates from the header row.
        Assumes dates start from column C (index 2) onwards.

        Returns:
            List of concert dates
        """
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='1:1'  # Header row only
            ).execute()

            values = result.get('values', [])
            if not values:
                return []

            # Skip first two columns (Name, Section)
            header = values[0]
            dates = [date.strip() for date in header[2:] if date.strip()]

            return dates

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_section_members(self, section: str, concert_date: str) -> List[Dict]:
        """
        Get all members for a specific section with their attendance status.

        Args:
            section: The section name (e.g., 'Flute', 'Clarinet')
            concert_date: The concert date to check attendance for

        Returns:
            List of dictionaries with member info:
            [
                {
                    'name': 'John Smith',
                    'row': 2,
                    'attending': True
                },
                ...
            ]
        """
        try:
            # Get all data
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='A:Z'  # Get all columns
            ).execute()

            values = result.get('values', [])
            if not values or len(values) < 2:
                return []

            # Find the column index for the concert date
            header = values[0]
            try:
                date_col_idx = header.index(concert_date)
            except ValueError:
                print(f"Concert date '{concert_date}' not found in header")
                return []

            members = []
            # Start from row 2 (index 1), row 1 is header
            for idx, row in enumerate(values[1:], start=2):
                # Check if this row belongs to the requested section
                if len(row) > 1 and row[1].strip() == section:
                    name = row[0].strip() if row else ''
                    # Check attendance status for this concert date
                    attending = False
                    if len(row) > date_col_idx and row[date_col_idx]:
                        attending = row[date_col_idx].strip().lower() in ['yes', 'x', 'true', '1']

                    members.append({
                        'name': name,
                        'row': idx,
                        'attending': attending
                    })

            return members

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def update_attendance(self, updates: List[Dict]) -> bool:
        """
        Update attendance for multiple members.

        Args:
            updates: List of dictionaries with update info:
            [
                {
                    'row': 2,
                    'concert_date': '2025-11-15',
                    'attending': True
                },
                ...
            ]

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get header to find column for concert date
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='1:1'
            ).execute()

            header = result.get('values', [])[0]

            # Prepare batch update
            data = []
            for update in updates:
                concert_date = update['concert_date']
                row = update['row']
                attending = update['attending']

                # Find column for this concert date
                try:
                    col_idx = header.index(concert_date)
                except ValueError:
                    print(f"Concert date '{concert_date}' not found")
                    continue

                # Convert column index to letter (A=0, B=1, etc.)
                col_letter = self._col_idx_to_letter(col_idx)

                # Set value
                value = 'Yes' if attending else ''

                data.append({
                    'range': f'{col_letter}{row}',
                    'values': [[value]]
                })

            if not data:
                return False

            # Execute batch update
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }

            self.sheet.values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()

            return True

        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

    @staticmethod
    def _col_idx_to_letter(idx: int) -> str:
        """Convert column index to letter (0='A', 1='B', etc.)."""
        result = ''
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result
