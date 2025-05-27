from datetime import datetime
from pony.orm import *
from flask_login import UserMixin

# Initialize PonyORM Database object
db = Database()

class User(db.Entity, UserMixin):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    email = Required(str, unique=True)
    password_hash = Required(str)
    api_key = Required(str, unique=True)
    email_validated = Required(bool, default=False)
    validation_token = Optional(str, nullable=True)
    created_at = Required(datetime, default=datetime.utcnow)
    # Relationships
    saved_jobs = Set("SavedJob")
    job_applications = Set("JobApplication")

    # UserMixin properties:
    # PonyORM handles 'id' automatically.
    # Flask-Login's UserMixin provides default implementations for:
    # is_authenticated: Returns True if the user has provided valid credentials.
    # is_anonymous: Returns False by default.
    # get_id(): Returns the user's ID (which PonyORM provides as self.id).
    
    @property
    def is_active(self):
        """Returns True if the user's email is validated, False otherwise."""
        return self.email_validated

class Job(db.Entity):
    id = PrimaryKey(int, auto=True)
    title = Required(str)
    company = Optional(str, nullable=True)
    location = Optional(str, nullable=True)
    description = Optional(LongStr, nullable=True) # For longer text
    posted_date = Optional(datetime) # Using datetime for posted_date
    salary_min = Optional(float, nullable=True)
    salary_max = Optional(float, nullable=True)
    salary_currency = Optional(str, nullable=True)
    job_type = Optional(str, nullable=True)
    company_url = Optional(str, nullable=True)
    apply_url = Optional(str, nullable=True)
    source_platform = Optional(str, nullable=True)
    created_at = Required(datetime, default=datetime.utcnow)
    # Relationships
    saved_jobs = Set("SavedJob") # Relationship via SavedJob entity
    applications = Set("JobApplication") # Relationship via JobApplication entity

class SavedJob(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    job = Required(Job)
    saved_at = Required(datetime, default=datetime.utcnow)
    # To ensure a user can save a job only once:
    composite_key(user, job)

class JobApplication(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    job = Required(Job)
    application_date = Required(datetime, default=datetime.utcnow)
    status = Required(str, default='Applied') # e.g., Applied, Interviewing, Offer, Rejected
    notes = Optional(LongStr, nullable=True)
    # To ensure a user can apply for a job only once:
    composite_key(user, job)
