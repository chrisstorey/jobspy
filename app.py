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
from flask_cors import CORS
from datetime import datetime


load_dotenv()

blog_posts = {
    1: {
        "title": "The Rise of AI in Software Development",
        "image": "https://picsum.photos/seed/ai/800/400",
        "date": "March 15, 2024",
        "excerpt": "Artificial Intelligence is revolutionizing how we approach software development. Modern AI tools like GitHub Copilot and ChatGPT are becoming increasingly prevalent in development workflows...",
        "content": """
            <p class="lead">Artificial Intelligence is revolutionizing how we approach software development, from code completion to testing and deployment.</p>

            <h2>The Current State of AI in Development</h2>
            <p>Modern AI tools like GitHub Copilot and ChatGPT are becoming increasingly prevalent in development workflows. These tools can suggest code completions, help debug issues, and even generate entire functions based on natural language descriptions.</p>

            <h2>Key Benefits</h2>
            <ul>
                <li>Increased developer productivity</li>
                <li>Reduced time spent on boilerplate code</li>
                <li>Better code quality through AI-assisted reviews</li>
                <li>Faster problem-solving and debugging</li>
            </ul>

            <h2>Looking Ahead</h2>
            <p>As AI continues to evolve, we can expect to see even more sophisticated tools that will help developers focus on higher-level problems while automating routine tasks. However, human creativity and problem-solving skills will remain essential in software development.</p>

            <blockquote class="blockquote">
                <p>"AI won't replace developers, but developers who use AI will replace those who don't."</p>
            </blockquote>
        """
    },
    2: {
        "title": "Remote Work Best Practices",
        "image": "https://picsum.photos/seed/remote/800/400",
        "date": "March 14, 2024",
        "excerpt": "As remote work becomes the norm in tech, establishing effective practices for virtual collaboration is crucial. Learn about the tools and strategies that make remote teams successful...",
        "content": """
            <p class="lead">The shift to remote work has fundamentally changed how tech teams collaborate and communicate.</p>

            <h2>Essential Remote Work Tools</h2>
            <p>Success in remote work environments depends heavily on the right combination of communication and collaboration tools. From video conferencing to asynchronous communication platforms, we explore the must-have tools for remote teams.</p>

            <h2>Communication Strategies</h2>
            <ul>
                <li>Regular team check-ins and standups</li>
                <li>Clear documentation practices</li>
                <li>Effective async communication</li>
                <li>Building virtual team culture</li>
            </ul>

            <h2>Work-Life Balance</h2>
            <p>Remote work requires intentional boundaries between professional and personal life. We discuss strategies for maintaining productivity while avoiding burnout.</p>
        """
    },
    3: {
        "title": "Top Tech Skills for 2024",
        "image": "https://picsum.photos/seed/skills/800/400",
        "date": "March 13, 2024",
        "excerpt": "Stay ahead of the curve with our comprehensive analysis of the most in-demand programming languages and technologies for 2024. From cloud computing to AI development...",
        "content": """
            <p class="lead">The tech industry continues to evolve rapidly. Here are the skills that will define success in 2024.</p>

            <h2>Most In-Demand Programming Languages</h2>
            <ul>
                <li>Python for AI and Data Science</li>
                <li>Rust for System Programming</li>
                <li>TypeScript for Web Development</li>
                <li>Kotlin for Android Development</li>
            </ul>

            <h2>Emerging Technologies</h2>
            <p>Cloud computing, edge computing, and AI continue to reshape the technology landscape. Understanding these technologies is becoming essential for modern developers.</p>

            <h2>Soft Skills Matter</h2>
            <p>Beyond technical expertise, employers are increasingly valuing soft skills like problem-solving, communication, and adaptability.</p>
        """
    }
}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here") # Change this!
CORS(app)

def get_db_connection():
    try:
        conn = sqlite3.connect(os.getenv("DATABASE_FILE", "Z:\all_jobs.sqlite"))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise


def init_db():
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                location TEXT,
                description TEXT,
                min_amount REAL,
                max_amount REAL,
                interval TEXT,
                currency TEXT,
                job_url TEXT
            )
        """)
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
    # Get the 3 most recent blog posts (sorted by ID in reverse order)
    recent_posts = dict(sorted(blog_posts.items(), reverse=True)[:3])
    return render_template("index.html", blog_posts=recent_posts)

@app.route("/blog/<int:post_id>")
@login_required
def blog_post(post_id):
    post = blog_posts.get(post_id)
    if not post:
        return redirect(url_for('index'))
    return render_template("blog_post.html", post=post)
@app.route("/jobs")
@login_required
def jobs():
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
            """SELECT id, title, location, min_amount, max_amount, interval, currency, job_url
               FROM jobs
               WHERE title LIKE ? OR description LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{query}%", f"%{query}%", per_page, offset),
        ).fetchall()

        jobs = [dict(job) for job in jobs]
        for job in jobs:
            if job["min_amount"] and job["max_amount"]:
                job["salary"] = f"{job['currency']}{job['min_amount']:,.0f} - {job['currency']}{job['max_amount']:,.0f} {job['interval']}"
            else:
                job["salary"] = "Not specified"

    finally:
        conn.close()

    pagination = Pagination(
        page=page,
        total=total,
        per_page=per_page,
        css_framework="govuk"
    )

    return render_template(
        "search_results.html",
        jobs=jobs,
        pagination=pagination,
        page=page,
        per_page=per_page,
        search_query=query,
        total=total
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
