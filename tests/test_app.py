import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from flask import session

# Add parent directory to path so we can import 'app'
# Also add 'app' directory so 'import onedrive_utils' inside __main__ works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app.__main__ import app

class TestResearchApp(unittest.TestCase):

    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier testing if used
        self.client = app.test_client()
    
    def test_home_page(self):
        """Test the home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'University of Exeter', response.data)

    def test_survey_access_without_consent(self):
        """Test that accessing /survey without consent redirects to home."""
        response = self.client.get('/survey')
        self.assertEqual(response.status_code, 302)
        # Check redirect location ends with root /
        # Note: headers['Location'] is a full URL usually
        self.assertTrue(response.headers['Location'].endswith('/'))

    def test_consent_flow(self):
        """Test submitting the consent form redirects to survey."""
        with self.client:
            response = self.client.post('/', data={'consent_check': 'on'})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers['Location'].endswith('/survey'))
            self.assertTrue(session['consent'])

    def test_survey_submission(self):
        """Test submitting the survey stores data and redirects to fingerprint."""
        with self.client.session_transaction() as sess:
            sess['consent'] = True

        with self.client:
            data = {
                'age': '18-24',
                'gender': 'Male',
                'income': 'Less than £15,000',
                'education': 'Bachelor\'s Degree'
            }
            response = self.client.post('/survey', data=data)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.headers['Location'].endswith('/fingerprint'))
            self.assertEqual(session['survey_data']['age'], '18-24')

    @patch('onedrive_utils.upload_file')
    def test_fingerprint_submission_success(self, mock_upload):
        """Test submitting fingerprint data correctly calls upload and returns success."""
        # Setup session
        with self.client.session_transaction() as sess:
            sess['consent'] = True
            sess['survey_data'] = {'age': '18-24'}

        # Mock the upload function to return True (Success)
        mock_upload.return_value = True

        fingerprint_data = {
            'visitorId': 'test_visitor',
            'components': {'os': 'Windows'}
        }

        response = self.client.post('/fingerprint', json=fingerprint_data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'status': 'success'})
        
        # Verify upload was called
        mock_upload.assert_called_once()
        # Verify the filename argument starts with 'data_'
        args, _ = mock_upload.call_args
        self.assertTrue(args[1].startswith('data_'))

    @patch('onedrive_utils.upload_file')
    def test_fingerprint_submission_failure(self, mock_upload):
        """Test that even if upload fails, we still return success to the frontend (as per current logic)."""
        # Note: The current app logic prints error but returns 200 success to let user proceed.
        # This test ensures no crash occurs.
        
        with self.client.session_transaction() as sess:
            sess['consent'] = True

        mock_upload.return_value = False # Simulate failure

        fingerprint_data = {'visitorId': 'test'}
        response = self.client.post('/fingerprint', json=fingerprint_data)
        
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
