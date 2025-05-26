from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_paginate import Pagination, get_page_parameter
from db import get_db_connection # Updated import
from utils.utils import format_title_case, format_salary, process_markdown # process_markdown moved here

jobs_bp = Blueprint('jobs', __name__, template_folder='../templates')

@jobs_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10
    offset = (page - 1) * per_page
    conn = get_db_connection()
    cursor = conn.cursor()
    sql_query = """
        SELECT j.id, j.title, j.company, j.location, j.description, j.posted_date, j.salary_min, j.salary_max, j.salary_currency, j.job_type, j.company_url, COUNT(*) OVER() as total_count
        FROM jobs j
        WHERE (j.title ILIKE ? OR j.description ILIKE ? OR j.company ILIKE ?)
    """
    params = [f'%{query}%', f'%{query}%', f'%{query}%']
    if location:
        sql_query += " AND j.location ILIKE ?"
        params.append(f'%{location}%')
    sql_query += " ORDER BY j.posted_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    cursor.execute(sql_query, tuple(params))
    jobs_data = cursor.fetchall()
    total_jobs = jobs_data[0][-1] if jobs_data else 0
    conn.close()
    jobs = []
    for job_data in jobs_data:
        jobs.append({
            'id': job_data[0],
            'title': format_title_case(job_data[1]),
            'company': job_data[2],
            'location': job_data[3],
            'description': job_data[4][:200] + '...' if job_data[4] else '',
            'posted_date': job_data[5].strftime('%Y-%m-%d'),
            'salary_min': format_salary(job_data[6]),
            'salary_max': format_salary(job_data[7]),
            'salary_currency': job_data[8],
            'job_type': format_title_case(job_data[9]),
            'company_url': job_data[10]
        })
    pagination = Pagination(page=page, total=total_jobs, per_page=per_page, css_framework='bootstrap4')
    return render_template('search_results.html', jobs=jobs, query=query, location=location, pagination=pagination)

@jobs_bp.route('/job/<int:job_id>')
def view_job(job_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, company, location, description, posted_date, salary_min, salary_max, salary_currency, job_type, company_url FROM jobs WHERE id = ?", (job_id,))
    job_data = cursor.fetchone()
    conn.close()
    if job_data:
        job = {
            'title': format_title_case(job_data[0]),
            'company': job_data[1],
            'location': job_data[2],
            'description': process_markdown(job_data[3]),
            'posted_date': job_data[4].strftime('%Y-%m-%d'),
            'salary_min': format_salary(job_data[5]),
            'salary_max': format_salary(job_data[6]),
            'salary_currency': job_data[7],
            'job_type': format_title_case(job_data[8]),
            'company_url': job_data[9]
        }
        return render_template('job_details.html', job=job)
    else:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs.search'))
