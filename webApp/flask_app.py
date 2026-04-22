"""
Flask web application serving the data collection endpoints for footprinting 
and survey gathering.
"""
import os
import json
import uuid
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, make_response
from dotenv import load_dotenv

load_dotenv()

# my python files
from emailer import send_email
from encryptor import encrypt_json

app = Flask(__name__)
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError('SECRET_KEY environment variable must be set in production.')
app.config['SECRET_KEY'] = _secret_key


@app.route('/', methods=['GET', 'POST'])
def consent_form():
    """
    Render consent form or handle consent submission.
    """
    if request.cookies.get('survey_completed'):
        return redirect(url_for('thankyou'))

    if request.method == 'POST':
        session['consent'] = True
        return redirect(url_for('survey'))
    return render_template("consent.html", current_step=1, total_steps=4)


@app.route('/survey', methods=['GET', 'POST'])
def survey():
    """
    Render survey form or handle survey submission.
    """
    if request.cookies.get('survey_completed'):
        return redirect(url_for('thankyou'))

    if not session.get('consent'):
        return redirect(url_for('consent_form'))

    if request.method == 'POST':
        # Collect form data
        email = request.form.get('email')
        hashed_email = None
        if email:
             # Normalize and hash
            hashed_email = hashlib.sha256(email.lower().strip().encode('utf-8')).hexdigest()

        session['survey_data'] = {
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'income': request.form.get('income'),
            'education': request.form.get('education'),
            'email': hashed_email
        }
        return redirect(url_for('fingerprint'))

    return render_template("survey.html", current_step=2, total_steps=4)


@app.route('/fingerprint', methods=['GET', 'POST'])
def fingerprint():
    """
    Render fingerprint page or handle fingerprint data submission.
    """
    if not session.get('consent'):
        return redirect(url_for('consent_form'))

    if request.method == 'POST':
        # Get JSON data from the fetch request
        fingerprint_data = request.json
        info_button_clicked = fingerprint_data.pop('infoButtonClicked', False) if fingerprint_data else False

        session_id = str(uuid.uuid4())
        
        # Combine with survey data
        full_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'survey_response': session.get('survey_data', {}),
            'fingerprint': fingerprint_data,
            'info_button_clicked': info_button_clicked
        }

        # Save to local file (code used during testing)
        # filename = f"data_{session_id}.json"
        # data_dir = os.path.join(app.root_path, 'data')
        
        # try:
        #     os.makedirs(data_dir, exist_ok=True)
        #     filepath = os.path.join(data_dir, filename)
            
        #     with open(filepath, 'w') as f:
        #         json.dump(full_data, f, indent=4)
                
        #     print(f"Successfully saved {filename} locally")
        # except Exception as e:
        #     print(f"Error saving data locally: {e}")

        # Encrypt json information ready for email transfer
        email_payload = encrypt_json(full_data) 

        # Send information to shair (via power automate email trigger)
        send_email(email_payload)

        resp = make_response(jsonify({'status': 'success'}))
        # Set cookie to expire in 1 year (365 days = 24 hours * 60 minutes * 60 seconds)
        resp.set_cookie('survey_completed', 'true', max_age=31536000)
        return resp, 200

    return render_template("fingerprint.html", current_step=3, total_steps=4)


@app.route('/thankyou')
def thankyou():
    """
    Render thank you page.
    """
    consent = request.args.get('consent', 'yes')
    return render_template("thankyou.html", consent=consent, current_step=4, total_steps=4)


# main driver function
if __name__ == '__main__':
    app.run(debug=True)