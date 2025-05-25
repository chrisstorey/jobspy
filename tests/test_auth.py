import unittest
import sys
import os

# Add the parent directory to the Python path to allow sibling directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, users # app.app is the Flask app instance, app.users is the user dict
from models.models import User
from flask import url_for

class AuthTests(unittest.TestCase):

    def setUp(self):
        """Set up test client and clear users for each test."""
        self.flask_app = app # This is the Flask app object from app.py
        # Configure for testing
        self.flask_app.config['TESTING'] = True
        self.flask_app.config['SECRET_KEY'] = 'test_secret_key' # Consistent secret key for tests
        self.flask_app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for easier form testing if WTForms are used
        
        # Configure server name for url_for to work correctly in tests
        self.flask_app.config['SERVER_NAME'] = 'localhost.test'
        self.flask_app.config['APPLICATION_ROOT'] = '/'
        self.flask_app.config['PREFERRED_URL_SCHEME'] = 'http'
        
        self.app = self.flask_app.test_client()
        users.clear() # Clear the global users dictionary from app.py
        # If a test user is needed for general tests, add it here.
        # For 'username_exists' test, we'll add the user within the test.
        
        # It's necessary to have a request context to use url_for
        self.context = self.flask_app.app_context()
        self.context.push()


    def tearDown(self):
        """Clean up after each test."""
        self.context.pop() # Pop the app context

    def test_successful_registration(self):
        """Test successful user registration."""
        test_username = "testuser"
        test_email = "test@example.com"
        
        initial_user_count = len(users)

        response = self.app.post('/register', data=dict(
            username=test_username,
            password="password123",
            first_name="Test",
            surname="User",
            email=test_email,
            mobile_number="01234567890",
            postcode="TE1 1ST"
        ), follow_redirects=False) # Ensure redirects are NOT followed

        self.assertEqual(response.status_code, 302) # Should redirect
        self.assertEqual(response.location, url_for('login', _external=False)) # Check redirect location
        
        self.assertEqual(len(users), initial_user_count + 1)
        self.assertIn(test_username, users)
        self.assertEqual(users[test_username].email, test_email)
        self.assertFalse(users[test_username].email_validated)

        # Check for flash message in the session context
        with self.app.session_transaction() as session:
            self.assertTrue('_flashed_messages' in session, "Flashed messages key not found in session.")
            flashed_messages = session['_flashed_messages']
            self.assertIsNotNone(flashed_messages, "Flashed messages list is None.")
            self.assertTrue(len(flashed_messages) > 0, "No flashed messages found in session.")
            # Default category for flash() is 'message'
            expected_flash_message = ('message', "Registration successful! Please log in.")
            self.assertIn(expected_flash_message, flashed_messages, 
                          f"Expected flash message {expected_flash_message} not found in {flashed_messages}")


    def test_registration_missing_fields(self):
        """Test registration with missing required fields."""
        initial_user_count = len(users)
        
        response = self.app.post('/register', data=dict(
            username="testuser_missing",
            password="password123",
            # Missing first_name, surname, email, mobile_number, postcode
        ), follow_redirects=False)

        self.assertEqual(response.status_code, 200) # Should stay on the registration page
        self.assertEqual(len(users), initial_user_count) # No new user should be added

        # Check for flash message
        self.assertIn(b"All mandatory fields are required.", response.data)

    def test_registration_username_exists(self):
        """Test registration with an already existing username."""
        # First, register a user successfully
        existing_username = "existinguser"
        self.app.post('/register', data=dict(
            username=existing_username,
            password="password123",
            first_name="Existing",
            surname="User",
            email="existing@example.com",
            mobile_number="01234567890",
            postcode="EX1 1ST"
        ), follow_redirects=True) # Follow redirect to complete this registration

        initial_user_count = len(users)
        self.assertIn(existing_username, users) # Verify the first user was added

        # Then, attempt to register another user with the same username
        response = self.app.post('/register', data=dict(
            username=existing_username, # Same username
            password="anotherpassword",
            first_name="Another",
            surname="Person",
            email="another@example.com",
            mobile_number="09876543210",
            postcode="AN0 7HR"
        ), follow_redirects=False)

        self.assertEqual(response.status_code, 200) # Should stay on the registration page
        self.assertEqual(len(users), initial_user_count) # No new user should be added

        # Check for flash message
        self.assertIn(b"Username already exists.", response.data)

if __name__ == '__main__':
    unittest.main()
