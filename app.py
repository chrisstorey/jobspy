import os
import sqlite3
import secrets # Added
import datetime # Added

import bleach
import markdown

from dotenv import load_dotenv  # type: ignore
from flask import Flask, render_template, request, redirect, url_for, flash  # type: ignore
from flask_cors import CORS
from flask_mail import Mail, Message # Added Message
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import check_password_hash, generate_password_hash

from blog import blog_posts

from models.models import User # Removed users import from models
from utils.utils import format_title_case, format_salary

# Add these utility functions at the top level, after the imports


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change this!
CORS(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'user@example.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')

mail = Mail(app)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    db_path = os.getenv("DATABASE_FILE", "all_jobs.sqlite")
    # The existence check here might be too strict if init_db() is supposed to create it.
    # if not os.path.exists(db_path):
    #     raise FileNotFoundError(
    #         f"Database file '{db_path}' not found. Please ensure it exists or init_db() has been called."
    #     )
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise


def init_db():
    """Initializes the database.

    Creates the `jobs` table if it doesn't already exist.
    The schema for the `jobs` table is as follows:
        - id (TEXT, PRIMARY KEY): Unique identifier for the job.
        - title (TEXT, NOT NULL): The title of the job.
        - location (TEXT): The location of the job.
        - description (TEXT): The detailed description of the job.
        - min_amount (REAL): The minimum salary amount.
        - max_amount (REAL): The maximum salary amount.
        - interval (TEXT): The salary interval (e.g., yearly, monthly).
        - currency (TEXT): The currency of the salary.
        - job_url (TEXT): The URL to the job posting.
    """
    db_path = os.getenv("DATABASE_FILE", "all_jobs.sqlite")
    db_exists = os.path.exists(db_path)

    # Informational print about database creation, not a return condition
    if os.getenv("DATABASE_FILE") and not db_exists: # User specified a path that doesn't exist
        print(f"Database file '{db_path}' (from DATABASE_FILE env var) does not exist. It will be created by SQLite.")
    elif not db_exists: # Default path doesn't exist
         print(f"Default database file '{db_path}' does not exist. It will be created by SQLite.")
    
    # Ensure the directory for the database file exists, if specified in db_path
    db_dir = os.path.dirname(db_path)
    if db_dir: # Only create directories if a path component is present
        os.makedirs(db_dir, exist_ok=True)

    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                location TEXT,
                description TEXT,
                min_amount REAL,
                max_amount REAL,
                interval TEXT,
                currency TEXT,
                job_url TEXT
            )
            """
        )
        # Create users table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                first_name TEXT NOT NULL,
                surname TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mobile_number TEXT NOT NULL,
                postcode TEXT NOT NULL,
                previous_job_title TEXT,
                previous_company TEXT,
                previous_job_description TEXT,
                email_validated BOOLEAN DEFAULT 0,
                validation_token TEXT,
                token_expiry DATETIME
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def process_markdown(text):
    """Converts markdown text to sanitized HTML.

    This function takes a markdown string, converts it to HTML using the
    `markdown` library, and then sanitizes the HTML using `bleach` to
    prevent XSS attacks.

    Markdown Extensions Used:
        - nl2br: Converts newlines to <br> tags.
        - fenced_code: Allows for code blocks using backticks.

    Args:
        text (str): The markdown text to convert.

    Returns:
        str: The sanitized HTML output.
    """
    # Convert markdown to HTML with safe extensions
    html = markdown.markdown(
        text, extensions=["nl2br", "fenced_code"], output_format="html5"
    )

    # Clean the HTML output to prevent XSS
    allowed_tags = [
        "p",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "a",
        "code",
        "pre",
        "br",
        "hr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]
    allowed_attrs = {"a": ["href", "title", "target"]}

    clean_html = bleach.clean(
        html, tags=allowed_tags, attributes=allowed_attrs, strip=True
    )
    return clean_html


# Placeholder email sending functions
def send_validation_email(user_email, validation_link):
    """
    Placeholder function to send a validation email.
    In a real application, this would use Flask-Mail to send an email.
    """
    """Sends a validation email to the user."""
    # Note: 'username' argument was added to the function signature
    try:
        msg = Message(
            subject="Validate your email address for Hudd-Jobs",
            sender=app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=[user_email]
        )
        msg.body = f"""Hi {username},

Please click the following link to validate your email address and complete your registration for Hudd-Jobs:
{validation_link}

This link will expire in 24 hours.

If you did not register for Hudd-Jobs, please ignore this email.

Thanks,
The Hudd-Jobs Team
"""
        mail.send(msg)
        print(f"Validation email supposedly sent to {user_email} for user {username} with link: {validation_link}")
    except Exception as e:
        print(f"Error sending validation email to {user_email}: {e}")
        # In a production app, you might want to handle this more gracefully


def send_welcome_email(user_email):
    """
    Placeholder function to send a welcome email.
    In a real application, this would use Flask-Mail to send an email.
    """
    print(f"Sending welcome email to: {user_email}")
    # Example (actual email sending would be here):
    # from flask_mail import Message
    # msg = Message("Welcome to Hudd-Jobs!", recipients=[user_email])
    # msg.body = "Thank you for registering at Hudd-Jobs.com!"
    # mail.send(msg)


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create a test user (replace with database storage in production)
# test_user = User(
#     id=1, 
#     username="chris", 
#     password=generate_password_hash("Liam1234"),
#     first_name="Chris",
#     surname="Test",
#     postcode="SW1A 1AA",
#     mobile_number="07123456789",
#     email="chris@example.com"
#     # previous_job_title, previous_company, previous_job_description are optional
#     # email_validated defaults to False
# )
# users[test_user.username] = test_user # This 'users' dictionary is also removed.


@login_manager.user_loader
def load_user(user_id):
    """Load a user from the user_id by querying the database."""
    conn = get_db_connection()
    try:
        user_data = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    
    if user_data:
        user_obj = User(
            id=user_data["id"],
            username=user_data["username"],
            password=user_data["password"], # Password in DB is already hashed
            first_name=user_data["first_name"],
            surname=user_data["surname"],
            postcode=user_data["postcode"],
            mobile_number=user_data["mobile_number"],
            email=user_data["email"],
            previous_job_title=user_data["previous_job_title"],
            previous_company=user_data["previous_company"],
            previous_job_description=user_data["previous_job_description"]
        )
        user_obj.email_validated = bool(user_data["email_validated"]) # Set from DB
        return user_obj
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user authentication.

    If the current user is already authenticated, redirects to the index page.

    For GET requests:
        Renders the login page.

    For POST requests:
        Attempts to authenticate the user based on 'username' and 'password'
        submitted in the form.
        - On successful authentication: Logs the user in and redirects to the
          index page.
        - On failed authentication: Flashes an "Invalid username or password"
          message and re-renders the login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("login.html")

    # Handle POST request for login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        try:
            user_data = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        finally:
            conn.close()

        if user_data and check_password_hash(user_data["password"], password):
            # Reconstruct the User object for Flask-Login
            user_obj = User(
                id=user_data["id"],
                username=user_data["username"],
                password=user_data["password"], # Already hashed
                first_name=user_data["first_name"],
                surname=user_data["surname"],
                postcode=user_data["postcode"],
                mobile_number=user_data["mobile_number"],
                email=user_data["email"],
                previous_job_title=user_data["previous_job_title"],
                previous_company=user_data["previous_company"],
                previous_job_description=user_data["previous_job_description"]
            )
            # Set email_validated status from DB
            user_obj.email_validated = bool(user_data["email_validated"])
            login_user(user_obj)
            return redirect(url_for("index"))

        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration.

    For GET requests:
        Renders the registration page.

    For POST requests:
        Validates form data, creates a new user, prints user attributes
        to the console, and redirects to the login page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        mobile_number = request.form.get("mobile_number")
        postcode = request.form.get("postcode")
        # Optional fields
        previous_job_title = request.form.get("previous_job_title")
        previous_company = request.form.get("previous_company")
        previous_job_description = request.form.get("previous_job_description")

        # Basic validation
        required_fields = [username, password, first_name, surname, email, mobile_number, postcode]
        if not all(required_fields):
            flash("All mandatory fields are required.")
            return render_template("register.html")
        
        # Check if username or email already exists in DB
        conn_check = get_db_connection()
        try:
            existing_user_by_username = conn_check.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing_user_by_username:
                flash("Username already exists.")
                return render_template("register.html")
            existing_user_by_email = conn_check.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing_user_by_email:
                flash("Email address already registered.")
                return render_template("register.html")
        finally:
            conn_check.close()

        hashed_password = generate_password_hash(password)
        
        # The User object is created here mainly for structure, ID will be from DB
        # email_validated defaults to False in the User model

        # Generate validation token and expiry
        validation_token = secrets.token_urlsafe(32)
        token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

        new_user_obj = User(
            id=None, # Will be set by DB
            username=username,
            password=hashed_password, # Already hashed
            first_name=first_name,
            surname=surname,
            postcode=postcode,
            mobile_number=mobile_number,
            email=email,
            previous_job_title=previous_job_title,
            previous_company=previous_company,
            previous_job_description=previous_job_description
        )

        conn_insert = get_db_connection()
        try:
            cursor = conn_insert.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, first_name, surname, email, mobile_number, postcode, 
                                   previous_job_title, previous_company, previous_job_description, email_validated,
                                   validation_token, token_expiry)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_user_obj.username, new_user_obj.password, new_user_obj.first_name, new_user_obj.surname,
                  new_user_obj.email, new_user_obj.mobile_number, new_user_obj.postcode,
                  new_user_obj.previous_job_title, new_user_obj.previous_company,
                  new_user_obj.previous_job_description, new_user_obj.email_validated,
                  validation_token, token_expiry)) # Add token and expiry to DB
            conn_insert.commit()
            inserted_id = cursor.lastrowid # Get the ID of the newly inserted user
        except sqlite3.IntegrityError:
            # This might happen if, despite earlier checks, username/email is not unique (race condition, etc.)
            flash("An error occurred during registration. Username or email might already be taken.")
            return render_template("register.html")
        finally:
            conn_insert.close()

        # Print user attributes to console for verification
        print("New user registered with DB:")
        print(f"  ID: {inserted_id}") # Print the ID from the database
        print(f"  Username: {new_user_obj.username}")
        print(f"  Email: {new_user_obj.email}")
        print(f"  First Name: {new_user_obj.first_name}")
        print(f"  Surname: {new_user_obj.surname}")
        print(f"  Postcode: {new_user_obj.postcode}")
        print(f"  Mobile Number: {new_user_obj.mobile_number}")
        # new_user_obj.email_validated is False by default from User model constructor
        print(f"  Email Validated: {new_user_obj.email_validated}")
        # For debugging purposes, remove in production if sensitive
        # print(f"  Validation Token: {validation_token}")
        # print(f"  Token Expiry: {token_expiry}")
        if new_user_obj.previous_job_title:
            print(f"  Previous Job Title: {new_user_obj.previous_job_title}")
        if new_user_obj.previous_company:
            print(f"  Previous Company: {new_user_obj.previous_company}")
        if new_user_obj.previous_job_description:
            print(f"  Previous Job Description: {new_user_obj.previous_job_description}")
        
        # Send validation email
        # The username argument was added to send_validation_email
        validation_link = url_for('validate_email', token=validation_token, _external=True)
        send_validation_email(new_user_obj.email, new_user_obj.username, validation_link)

        flash("Registration successful! Please check your email to validate your account before logging in.")
        return redirect(url_for("login")) # Or a page saying "check your email"

    return render_template("register.html")


@app.route('/validate_email/<token>', methods=['GET'])
def validate_email(token):
    """Validates user's email address based on the provided token."""
    conn = get_db_connection()
    try:
        # Fetch user by validation token
        user_data = conn.execute("SELECT * FROM users WHERE validation_token = ?", (token,)).fetchone()

        if not user_data:
            flash("Invalid validation link.", "danger")
            return redirect(url_for('register'))

        # Check token expiry
        # Ensure token_expiry is a datetime object if it's stored as TEXT/ISOFORMAT
        # SQLite stores DATETIME as TEXT in ISO format, so parse it.
        token_expiry_str = user_data["token_expiry"]
        token_expiry_dt = datetime.datetime.fromisoformat(token_expiry_str)

        if datetime.datetime.utcnow() > token_expiry_dt:
            flash("Validation link has expired. Please register again or request a new validation email.", "warning")
            # Optionally, here you could offer to resend validation or delete the old user record
            return redirect(url_for('register'))

        # Token is valid and not expired, update user
        conn.execute("""
            UPDATE users 
            SET email_validated = 1, validation_token = NULL, token_expiry = NULL 
            WHERE id = ?
        """, (user_data["id"],))
        conn.commit()

        # Send welcome email
        send_welcome_email(user_data["email"]) # Assuming send_welcome_email takes user_email

        flash("Email validated successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    except sqlite3.Error as e:
        print(f"Database error during email validation: {e}")
        flash("An error occurred during email validation. Please try again.", "danger")
        return redirect(url_for('register'))
    except Exception as e:
        # Catch any other unexpected errors, e.g., datetime parsing
        print(f"Unexpected error during email validation: {e}")
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for('register'))
    finally:
        if conn:
            conn.close()


@app.route("/logout")
@login_required
def logout():
    """Logs out the currently authenticated user.

    Requires user login.
    After logging out, it flashes a confirmation message ("You have been
    logged out.") and redirects the user to the login page.
    """
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Renders the main page of the application.

    Displays the three most recent blog posts, sorted by ID in descending order.
    """
    # Get the 3 most recent blog posts (sorted by ID in reverse order)
    recent_posts = dict(sorted(blog_posts.items(), reverse=True)[:3])
    return render_template("index.html", blog_posts=recent_posts)


@app.route("/blog/<int:post_id>")
@login_required
def blog_post(post_id):
    """Displays a specific blog post identified by its post_id.

    Requires user login.
    The content of the blog post, assumed to be in Markdown format,
    is converted to HTML before rendering. If a post with the given
    post_id is not found, the user is redirected to the index page.

    Args:
        post_id (int): The ID of the blog post to display.
    """
    post = blog_posts.get(post_id)
    if not post:
        return redirect(url_for("index"))
    # Convert markdown content to HTML
    post = dict(post)
    post["content"] = markdown.markdown(post["content"])
    return render_template("blog_post.html", post=post)


@app.route("/search")
@login_required
def search():
    """Handles job searches based on a query parameter 'q'.

    Requires user login.
    Results are paginated. Job titles are formatted to title case,
    and salary information is formatted into a readable string.
    If the query parameter 'q' is not provided or is empty,
    it redirects to the index page.
    """
    query = request.args.get("q", "")
    if not query:
        return redirect(url_for("index"))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        total = conn.execute(
            """SELECT COUNT(*) FROM jobs
               WHERE title LIKE ? OR description LIKE ?""",
            (f"%{query}%", f"%{query}%"),
        ).fetchone()[0]

        jobs = conn.execute(
            """SELECT id, title, location, min_amount, max_amount, interval, currency
               FROM jobs
               WHERE title LIKE ? OR description LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{query}%", f"%{query}%", per_page, offset),
        ).fetchall()

        jobs = [dict(job) for job in jobs]
        for job in jobs:
            job["title"] = format_title_case(job["title"])
            job["salary"] = format_salary(
                job["min_amount"], job["max_amount"], job["currency"], job["interval"]
            )

    finally:
        conn.close()

    pagination = Pagination(
        page=page, total=total, per_page=per_page, css_framework="govuk"
    )

    return render_template(
        "search_results.html",
        jobs=jobs,
        pagination=pagination,
        page=page,
        per_page=per_page,
        search_query=query,
        total=total,
    )
@app.route("/jobs")
@app.route("/jobs/<string:job_id>")
@login_required
def view_job(job_id=None):
    """Displays detailed information for a specific job.

    Requires user login.
    If no job_id is provided in the URL, it redirects to the index page.
    The job description, assumed to be in Markdown, is processed and
    converted to HTML. The job title is formatted to title case, and
    the salary information is formatted into a readable string.
    If a job with the given job_id is not found, a message is flashed
    to the user, and they are redirected to the index page.

    Args:
        job_id (str, optional): The ID of the job to display. Defaults to None.
    """
    if job_id is None:
        # If no job_id is provided, redirect to index
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            flash("Job not found")
            return redirect(url_for("index"))

        job = dict(job)
        job["description"] = process_markdown(job["description"])
        job["title"] = format_title_case(job["title"])
        job["salary"] = format_salary(
            job["min_amount"], job["max_amount"], job["currency"], job["interval"]
        )

        return render_template("job_detail.html", job=job)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash("Error retrieving job details")
        return redirect(url_for("index"))
    finally:
        conn.close()

if __name__ == "__main__":
    init_db() # Ensure this is called to create tables, including users table
    app.run(debug=True)
