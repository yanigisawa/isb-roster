"""
Google Sheets service for reading and writing roster data.
"""

from typing import List, Dict
from datetime import datetime, date

import dateparser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsService:
    """Handles all Google Sheets API interactions."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    SECTION_COLUMN = 0  # Section is in column A (index 0)
    NAME_COLUMN = 1  # Name is in column B (index 1)
    EMAIL_COLUMN = 3  # Email is in column D (index 3)
    ORDER_COLUMN = 4  # Order is in column E (index 4)
    DATE_COLUMN_START = 9  # Dates start from column J (index 9)
    FIRST_DATA_ROW = 1  # Data starts from row 2 (index 1)
    JUNE = 6

    SECTION_MAP = {
        "Flute": ["Flute, Piccolo", "Flute"],
        "Double Reeds": ["Oboe", "Oboe/English Horn", "Bassoon"],
        "Clarinet": ["Clarinet", "Clarinet, Bass", "Clarinet, Contra"],
        "Saxophone": ["Sax, Alto", "Sax, Tenor", "Sax, Bari"],
        "Trumpet": ["Trumpet"],
        "Horn": ["Horn"],
        "Trombone": ["Trombone"],
        "Euphonium, BC": ["Euphonium, BC"],
        "Tuba": ["Tuba"],
        "Percussion": ["Percussion"],
    }

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
        Get a list of all unique sections from the SECTION_MAP
        dictionary for this class.

        Returns:
            List of unique section names
        """
        return sorted(list(self.SECTION_MAP.keys()))

    def concert_is_next_year(self, parsed_date: date, current_month: int) -> bool:
        """
        Determine if the parsed concert date falls in the next calendar year
        based on the current month.

        Args:
            parsed_date: The parsed date object
            current_month: The current month as an integer

        Returns:
            True if the concert date is in the next calendar year, False otherwise
        """
        return (
            current_month > self.JUNE
            and parsed_date.month < self.JUNE
            and parsed_date.month < current_month
        )

    def get_date_from_string(self, date_str: str) -> date:
        """
        Parse a date string of the format 'Mon Day' (e.g., 'Nov 15')
        into a date object, considering the current year and potential
        next year adjustment.

        Args:
            date_str: The date string to parse

        Returns:
            A date object representing the parsed date
        """
        today = date.today()
        current_year = today.year
        current_month = today.month

        try:
            parsed_date = dateparser.parse(f"{date_str} {current_year}").date()

            # Handle Dates occurring next Calendar year
            if self.concert_is_next_year(parsed_date, current_month):
                parsed_date = dateparser.parse(f"{date_str} {current_year + 1}").date()
        except ValueError:
            return None

        return parsed_date

    def get_concert_dates(self) -> List[str]:
        """
        Get concert dates from the header row.
        Assumes dates start from column J (index 9) onwards.
        Date is of the format 'Mon Day' (e.g., 'Nov 15').

        Returns:
            List of future concert dates
        """
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='1:1'
        ).execute()

        values = result.get('values', [])
        if not values or len(values) < 1:
            return []

        header = values[0]
        dates = [date.strip() for date in header[self.DATE_COLUMN_START:] if date.strip()]

        # Filter out past dates
        today = date.today()
        future_dates = []
        column_count = -1

        for date_str in dates:
            column_count += 1
            parsed_date = self.get_date_from_string(date_str)
            if parsed_date is None:
                continue

            # Only include future dates
            if parsed_date <= today:
                continue
            future_dates.append(
                {
                    "date_str": date_str,
                    "parsed_date": parsed_date,
                    "column_index": self.DATE_COLUMN_START + column_count
                }
            )

        return future_dates

    def _is_in_section(self, section: str, section_name: str) -> bool:
        """
        Check if a given section string matches the standard section name
        using the SECTION_MAP.

        Args:
            section: The section string from the sheet
            section_name: The standard section name to check against
        Returns:
            True if the section matches the section_name, False otherwise
        """
        for alias in self.SECTION_MAP.get(section_name, []):
            if section == alias:
                return True
        return False

    def get_all_members_for_section(self, section_name: str, concert_date_column_index: int) -> List[Dict]:
        """
        Get all members for a specific section name.

        Returns:
            List of Members for the given section name
            [
                {
                    'name': 'John Smith',
                    'row': 2,
                    'email': "john.smith@example.com"
                },
                ...
            ]
        """
        # Get all data
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:Z'  # Get all columns
        ).execute()

        values = result.get('values', [])
        if not values or len(values) < 2:
            return []

        members = []

        for idx, row in enumerate(values[self.FIRST_DATA_ROW:], start=2):
            if len(row) < 2:
                continue
            section = row[self.SECTION_COLUMN].strip()
            name = row[self.NAME_COLUMN].strip() if row else ''

            if not self._is_in_section(section, section_name):
                continue

            members.append({
                'name': name,
                'row': idx,
                'email': row[self.EMAIL_COLUMN].strip() if len(row) > 2 else '',
                'attending': row[concert_date_column_index].strip().lower() in ['yes', 'x', 'true', '1'] if len(row) > concert_date_column_index else False
            })

        return sorted(members, key=lambda x: x['name'])

    def get_section_name_from_alias(self, alias: str) -> str:
        """
        Get the standard section name from an alias.

        Args:
            alias: The alias to look up
        """
        for section_name, aliases in self.SECTION_MAP.items():
            if alias in aliases:
                return section_name
        return None

    def get_all_members_with_attendance(self, concert_date_column_index: int) -> Dict[str, List[Dict]]:
        """
        Get all members grouped by section with their attendance status for a specific date.

        Args:
            concert_date_column_index: The column index of the concert date

        Returns:
            Dictionary with section names as keys and lists of members as values:
            {
                'Flute': [
                    {
                        'name': 'John Smith',
                        'attending': True
                    },
                    ...
                ],
                ...
            }
        """
        # Get all data
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A:Z'  # Get all columns
        ).execute()

        values = result.get('values', [])
        if not values or len(values) < 2:
            return {}

        # Group members by section
        section_members = {sn: [] for sn in self.SECTION_MAP.keys()}

        # Start from row 2 (index 1), row 1 is header
        for row in values[self.FIRST_DATA_ROW:]:
            if len(row) < 2:
                continue

            section = row[self.SECTION_COLUMN].strip()
            name = row[self.NAME_COLUMN].strip() if row else ''

            section_name = self.get_section_name_from_alias(section)
            attending = False
            if len(row) > concert_date_column_index and row[concert_date_column_index]:
                attending = row[concert_date_column_index].strip().lower() in ['yes', 'x', 'true', '1']

            if not attending:
                continue
            section_members[section_name].append({
                'name': name,
                'attending': attending
            })

        # Sort members within each section by name
        for section_name in section_members:
            section_members[section_name] = sorted(
                section_members[section_name],
                key=lambda x: x['name']
            )

        return section_members

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
        data = []
        for update in updates:
            concert_date_column_index = update['concert_date_column_index']
            row = update['row']
            attending = update['attending']

            # Convert column index to letter (A=0, B=1, etc.)
            col_letter = self._col_idx_to_letter(concert_date_column_index)

            # Set value
            value = 'X' if attending else ''

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

    @staticmethod
    def _col_idx_to_letter(idx: int) -> str:
        """Convert column index to letter (0='A', 1='B', etc.)."""
        result = ''
        while idx >= 0:
            result = chr(65 + (idx % 26)) + result
            idx = idx // 26 - 1
        return result
