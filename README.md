# Concert Band Roster Manager

A lightweight Flask web application for managing concert band attendance. Section leaders can easily mark which members will be performing at upcoming concerts, with data synced directly to Google Sheets.

## Features

- Simple section-based interface (no authentication required)
- Real-time sync with Google Sheets
- Mobile-friendly responsive design
- Support for multiple concert dates
- Easy deployment to PythonAnywhere

## Prerequisites

- Python 3.8 or higher
- Google Cloud Project with Sheets API enabled
- Google Service Account credentials

## Google Sheets Setup

### 1. Create Your Spreadsheet

Create a Google Spreadsheet with the following structure:

| Member Name | Section  | Concert Date 1 | Concert Date 2 | ... |
|-------------|----------|----------------|----------------|-----|
| John Smith  | Flute    |                |                |     |
| Jane Doe    | Clarinet |                |                |     |
| Bob Jones   | Trumpet  |                |                |     |

**Important:**
- Column A: Member Name
- Column B: Section
- Columns C+: Concert dates (put the date as the column header)

### 2. Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name (e.g., "roster-manager")
   - Click "Create and Continue"
   - Skip the optional permissions
   - Click "Done"
5. Create a Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON"
   - Download the file (this is your `service-account-key.json`)
6. Share Your Spreadsheet:
   - Open your Google Spreadsheet
   - Click "Share"
   - Copy the service account email (looks like `something@project-name.iam.gserviceaccount.com`)
   - Paste it and give "Editor" access

## Local Installation

### 1. Clone/Download the Project

```bash
cd isb-roster
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```
SPREADSHEET_ID=your_spreadsheet_id_here
SECRET_KEY=generate_a_random_secret_key
FLASK_ENV=development
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
```

**To get your SPREADSHEET_ID:**
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
- Copy the long string between `/d/` and `/edit`

**To generate a SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Add Service Account Credentials

Place your downloaded `service-account-key.json` file in the project root directory.

### 6. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## PythonAnywhere Deployment

### 1. Create PythonAnywhere Account

Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com/) (free tier works fine)

### 2. Upload Files

Option A - Using Git:
```bash
git clone your-repo-url
cd isb-roster
```

Option B - Manual Upload:
- Use the "Files" tab to upload all project files
- Create directory: `/home/yourusername/isb-roster`

### 3. Set Up Virtual Environment

In PythonAnywhere Bash console:

```bash
cd ~/isb-roster
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file in PythonAnywhere:

```bash
nano .env
```

Add your configuration (same as local setup).

### 5. Upload Service Account Key

Upload your `service-account-key.json` to `/home/yourusername/isb-roster/`

### 6. Configure WSGI

Go to PythonAnywhere "Web" tab:
- Click "Add a new web app"
- Choose "Manual configuration"
- Select Python 3.10 (or latest available)
- Edit the WSGI configuration file:

```python
import sys
import os
from dotenv import load_dotenv

# Add your project directory to path
project_home = '/home/yourusername/isb-roster'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from app import app as application
```

### 7. Set Virtual Environment

In the "Web" tab:
- Set "Virtualenv" path: `/home/yourusername/isb-roster/venv`

### 8. Reload and Test

- Click "Reload" button
- Visit `yourusername.pythonanywhere.com`

## Project Structure

```
isb-roster/
├── app.py                      # Main Flask application
├── sheets_service.py           # Google Sheets API wrapper
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example               # Environment template
├── service-account-key.json   # Google credentials (not in git)
├── templates/
│   ├── index.html             # Section selection page
│   └── roster.html            # Member checklist page
└── static/
    └── style.css              # Styling
```

## Usage

1. Navigate to the application URL
2. Select your section from the home page
3. Check the boxes next to members who will be attending
4. Click "Save Attendance"
5. Changes are immediately written to Google Sheets

## Troubleshooting

### "Error loading sections"
- Check that SPREADSHEET_ID is correct in `.env`
- Verify the spreadsheet is shared with the service account email
- Ensure the service account key file exists

### "No sections found"
- Check that your spreadsheet has data in columns A and B
- Verify column B contains section names

### "Error updating roster"
- Check that the service account has "Editor" access to the spreadsheet
- Verify the date columns exist in the spreadsheet

## Security Notes

- No authentication is used by design (trust-based system)
- Keep your `service-account-key.json` private
- Never commit `.env` or `service-account-key.json` to git
- Consider adding IP restrictions in Google Cloud Console for production

## License

MIT License - feel free to modify for your community band's needs.
