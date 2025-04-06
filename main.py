import os

import pandas as pd
from jobspy import scrape_jobs
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DATABASE_TABLE: str = os.getenv("DATABASE_TABLE")
DATABASE_FILE: str = os.getenv("DATABASE_FILE")
LOCATION: str = os.getenv("LOCATION")
MAX_RESULTS: int = os.getenv("MAX_RESULTS")
HOURS_OLD: int = os.getenv("HOURS_OLD")

#
connection = sqlite3.connect(DATABASE_FILE)

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

def get_jobs(search_term: str, location: str, results_wanted: int, hours_old: int) -> pd.DataFrame:
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "glassdoor", "google"],
        search_term=search_term,
        google_search_term=f"{search_term} jobs near {location}, since yesterday",
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="UK",
        linkedin_fetch_description=True,
    )
    return jobs




job_list2 = pd.DataFrame()

for sector in sectors:
    job_list = get_jobs(sector, LOCATION, MAX_RESULTS, HOURS_OLD)
    print(f"Found {len(job_list)} jobs in {sector}")
    job_list.to_sql(
        name=DATABASE_TABLE, con=connection, if_exists="append", index=False
    )
