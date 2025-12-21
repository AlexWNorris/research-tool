import os
import json
import uuid
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import onedrive_utils

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'  # TODO: Change this in production


@app.route('/', methods=['GET', 'POST'])
def consent_form():
    """
    Render consent form or handle consent submission.
    """
    if request.method == 'POST':
        session['consent'] = True
        return redirect(url_for('survey'))
    return render_template("consent.html")


@app.route('/survey', methods=['GET', 'POST'])
def survey():
    """
    Render survey form or handle survey submission.
    """
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

    return render_template("survey.html")


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

        session_id = str(uuid.uuid4())
        
        # Combine with survey data
        full_data = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'survey_response': session.get('survey_data', {}),
            'fingerprint': fingerprint_data
        }

        # Upload to OneDrive
        filename = f"data_{session_id}.json"
        
        try:
            json_content = json.dumps(full_data, indent=4)
            if onedrive_utils.upload_file(json_content, filename):
                print(f"Successfully uploaded {filename} to OneDrive")
            else:
                print("OneDrive upload failed.")
        except Exception as e:
            print(f"Error during OneDrive upload: {e}")

        # Optional: Clear session data if no longer needed
        # session.pop('survey_data', None)

        return jsonify({'status': 'success'}), 200

    return render_template("fingerprint.html")


@app.route('/thankyou')
def thankyou():
    """
    Render thank you page.
    """
    return render_template("thankyou.html")


# main driver function
if __name__ == '__main__':
    app.run(debug=True)