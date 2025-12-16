import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import onedrive_utils



app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'  # TODO: Change this to a random value in production

@app.route('/', methods=['GET', 'POST'])
def concent_form():
    if request.method == 'POST':
        # In a real scenario, you might want to log that consent was given here
        session['consent'] = True
        return redirect(url_for('survey'))
    return render_template("consent.html")

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if not session.get('consent'):
        return redirect(url_for('concent_form'))
    
    if request.method == 'POST':
        # Collect form data
        session['survey_data'] = {
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'income': request.form.get('income'),
            'education': request.form.get('education')
        }
        return redirect(url_for('fingerprint'))

    return render_template("survey.html")

import os
import json
import uuid
from datetime import datetime

# ... imports ...

@app.route('/fingerprint', methods=['GET', 'POST'])
def fingerprint():
    if not session.get('consent'):
        return redirect(url_for('concent_form'))
    
    if request.method == 'POST':
        # Get JSON data from the fetch request
        fingerprint_data = request.json
        
        # Combine with survey data
        full_data = {
            'session_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'survey_response': session.get('survey_data', {}),
            'fingerprint': fingerprint_data
        }
        
        # Ensure data directory exists
        data_dir = os.path.join(app.root_path, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Save to file
        filename = f"participant_{full_data['session_id']}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(full_data, f, indent=4)
            
        # Upload to OneDrive
        # We upload the JSON string content
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
    return render_template("thankyou.html")

# main driver function
if __name__ == '__main__':
    app.run(debug=True)