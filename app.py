import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash # flash and others might be needed by remaining routes or future ones
from flask_cors import CORS

# Import Blueprints and utility functions from new modules
from auth import auth_bp, login_manager
from blog_routes import blog_bp
from jobs import jobs_bp
from db import init_db
from email_utils import mail, configure_mail # configure_mail handles mail.init_app(app)
from utils.utils import format_title_case, format_salary # These might be used by other utility functions or directly in templates


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
CORS(app)

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
    with app.app_context(): # Ensure init_db runs within app context if it needs it
        init_db()
    app.run(debug=True)
