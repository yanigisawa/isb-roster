"""
Concert Band Roster Manager - Flask Application
"""
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from sheets_service import SheetsService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize Google Sheets service
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')

# Global sheets service instance
sheets_service = None


def get_sheets_service():
    """Get or create the sheets service instance."""
    global sheets_service
    if sheets_service is None:
        if not SPREADSHEET_ID:
            raise ValueError("SPREADSHEET_ID not configured")
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_PATH}")
        sheets_service = SheetsService(SPREADSHEET_ID, CREDENTIALS_PATH)
    return sheets_service


@app.route('/')
def index():
    """Home page - display all sections."""
    service = get_sheets_service()
    sections = service.get_all_sections()
    dates = service.get_concert_dates()

    return render_template('index.html', sections=sections, dates=dates)


@app.route('/section/<section_name>')
def section_roster(section_name):
    """Display roster for a specific section."""
    service = get_sheets_service()
    dates = service.get_concert_dates()

    if not dates:
        flash('No concert dates found in the spreadsheet', 'warning')
        return redirect(url_for('index'))

    # Use the first concert date by default
    # In the future, you could allow selecting which date
    concert_date_column_index = request.args.get('date', dates[0]['column_index'])
    print(f"Selected concert date column index: {concert_date_column_index}")

    members = service.get_all_members_for_section(section_name, concert_date_column_index)

    return render_template(
        'roster_form.html',
        section=section_name,
        concert_date=concert_date_column_index,
        all_dates=dates,
        members=members
    )


@app.route('/update', methods=['POST'])
def update_roster():
    """Handle roster updates from section leaders."""
    section = request.form.get('section', "")
    concert_date_column_index = int(request.form.get('concert_date', -1))

    print(f"Updating roster for section: {section}, concert date column index: {concert_date_column_index}")
    # Get all member rows for this section
    service = get_sheets_service()
    members = service.get_all_members_for_section(section, concert_date_column_index)

    # Prepare updates based on form data
    updates = []
    for member in members:
        member_id = f"member_{member['row']}"
        # Checkbox is checked if present in form data
        attending = request.form.get(member_id) == 'true'

        updates.append({
            'row': member['row'],
            'concert_date_column_index': concert_date_column_index,
            'attending': attending
        })

    # Apply updates
    success = service.update_attendance(updates)

    if success:
        flash(f'Roster updated successfully for {section}!', 'success')
    else:
        flash('Error updating roster', 'error')

    # Redirect back to the section roster
    return redirect(
        url_for('section_roster', section_name=section)
    )


@app.route('/roster')
def roster():
    """Display roster for all sections for a selected date."""
    service = get_sheets_service()
    dates = service.get_concert_dates()

    if not dates:
        flash('No concert dates found in the spreadsheet', 'warning')
        return redirect(url_for('index'))

    return render_template(
        'roster_view.html',
        dates=dates
    )


@app.route('/api/roster/<int:date_column_index>')
def api_get_roster(date_column_index):
    """API endpoint to get roster data for all sections for a specific date."""
    service = get_sheets_service()
    roster_data = service.get_all_members_with_attendance(date_column_index)

    return {
        'success': True,
        'data': roster_data
    }


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
