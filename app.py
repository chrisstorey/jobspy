import os
import sqlite3

import bleach
import markdown

from dotenv import load_dotenv  # type: ignore
from flask import Flask, render_template, request, redirect, url_for, flash  # type: ignore
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

from models import User, users
from utils.utils import format_title_case, format_salary

# Add these utility functions at the top level, after the imports


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change this!
CORS(app)


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(os.getenv("DATABASE_FILE", "all_jobs.sqlite")):
        raise FileNotFoundError(
            "Database file not found. Please ensure the database file exists."
        )
    try:
        conn = sqlite3.connect(os.getenv("DATABASE_FILE", "Z:\all_jobs.sqlite"))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise


def init_db():
    """Initializes the database by creating the necessary tables."""
    if not os.path.exists(os.getenv("DATABASE_FILE", "Z:\all_jobs.sqlite")):
        print("Database file does not exist. Please check the path.")
        return

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
        conn.commit()
    finally:
        conn.close()


def process_markdown(text):
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


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create a test user (replace with database storage in production)
test_user = User(1, "chris", generate_password_hash("Liam1234"))
users[test_user.username] = test_user


@login_manager.user_loader
def load_user(user_id):
    """Load a user from the user_id."""
    # In this example, we're using a simple dictionary to store users
    # In a real application, you would query the database
    # to retrieve the user by their ID
    for user in users.values():
        if str(user.id) == user_id:
            return user
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login route to authenticate users."""
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("login.html")

    # Handle POST request for login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users.get(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Logout route to log out the user."""
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/")
def index():
    # Get the 3 most recent blog posts (sorted by ID in reverse order)
    recent_posts = dict(sorted(blog_posts.items(), reverse=True)[:3])
    return render_template("index.html", blog_posts=recent_posts)


@app.route("/blog/<int:post_id>")
@login_required
def blog_post(post_id):
    post = blog_posts.get(post_id)
    if not post:
        return redirect(url_for("index"))
    # Convert markdown content to HTML
    post = dict(post)
    post["content"] = markdown.markdown(post["content"])
    return render_template("blog_post.html", post=post)


@app.route("/jobs")
@app.route("/search")
@login_required
def search():
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

@app.route("/job/<string:job_id>")
@login_required
def view_job(job_id):
    print(f"Job ID type: {type(job_id)}, value: {job_id}")  # Debug line
    conn = get_db_connection()
    try:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            flash("Job not found")
            return redirect(url_for("index"))

        job = dict(job)
        job["description"] = process_markdown(job["description"])
        conn.close()
        return render_template("job_detail.html", job=job)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash("Error retrieving job details")
        return redirect(url_for("index"))
    finally:
        conn.close()

@app.route("/jobs")
@app.route("/jobs/<string:job_id>")
@login_required
def view_job(job_id=None):
    if job_id is None:
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            return redirect(url_for("index"))

        job = dict(job)
        job["description"] = process_markdown(job["description"])
        job["title"] = format_title_case(job["title"])
        job["salary"] = format_salary(
            job["min_amount"], job["max_amount"], job["currency"], job["interval"]
        )

    finally:
        conn.close()

    return render_template("jobs.html", job=job, pagination=None)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
