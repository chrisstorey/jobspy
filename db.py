import os
import sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL', 'instance/job_search_app.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = DATABASE_URL
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DROP TABLE IF EXISTS users;
    """)
    cursor.execute("""
        DROP TABLE IF EXISTS jobs;
    """)
    cursor.execute("""
        DROP TABLE IF EXISTS saved_jobs;
    """)
    cursor.execute("""
        DROP TABLE IF EXISTS job_applications;
    """)

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            email_validated BOOLEAN DEFAULT FALSE,
            validation_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            posted_date DATE,
            salary_min REAL,
            salary_max REAL,
            salary_currency TEXT,
            job_type TEXT,  -- e.g., Full-time, Part-time, Contract
            company_url TEXT,
            apply_url TEXT,
            source_platform TEXT, -- e.g., LinkedIn, Indeed, Company Website
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Table for users to save jobs
    cursor.execute("""
        CREATE TABLE saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            UNIQUE(user_id, job_id)
        );
    """)
    # Table for tracking job applications
    cursor.execute("""
        CREATE TABLE job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Applied', -- e.g., Applied, Interviewing, Offer, Rejected
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            UNIQUE(user_id, job_id)
        );
    """)
    conn.commit()
    conn.close()
