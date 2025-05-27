import os
import pandas as pd
from dotenv import load_dotenv
from jobspy import scrape_jobs
from datetime import datetime, timedelta # For date parsing

# PonyORM imports
from pony.orm import db_session, select
from models.models import db as pony_db, Job

load_dotenv()

# --- PonyORM Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "instance/app.sqlite") # Default to a local sqlite file if not set

if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.split(":///")[-1] if ":///" in DATABASE_URL else DATABASE_URL
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    pony_db.bind(provider='sqlite', filename=db_path, create_db=True)
else:
    raise ValueError(f"Unsupported database provider for DATABASE_URL: {DATABASE_URL}. Only SQLite is configured for PonyORM currently.")

pony_db.generate_mapping(create_tables=True)
# --- End PonyORM Database Configuration ---

LOCATION: str = os.getenv("LOCATION", "Wakefield") # Default if not set
MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", 50)) # Default and ensure int
HOURS_OLD: int = int(os.getenv("HOURS_OLD", 24)) # Default and ensure int

sectors = [
    "healthcare",
    "education",
    "construction",
    "retail",
    "hospitality",
    "cleaning",
    "warehouse",
    "manufacturing",
    "transport",
    "finance",
    "technology",
    "engineering",
    "sales",
    "marketing",
    "hr",
    "admin",
    "customer service",
    "social care",
    "legal",
    "media",
    "creative",
    "security",
]

def parse_job_date(date_str: str) -> datetime | None:
    if not date_str or pd.isna(date_str):
        return None
    try:
        if "today" in date_str.lower() or "just posted" in date_str.lower():
            return datetime.utcnow()
        if "yesterday" in date_str.lower():
            return datetime.utcnow() - timedelta(days=1)
        # Add more specific parsing if needed, e.g., "N days ago"
        # For now, attempt direct parsing or fallback
        return pd.to_datetime(date_str).to_pydatetime()
    except (ValueError, TypeError):
        # Try to parse formats like "3 days ago"
        if "days ago" in date_str:
            try:
                days = int(date_str.split()[0])
                return datetime.utcnow() - timedelta(days=days)
            except:
                return None # Fallback if parsing fails
        return None


@db_session
def process_and_save_jobs():
    for sector in sectors:
        print(f"Scraping jobs for sector: {sector} in {LOCATION}")
        jobs_df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor", "google"], # Consider adding 'zip_recruiter' if relevant
            search_term=sector,
            # google_search_term=f"{sector} jobs near {LOCATION}", # Simplified, jobspy handles location
            location=LOCATION,
            results_wanted=MAX_RESULTS,
            hours_old=HOURS_OLD,
            country_indeed="UK",
            linkedin_fetch_description=True, # Fetch full description from LinkedIn
            # proxy=os.getenv("PROXY_URL") # Optional: if you have proxies
        )

        if jobs_df is None or jobs_df.empty:
            print(f"No jobs found for {sector}.")
            continue
        
        print(f"Found {len(jobs_df)} jobs in {sector}. Processing and saving to database...")

        for index, job_data in jobs_df.iterrows():
            # Use a unique identifier if available, e.g., job_url.
            # jobspy often provides 'job_url' which can be used.
            job_url = job_data.get('job_url')
            if not job_url: # If no job_url, construct a pseudo-unique key or skip
                print(f"Skipping job '{job_data.get('title')}' due to missing job_url.")
                continue

            existing_job = Job.get(apply_url=job_url)
            if existing_job:
                print(f"Job '{job_data.get('title')}' at '{job_url}' already exists. Skipping.")
                continue

            # Convert NaN to None for optional fields
            company = job_data.get('company') if pd.notna(job_data.get('company')) else None
            job_location = job_data.get('location') if pd.notna(job_data.get('location')) else None
            description = job_data.get('description') if pd.notna(job_data.get('description')) else None
            posted_date_str = job_data.get('date_posted') # jobspy often uses 'date_posted'
            posted_date = parse_job_date(posted_date_str)
            
            salary_min = job_data.get('min_amount') if pd.notna(job_data.get('min_amount')) else None
            salary_max = job_data.get('max_amount') if pd.notna(job_data.get('max_amount')) else None
            salary_currency = job_data.get('currency') if pd.notna(job_data.get('currency')) else None
            job_type = job_data.get('job_type') if pd.notna(job_data.get('job_type')) else None # e.g. "fulltime", "parttime"
            company_url = job_data.get('company_url') if pd.notna(job_data.get('company_url')) else None
            source_platform = job_data.get('site_name') if pd.notna(job_data.get('site_name')) else None


            try:
                Job(
                    title=job_data.get('title', 'N/A'), # Ensure title is present
                    company=company,
                    location=job_location,
                    description=description,
                    posted_date=posted_date,
                    salary_min=float(salary_min) if salary_min is not None else None,
                    salary_max=float(salary_max) if salary_max is not None else None,
                    salary_currency=salary_currency,
                    job_type=job_type,
                    company_url=company_url,
                    apply_url=job_url, # Using job_url as the apply_url
                    source_platform=source_platform
                )
                print(f"Saved job: {job_data.get('title')}")
            except Exception as e:
                print(f"Error saving job '{job_data.get('title')}': {e}")
                # Optionally, log more details or the job_data itself

if __name__ == "__main__":
    process_and_save_jobs()
    print("Job scraping and saving process completed.")
