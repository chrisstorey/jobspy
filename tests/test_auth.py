import unittest
import sys
import os
import sqlite3
import datetime
import secrets # For creating tokens if needed, though app should do it

# Add the parent directory to the Python path to allow sibling directory imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app, init_db, and get_db_connection from your Flask app (app.py)
from app import app, init_db, get_db_connection as app_get_db_connection
from models.models import User # User model for type hinting or comparison if needed
from flask import url_for

# Store original DATABASE_FILE setting
ORIGINAL_DATABASE_FILE = os.getenv("DATABASE_FILE")
ORIGINAL_MAIL_SERVER = app.config.get('MAIL_SERVER') # Store original mail server

class AuthTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up for all tests in this class."""
        # Override DATABASE_FILE for testing to use an in-memory database
        os.environ["DATABASE_FILE"] = ":memory:"
        app.config['DATABASE_FILE'] = ":memory:"
        # Disable actual email sending during tests
        app.config['MAIL_SUPPRESS_SEND'] = True # Flask-Mail built-in way to suppress sending
        app.config['TESTING'] = True # General testing flag

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class."""
        # Restore original DATABASE_FILE setting
        if ORIGINAL_DATABASE_FILE is None:
            if "DATABASE_FILE" in os.environ: # Check if it was set during tests
                 del os.environ["DATABASE_FILE"]
        else:
            os.environ["DATABASE_FILE"] = ORIGINAL_DATABASE_FILE
        app.config['DATABASE_FILE'] = ORIGINAL_DATABASE_FILE
        app.config['MAIL_SUPPRESS_SEND'] = False # Restore email sending
        app.config['TESTING'] = False


    def setUp(self):
        """Set up test client and initialize database for each test."""
        self.flask_app = app
        self.flask_app.config['SECRET_KEY'] = 'test_secret_key_auth'
        self.flask_app.config['WTF_CSRF_ENABLED'] = False
        self.flask_app.config['SERVER_NAME'] = 'localhost.test' # For url_for
        self.flask_app.config['APPLICATION_ROOT'] = '/'
        self.flask_app.config['PREFERRED_URL_SCHEME'] = 'http'
        
        self.app = self.flask_app.test_client()
        
        # Initialize a fresh database schema for each test
        # and get a direct db connection for test-specific setup/assertions
        with self.flask_app.app_context():
            init_db() 
            # self.db_conn = app_get_db_connection() # Not strictly needed if query_db opens/closes its own

        # It's necessary to have an app context for url_for
        self.context = self.flask_app.app_context()
        self.context.push()

    def tearDown(self):
        """Clean up after each test."""
        # if self.db_conn: # Not strictly needed if query_db opens/closes its own
        #     self.db_conn.close()
        self.context.pop()

    # Helper method to query DB more easily in tests
    def query_db(self, query, args=(), one=False):
        # This helper uses its own connection per query for simplicity in tests
        # Ensure it uses the :memory: database configured for tests
        current_db_path = self.flask_app.config['DATABASE_FILE']
        if current_db_path != ":memory:":
             #This is a safeguard, os.environ should make app_get_db_connection use :memory:
             #If app_get_db_connection hardcodes path or doesn't re-evaluate os.getenv, this won't work.
             #For this app, app_get_db_connection() calls os.getenv each time.
            pass

        db_conn = app_get_db_connection() 
        cur = db_conn.execute(query, args)
        rv = cur.fetchall()
        db_conn.close() # Close connection after query
        return (rv[0] if rv else None) if one else rv


    def test_successful_registration_and_token_generation(self):
        """Test successful user registration and email validation token generation."""
        test_username = "testuser_db"
        test_email = "test_db@example.com"
        
        response = self.app.post('/register', data=dict(
            username=test_username,
            password="password123",
            first_name="TestDB",
            surname="UserDB",
            email=test_email,
            mobile_number="01234567890",
            postcode="DB1 1ST"
        ), follow_redirects=False)

        self.assertEqual(response.status_code, 302, "Registration should redirect.")
        self.assertTrue(response.location.endswith(url_for('login', _external=False)), 
                        f"Redirect location '{response.location}' did not end with expected '{url_for('login', _external=False)}'")

        # Verify user in database
        user_from_db = self.query_db("SELECT * FROM users WHERE username = ?", [test_username], one=True)
        self.assertIsNotNone(user_from_db, "User not found in database after registration.")
        self.assertEqual(user_from_db['email'], test_email)
        self.assertEqual(user_from_db['first_name'], "TestDB")
        
        # Test email validation token generation (integrated)
        self.assertFalse(bool(user_from_db['email_validated']), "Email should not be validated yet.")
        self.assertIsNotNone(user_from_db['validation_token'], "Validation token was not generated.")
        self.assertTrue(len(user_from_db['validation_token']) > 10, "Validation token seems too short.")
        self.assertIsNotNone(user_from_db['token_expiry'], "Token expiry was not set.")
        
        token_expiry_dt = datetime.datetime.fromisoformat(user_from_db['token_expiry'])
        self.assertTrue(token_expiry_dt > datetime.datetime.utcnow(), "Token expiry should be in the future.")

        # Attempt flash message testing
        with self.app.session_transaction() as session:
            flashed_messages = session.get('_flashed_messages', [])
            expected_message = "Registration successful! Please check your email to validate your account before logging in."
            self.assertTrue(
                any(msg_tuple[1] == expected_message for msg_tuple in flashed_messages),
                f"Flash message '{expected_message}' not found in session. Found: {flashed_messages}"
            )

    def test_registration_missing_fields(self):
        """Test registration with missing required fields."""
        response = self.app.post('/register', data=dict(
            username="testuser_missing_db",
            password="password123",
        ), follow_redirects=False)

        self.assertEqual(response.status_code, 200, "Should stay on registration page with status 200.")
        users_in_db = self.query_db("SELECT * FROM users WHERE username = ?", ["testuser_missing_db"])
        self.assertEqual(len(users_in_db), 0, "No user should be added to DB if fields are missing.")
        self.assertIn(b"All mandatory fields are required.", response.data, "Flash message for missing fields not found.")

    def test_registration_username_exists(self):
        """Test registration with an already existing username."""
        existing_username = "existinguser_db"
        self.app.post('/register', data=dict(
            username=existing_username, password="password123", first_name="Existing",
            surname="User", email="existing_db@example.com", mobile_number="01234567890",
            postcode="EX1 1DB"
        ), follow_redirects=True) 

        user_check = self.query_db("SELECT * FROM users WHERE username = ?", [existing_username], one=True)
        self.assertIsNotNone(user_check, "First user registration failed to save to DB.")
        
        initial_user_count = len(self.query_db("SELECT * FROM users"))

        response = self.app.post('/register', data=dict(
            username=existing_username, password="anotherpassword", first_name="Another",
            surname="Person", email="another_db@example.com", mobile_number="09876543210",
            postcode="AN0 7HR"
        ), follow_redirects=False)

        self.assertEqual(response.status_code, 200, "Should stay on registration page.")
        final_user_count = len(self.query_db("SELECT * FROM users"))
        self.assertEqual(final_user_count, initial_user_count, "User count changed after duplicate username registration attempt.")
        self.assertIn(b"Username already exists.", response.data, "Flash message for existing username not found.")

    def test_validate_email_route_success(self):
        """Test successful email validation via the /validate_email/<token> route."""
        username_to_validate = "validate_success_user"
        email_to_validate = "validate_success@example.com"
        self.app.post('/register', data=dict(
            username=username_to_validate, password="password123", first_name="Validate",
            surname="User", email=email_to_validate, mobile_number="0111222333",
            postcode="VS1 1VS"
        ), follow_redirects=True) 

        user_data = self.query_db("SELECT * FROM users WHERE username = ?", [username_to_validate], one=True)
        self.assertIsNotNone(user_data, "User not found after registration for validation test.")
        self.assertFalse(bool(user_data['email_validated']), "Email should be unvalidated initially.")
        validation_token = user_data['validation_token']
        self.assertIsNotNone(validation_token, "Validation token not set in DB.")

        validate_response = self.app.get(f'/validate_email/{validation_token}', follow_redirects=False)
        
        self.assertEqual(validate_response.status_code, 302, "Validation route should redirect.")
        self.assertTrue(validate_response.location.endswith(url_for('login', _external=False)), "Should redirect to login after validation.")

        validated_user_data = self.query_db("SELECT * FROM users WHERE id = ?", [user_data['id']], one=True)
        self.assertTrue(bool(validated_user_data['email_validated']), "Email not validated in DB.")
        self.assertIsNone(validated_user_data['validation_token'], "Validation token not cleared in DB.")
        self.assertIsNone(validated_user_data['token_expiry'], "Token expiry not cleared in DB.")
        
        final_page_response = self.app.get(validate_response.location) 
        self.assertIn(b"Email validated successfully! You can now log in.", final_page_response.data, "Success flash message not found on login page.")

    def test_validate_email_route_invalid_token(self):
        """Test /validate_email/<token> with an invalid token."""
        response = self.app.get('/validate_email/thisisnotavalidtoken123XYZ', follow_redirects=False)
        self.assertEqual(response.status_code, 302, "Invalid token should redirect.")
        self.assertTrue(response.location.endswith(url_for('register', _external=False)), "Should redirect to register for invalid token.")
        
        redirected_response = self.app.get(response.location)
        self.assertIn(b"Invalid validation link.", redirected_response.data, "Flash message for invalid token not found.")

    def test_validate_email_route_expired_token(self):
        """Test /validate_email/<token> with an expired token."""
        username_expired = "expired_token_user_db"
        self.app.post('/register', data=dict(
            username=username_expired, password="password123", first_name="ExpiredDB",
            surname="TokenDB", email="expired_db@example.com", mobile_number="0222333444",
            postcode="EX2 2DB"
        ), follow_redirects=True)

        user_data_before_expiry_update = self.query_db("SELECT * FROM users WHERE username = ?", [username_expired], one=True)
        self.assertIsNotNone(user_data_before_expiry_update, "User not found for expiry test setup.")
        validation_token = user_data_before_expiry_update['validation_token']
        self.assertIsNotNone(validation_token, "Validation token not set for expiry test setup.")

        past_datetime_iso = (datetime.datetime.utcnow() - datetime.timedelta(hours=48)).isoformat()
        
        db_conn_update = app_get_db_connection()
        try:
            db_conn_update.execute("UPDATE users SET token_expiry = ? WHERE username = ?", 
                                   [past_datetime_iso, username_expired])
            db_conn_update.commit()
        finally:
            db_conn_update.close()

        response = self.app.get(f'/validate_email/{validation_token}', follow_redirects=False)
        
        self.assertEqual(response.status_code, 302, "Expired token should redirect.")
        self.assertTrue(response.location.endswith(url_for('register', _external=False)), "Should redirect to register for expired token.")
        
        redirected_response = self.app.get(response.location) 
        self.assertIn(b"Validation link has expired.", redirected_response.data, "Flash message for expired token not found.")

        user_data_after = self.query_db("SELECT * FROM users WHERE username = ?", [username_expired], one=True)
        self.assertFalse(bool(user_data_after['email_validated']), "Email should still be unvalidated after expired token attempt.")

if __name__ == '__main__':
    unittest.main()
