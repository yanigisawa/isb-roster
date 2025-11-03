# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask web application for managing concert band attendance. Section leaders select their section and mark member attendance for upcoming concerts. All data syncs to a Google Sheet via the Google Sheets API.

## Development Commands

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (localhost:5000)
python app.py
```

### Environment Setup

Required environment variables in `.env`:
- `SPREADSHEET_ID`: Google Sheets ID (from the URL)
- `SECRET_KEY`: Flask secret key for sessions
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON file
- `FLASK_ENV`: Set to `development` for local dev

## Architecture

### Core Components

**app.py** - Flask application with three main routes:
- `/` - Home page displaying all sections
- `/section/<section_name>` - Roster management for specific section
- `/update` - POST endpoint to save attendance updates

**sheets_service.py** - Google Sheets API wrapper (SheetsService class):
- Reads member data and concert dates from Google Sheets
- Writes attendance updates back to specific cells
- Handles section mapping (maps section names to sheet instrument categories)

### Google Sheets Integration

The application expects a specific spreadsheet structure:
- **Column A (index 0)**: Section/Instrument
- **Column B (index 1)**: Member Name
- **Column E (index 4)**: Email Address
- **Columns J+ (index 9+)**: Concert dates (format: "Mon Day" like "Nov 15")

**Important Constants in sheets_service.py:19-23**:
```python
SECTION_COLUMN = 0
NAME_COLUMN = 1
EMAIL_COLUMN = 4
DATE_COLUMN_START = 9
FIRST_DATA_ROW = 1  # Row 2 in the sheet (0-indexed)
```

### Section Mapping

`SECTION_MAP` (sheets_service.py:26-37) defines which instrument types belong to each section. For example:
- "Clarinet" section includes: "Clarinet", "Clarinet, Bass", "Clarinet, Contra"
- "Double Reeds" includes: "Oboe", "Oboe/English Horn", "Bassoon"

This allows grouping multiple instrument variations under a single section leader.

### Date Handling Logic

The application filters concert dates to show only future dates:
- Uses `dateparser` library to parse "Mon Day" format dates
- `concert_is_next_year()` handles year boundary logic (concerts after June are assumed to roll into next year if month is before June)
- Only dates > today are displayed

### Data Flow

1. User selects section on home page → redirects to `/section/<name>`
2. `get_all_members_for_section()` fetches all members matching that section from the sheet
3. User checks/unchecks members and submits form
4. Form POST to `/update` with member checkboxes and concert date column index
5. `update_attendance()` batch-updates cells in Google Sheets (writes "X" for checked, "" for unchecked)

### Authentication

No user authentication is implemented - this is a trust-based system. Section leaders access their section's roster directly. The only security is the Google service account credentials.

## Deployment Notes

### PythonAnywhere WSGI Configuration

When deploying to PythonAnywhere, the WSGI file must:
1. Load environment variables from `.env` using `python-dotenv`
2. Add project directory to `sys.path`
3. Import the Flask app as `application`

See README.md:172-187 for complete WSGI template.

### Google Service Account Setup

The application requires a Google Cloud service account with:
- Google Sheets API enabled
- JSON key file downloaded to project root
- Service account email given "Editor" access to the target spreadsheet

The `service-account-key.json` file should never be committed to version control.
