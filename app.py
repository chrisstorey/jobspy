import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash # flash and others might be needed by remaining routes or future ones
from flask_cors import CORS

# PonyORM imports
from models.models import db as pony_db, User, Job, SavedJob, JobApplication
import os # Should already be there, but good to ensure

# Import Blueprints and utility functions from new modules
from auth import auth_bp, login_manager
from blog_routes import blog_bp
from jobs import jobs_bp
# from db import init_db # Removed
from email_utils import mail, configure_mail # configure_mail handles mail.init_app(app)
from utils.utils import format_title_case, format_salary # These might be used by other utility functions or directly in templates


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
CORS(app)

# --- PonyORM Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "instance/app.sqlite") # Default to a local sqlite file if not set

# Configure PonyORM
# The provider can be 'sqlite', 'postgres', 'mysql', 'oracle'
# For SQLite, filename is the path to the .sqlite file.
# Ensure the directory for the SQLite file exists if it's not in the root.
# More robust check for SQLite: allows for "sqlite:///path/to/db.sqlite" or just "path/to/db.sqlite"
if "sqlite" in DATABASE_URL or "://" not in DATABASE_URL:
    if ":///" in DATABASE_URL:
        db_path = DATABASE_URL.split(":///")[-1] # Get path if 'sqlite:///' prefix is used
    else:
        db_path = DATABASE_URL # Assumes it's a direct path
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    pony_db.bind(provider='sqlite', filename=db_path, create_db=True)
else:
    # Placeholder for other database providers if needed in the future
    # For PostgreSQL, it would be something like:
    # pony_db.bind(provider='postgres', dsn=DATABASE_URL)
    raise ValueError(f"Unsupported database provider for DATABASE_URL: {DATABASE_URL}. Only SQLite is configured for PonyORM currently.")

pony_db.generate_mapping(create_tables=True) # This creates tables if they don't exist
# --- End PonyORM Database Configuration ---

# Initialize Flask extensions
login_manager.init_app(app)
configure_mail(app) # Initializes Flask-Mail with app context

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(jobs_bp)
app.register_blueprint(blog_bp)


# This function is being kept in app.py for now as per subtask description.
# Example of a route that might remain or be added in app.py
@app.route('/ping')
def ping():
    return "Pong!"

if __name__ == "__main__":
    # init_db() removed, PonyORM handles DB creation via generate_mapping
    app.run(debug=True)
