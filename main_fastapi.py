import os
import sqlite3
import markdown
import bleach
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from werkzeug.security import check_password_hash, generate_password_hash
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from blog import blog_posts
from models.models import User, users
from utils.utils import format_title_case, format_salary

load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not os.path.exists(os.getenv("DATABASE_FILE", "2.sqlite")):
        raise FileNotFoundError(
            "Database file not found. Please ensure the database file exists."
        )
    try:
        conn = sqlite3.connect(os.getenv("DATABASE_FILE", "Z:/all_jobs.sqlite"))
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise

def init_db():
    """Initializes the database by creating the necessary tables."""
    if not os.path.exists(os.getenv("DATABASE_FILE", "Z:/all_jobs.sqlite")):
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
        "p", "ul", "ol", "li", "strong", "em", "a", "code", "pre", "br", "hr",
        "h1", "h2", "h3", "h4", "h5", "h6",
    ]
    allowed_attrs = {"a": ["href", "title", "target"]}
    clean_html = bleach.clean(
        html, tags=allowed_tags, attributes=allowed_attrs, strip=True
    )
    return clean_html

# In-memory user store for demonstration
test_user = User(id=1, username="chris", password=generate_password_hash("Liam1234"))
users[test_user.username] = test_user

# Dummy function to get current user - replace with real authentication
def get_current_user(request: Request):
    user = request.session.get("user")
    if user:
        return users.get(user["username"])
    return None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    recent_posts = dict(sorted(blog_posts.items(), reverse=True)[:3])
    return templates.TemplateResponse("index.html", {"request": request, "blog_posts": recent_posts, "current_user": get_current_user(request)})

@app.get("/blog/{post_id}", response_class=HTMLResponse)
async def blog_post(request: Request, post_id: int):
    post = blog_posts.get(post_id)
    if not post:
        return RedirectResponse(url="/")
    post = dict(post)
    post["content"] = markdown.markdown(post["content"])
    return templates.TemplateResponse("blog_post.html", {"request": request, "post": post, "current_user": get_current_user(request)})

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    if not q:
        return RedirectResponse(url="/")

    page = int(request.query_params.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE title LIKE ? OR description LIKE ?",
            (f"%{q}%", f"%{q}%")
        ).fetchone()[0]

        jobs_cursor = conn.execute(
            """SELECT id, title, location, min_amount, max_amount, interval, currency
               FROM jobs WHERE title LIKE ? OR description LIKE ? LIMIT ? OFFSET ?""",
            (f"%{q}%", f"%{q}%", per_page, offset)
        )
        jobs = [dict(row) for row in jobs_cursor.fetchall()]
        for job in jobs:
            job["title"] = format_title_case(job["title"])
            job["salary"] = format_salary(
                job["min_amount"], job["max_amount"], job["currency"], job["interval"]
            )
    finally:
        conn.close()

    # Pagination logic to be adapted
    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "jobs": jobs,
            "pagination": None,  # Placeholder for pagination
            "page": page,
            "per_page": per_page,
            "search_query": q,
            "total": total,
            "current_user": get_current_user(request)
        },
    )

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def view_job(request: Request, job_id: str):
    conn = get_db_connection()
    try:
        job_cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = job_cursor.fetchone()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        job = dict(job)
        job["description"] = process_markdown(job["description"])
        job["title"] = format_title_case(job["title"])
        job["salary"] = format_salary(
            job["min_amount"], job["max_amount"], job["currency"], job["interval"]
        )
        return templates.TemplateResponse("job_detail.html", {"request": request, "job": job, "current_user": get_current_user(request)})
    finally:
        conn.close()

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users.get(username)
    if user and check_password_hash(user.password, password):
        request.session["user"] = {"username": user.username, "id": user.id}
        return RedirectResponse(url="/", status_code=303)

    # Flashing messages needs to be handled differently in FastAPI
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
