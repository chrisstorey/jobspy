from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import pandas as pd
from flask_paginate import Pagination, get_page_parameter
from dotenv import load_dotenv
import os
import markdown
import bleach
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, users

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change this!


def get_db_connection():
    conn = sqlite3.connect(os.getenv("DATABASE_FILE", "all_jobs.sqlite"))
    conn.row_factory = sqlite3.Row
    return conn


def process_markdown(text):
    # Convert markdown to HTML with safe extensions
    html = markdown.markdown(text,
                             extensions=['nl2br', 'fenced_code'],
                             output_format='html5')

    # Clean the HTML output to prevent XSS
    allowed_tags = ['p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'code',
                    'pre', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attrs = {'a': ['href', 'title', 'target']}

    clean_html = bleach.clean(html,
                              tags=allowed_tags,
                              attributes=allowed_attrs,
                              strip=True)
    return clean_html


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create a test user (replace with database storage in production)
test_user = User(1, "admin", generate_password_hash("password123"))
users[test_user.username] = test_user


@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == user_id:
            return user
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
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
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 1
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    job = conn.execute("SELECT * FROM jobs LIMIT 1 OFFSET ?", (offset,)).fetchone()
    conn.close()

    if job is not None:
        job = dict(job)
        job["description"] = process_markdown(job["description"])

    pagination = Pagination(
        page=page, total=total, per_page=per_page, css_framework="govuk"
    )

    return render_template(
        "jobs.html", job=job, pagination=pagination, page=page, per_page=per_page
    )


if __name__ == "__main__":
    app.run(debug=True)
