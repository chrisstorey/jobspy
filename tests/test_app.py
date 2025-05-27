from flask import current_app
from pony.orm import db_session # For tests that might interact with DB directly if needed

# Note: Fixtures 'app', 'client', 'db' are expected to be defined in tests/conftest.py

def test_app_exists(app):
    """Test if the Flask app instance exists and is in testing mode."""
    assert app is not None
    assert current_app == app # Check if app context is correctly set up by fixture
    assert app.config['TESTING'] is True
    assert "sqlite:///:memory:" in app.config['DATABASE_URL'] # Check if test DB is used

def test_ping_route(client):
    """Test the /ping route."""
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.data == b'Pong!'

def test_blueprints_registered(app):
    """Test if the main blueprints are registered with the app."""
    # Blueprint names are 'auth', 'jobs', 'blog'
    # The actual names in app.blueprints might have a prefix if registered with one,
    # but the keys in app.blueprints dict are usually the ones given in Blueprint constructor.
    registered_blueprints = app.blueprints.keys()
    assert 'auth' in registered_blueprints
    assert 'jobs' in registered_blueprints
    assert 'blog' in registered_blueprints

# Example of a test that might use the db fixture and db_session
# This is more of a placeholder to show how it would be used.
def test_database_connection(db):
    """Test if the database fixture works and we can enter a db_session."""
    try:
        with db_session:
            # Perform a simple query or check, e.g., count users if User model is imported
            # from models.models import User
            # user_count = db.User.select().count() # Example, assumes User entity
            # assert user_count >= 0 
            pass # Just entering and exiting db_session is a basic test
        assert True
    except Exception as e:
        assert False, f"Database session failed: {e}"
