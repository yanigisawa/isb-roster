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
    try:
        service = get_sheets_service()
        sections = service.get_all_sections()
        dates = service.get_concert_dates()

        return render_template('index.html', sections=sections, dates=dates)

    except Exception as e:
        return f"Error loading sections: {str(e)}", 500


@app.route('/section/<section_name>')
def section_roster(section_name):
    """Display roster for a specific section."""
    try:
        service = get_sheets_service()
        dates = service.get_concert_dates()

        if not dates:
            flash('No concert dates found in the spreadsheet', 'warning')
            return redirect(url_for('index'))

        # Use the first concert date by default
        # In the future, you could allow selecting which date
        concert_date = request.args.get('date', dates[0])

        members = service.get_section_members(section_name, concert_date)

        return render_template(
            'roster.html',
            section=section_name,
            concert_date=concert_date,
            all_dates=dates,
            members=members
        )

    except Exception as e:
        flash(f"Error loading roster: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update_roster():
    """Handle roster updates from section leaders."""
    try:
        section = request.form.get('section')
        concert_date = request.form.get('concert_date')

        # Get all member rows for this section
        service = get_sheets_service()
        members = service.get_section_members(section, concert_date)

        # Prepare updates based on form data
        updates = []
        for member in members:
            member_id = f"member_{member['row']}"
            # Checkbox is checked if present in form data
            attending = member_id in request.form

            updates.append({
                'row': member['row'],
                'concert_date': concert_date,
                'attending': attending
            })

        # Apply updates
        success = service.update_attendance(updates)

        if success:
            flash(f'Roster updated successfully for {section}!', 'success')
        else:
            flash('Error updating roster', 'error')

        # Redirect back to the section roster
        return redirect(url_for('section_roster', section_name=section, date=concert_date))

    except Exception as e:
        flash(f"Error updating roster: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
