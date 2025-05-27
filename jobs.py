from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_paginate import Pagination, get_page_parameter
from pony.orm import db_session, select, count, desc # PonyORM imports
from models.models import Job # PonyORM Job entity
from utils.utils import format_title_case, format_salary, process_markdown

jobs_bp = Blueprint('jobs', __name__, template_folder='../templates')

@jobs_bp.route('/search', methods=['GET'])
@db_session
def search():
    query = request.args.get('query', '').strip()
    location = request.args.get('location', '').strip()
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10

    jobs_query = select(j for j in Job)

    if query:
        jobs_query = jobs_query.filter(
            lambda j: query.lower() in j.title.lower() or \
                      (j.description and query.lower() in j.description.lower()) or \
                      (j.company and query.lower() in j.company.lower())
        )
    
    if location:
        jobs_query = jobs_query.filter(lambda j: j.location and location.lower() in j.location.lower())

    total_jobs = count(jobs_query)
    
    # Apply ordering and pagination
    # Note: Pony's desc() is applied to the attribute directly in order_by
    ordered_jobs_query = jobs_query.order_by(desc(Job.posted_date))
    
    # Pony's page() is 1-indexed.
    job_entities = list(ordered_jobs_query.page(page, per_page=per_page))

    jobs_list = []
    for job_entity in job_entities:
        jobs_list.append({
            'id': job_entity.id,
            'title': format_title_case(job_entity.title),
            'company': job_entity.company,
            'location': job_entity.location,
            'description': (job_entity.description[:200] + '...') if job_entity.description else '',
            'posted_date': job_entity.posted_date.strftime('%Y-%m-%d') if job_entity.posted_date else 'N/A',
            # Assuming format_salary can handle None for min/max
            'salary_min': format_salary(job_entity.salary_min, job_entity.salary_max, job_entity.salary_currency, None)[0] if job_entity.salary_min is not None else None, # Simplified, adjust format_salary if needed
            'salary_max': format_salary(job_entity.salary_min, job_entity.salary_max, job_entity.salary_currency, None)[1] if job_entity.salary_max is not None else None, # Simplified
            'salary_str': format_salary(job_entity.salary_min, job_entity.salary_max, job_entity.salary_currency, job_entity.job_type), # For display
            'salary_currency': job_entity.salary_currency,
            'job_type': format_title_case(job_entity.job_type) if job_entity.job_type else 'N/A',
            'company_url': job_entity.company_url
        })
        
    pagination = Pagination(page=page, total=total_jobs, per_page=per_page, css_framework='bootstrap4')
    return render_template('search_results.html', jobs=jobs_list, query=query, location=location, pagination=pagination)

@jobs_bp.route('/job/<int:job_id>')
@db_session
def view_job(job_id):
    job_entity = Job.get(id=job_id)
    if job_entity:
        job_detail = {
            'id': job_entity.id, # Added id for consistency
            'title': format_title_case(job_entity.title),
            'company': job_entity.company,
            'location': job_entity.location,
            'description': process_markdown(job_entity.description) if job_entity.description else 'No description available.',
            'posted_date': job_entity.posted_date.strftime('%Y-%m-%d') if job_entity.posted_date else 'N/A',
            'salary_str': format_salary(job_entity.salary_min, job_entity.salary_max, job_entity.salary_currency, job_entity.job_type), # For display
            'job_type': format_title_case(job_entity.job_type) if job_entity.job_type else 'N/A',
            'company_url': job_entity.company_url,
            'apply_url': job_entity.apply_url # Added apply_url
        }
        return render_template('job_details.html', job=job_detail)
    else:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs.search'))
