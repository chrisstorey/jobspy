import os
import sqlite3

import bleach
import markdown
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_cors import CORS
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, users

load_dotenv()

blog_posts = {
    2: {
        "title": "Moving On From Your Entry-Level Job",
        "image": "https://images.unsplash.com/photo-1549588628-34abaf47106c?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "date": "March 15, 2024",
        "excerpt": "Ready to level up your career in Huddersfield? This article guides you through recognizing when it's time to move on from your entry-level job and highlights local resources to help you take that next step....",
        "content": """
Congratulations! You've landed that first step on the career ladder, gained valuable experience, and now you're feeling that familiar itch – the desire to grow and take on new challenges. Moving on from an entry-level job is a natural part of career progression, and in a vibrant town like Huddersfield, there are resources and strategies to help you make that leap successfully.

## Recognizing It's Time for a Change

How do you know when it's time to move on? Here are a few tell-tale signs:

* **You've mastered your current role:** The tasks have become routine, and you're no longer learning new skills
* **Limited growth opportunities:** You see little to no possibility for advancement within your current company
* **Your skills and interests have evolved:** You've discovered new passions or developed skills that aren't being utilized
* **You're feeling stagnant or unfulfilled:** Your work no longer excites you, and you crave more responsibility

## Taking Proactive Steps

Once you've recognized it's time for a change, here's how to approach your next career move in Huddersfield:

1. **Self-Assessment and Goal Setting:** Take time to reflect on your skills, interests, and values
2. **Update Your CV and Cover Letter:** Highlight skills and accomplishments from your entry-level role
3. **Network, Network, Network:** Attend local industry events and join professional groups
4. **Skill Development:** Identify and address skills gaps through courses and workshops
5. **Job Searching Strategies:** Utilize online job boards and company career pages
6. **Prepare for Interviews:** Practice your interview skills and articulate your career goals

## Who Can Help You in Huddersfield?

Huddersfield offers several resources to support you in your career transition:

* **Kirklees Council Employment and Skills:** Access job fairs and training programs
* **Huddersfield University Careers Service:** Career guidance and resources
* **Local Recruitment Agencies:** Connect with agencies specializing in your field
* **Networking Groups:** Join the Huddersfield & District Chamber of Commerce
* **Local Colleges:** Explore courses at Kirklees College for upskilling

Moving on from your entry-level job is an exciting step in your career journey. By being proactive and utilizing local resources, you can successfully navigate this transition.
""",
    },
    1: {
        "title": "Finding support in mentorship",
        "image": "https://picsum.photos/seed/remote/800/400",
        "date": "April 27, 2025",
        "excerpt": "Ready to skyrocket your career or personal growth? Discover the power of mentorship and unlock invaluable guidance right here in your community. Let's find your perfect mentor! ...",
        "content": """
Okay, let's delve deeper into the world of mentorship in Huddersfield and expand on those initial ideas.

## Finding Mentors in Huddersfield: Guiding Your Journey to Success

Okay, I've expanded the article with more details from my search:

**Finding Mentors in Huddersfield**

**Introduction**

Mentorship is a valuable resource for personal and professional growth. A mentor can provide guidance, support, and inspiration, helping you to achieve your goals. If you are looking for a mentor in Huddersfield, there are a number of resources available to you.

**How to find a mentor in Huddersfield**

  * **Networking:** Attend industry events and meetups. This is a great way to meet potential mentors who are working in your field of interest. Check out platforms like [Meetup](https://www.meetup.com/find/gb--45--huddersfield/networking/) and [Eventbrite](https://www.eventbrite.co.uk/d/united-kingdom--huddersfield/networking/) for networking events in Huddersfield.

  * **Online platforms:** There are a number of online platforms that connect mentors and mentees. Some popular options include MentorCruise, NxtMngr, and ADPList.

  * **Professional organizations:** Many professional organizations have mentorship programs. The [Huddersfield Chamber of Commerce](https://www.google.com/search?q=https://www.huddersfieldchamber.com/) is a good place to start.

  * **University of Huddersfield:** [The University of Huddersfield](https://www.hud.ac.uk/) offers coaching and mentoring programs for staff and has mentors for students and startups. Check out their [coaching and mentoring page](https://staff.hud.ac.uk/hr/pod/coaching-and-mentoring/) for more information.

  * **General Practice Mentoring (GPMplus):** This free service is available for GPs, PMs, Nurses, and other practice staff with leadership or decision-making responsibilities in the West Yorkshire, North Yorkshire and Humberside areas. [GPMplus](https://gpmplus.co.uk/general-prcatice-mentoring-2/) can help with career goals, problem-solving, and work-life balance.

  * **Welcome Mentors:** Coordinated by Third Sector Leaders Kirklees, this program supports refugees, asylum seekers, and migrants settling in Kirklees. [Welcome Mentors](https://tslkirklees.org.uk/get-help-with/welcome-mentors/) offer help with accessing services and integrating into the community.

  * **Huddersfield Health Innovation Partnership (HHIP):** HHIP offers mentoring for health and wellbeing organizations looking to develop innovative products or services. More details can be found on the [HHIP support page](https://huddshealthinnovation.org/support/).

  * **Friends and family:** Ask your friends and family if they know anyone who might be a good mentor for you.

**Tips for finding a good mentor**

  * **Do your research:** Make sure you understand what you are looking for in a mentor. What are your goals? What skills do you want to develop?
  * **Be clear about your expectations:** Let your potential mentor know what you are hoping to gain from the relationship.
  * **Be proactive:** Don't wait for your mentor to reach out to you. Be sure to stay in touch and let them know how you are progressing.
  * **Be grateful:** Show your appreciation for your mentor's time and guidance.

**Conclusion**

Finding a mentor can be a great way to accelerate your personal and professional growth. If you are looking for a mentor in Huddersfield, there are a number of resources available to you. By following the tips above, you can increase your chances of finding a good mentor who can help you achieve your goals.

**Additional resources**

  * [Huddersfield Chamber of Commerce](https://www.google.com/search?q=https://www.huddersfieldchamber.com/)
  * [The University of Huddersfield](https://www.hud.ac.uk/)
  * [Huddersfield Young Professionals](https://www.google.com/search?q=https://www.huddersfieldyp.co.uk/)

I hope this article has been helpful. If you have any questions, please feel free to leave a comment below.
Remote work requires intentional boundaries between professional and personal life. We discuss strategies for maintaining productivity while avoiding burnout.
""",
    },
    3: {
        "title": "Top Tech Skills for 2024",
        "image": "https://picsum.photos/seed/skills/800/400",
        "date": "March 13, 2024",
        "excerpt": "Stay ahead of the curve with our comprehensive analysis of the most in-demand programming languages and technologies for 2024. From cloud computing to AI development...",
        "content": """
# Top Tech Skills for 2024

The tech industry continues to evolve rapidly. Here are the skills that will define success in 2024.

## Most In-Demand Programming Languages

* Python for AI and Data Science
* Rust for System Programming
* TypeScript for Web Development
* Kotlin for Android Development

## Emerging Technologies

Cloud computing, edge computing, and AI continue to reshape the technology landscape. Understanding these technologies is becoming essential for modern developers.

## Soft Skills Matter

Beyond technical expertise, employers are increasingly valuing soft skills like problem-solving, communication, and adaptability.
""",
    },
}

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change this!
CORS(app)


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(os.getenv("DATABASE_FILE", "Z:\all_jobs.sqlite")):
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
    # Check if the database file exists
    if not os.path.exists(os.getenv("DATABASE_FILE", "Z:\all_jobs.sqlite")):
        print("Database file does not exist. Please check the path.")
        return

    # Create the jobs table if it doesn't exist
    conn = get_db_connection()
    try:
        conn.execute(
            """
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
test_user = User(1, "admin", generate_password_hash("password123"))
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
        return redirect(url_for("index"))
    # Convert markdown content to HTML
    post = dict(post)
    post["content"] = markdown.markdown(post["content"])
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
                job["salary"] = (
                    f"{job['currency']}{job['min_amount']:,.0f} - {job['currency']}{job['max_amount']:,.0f} {job['interval']}"
                )
            else:
                job["salary"] = "Not specified"

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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
