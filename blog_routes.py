from flask import Blueprint, render_template, redirect, url_for, request
import markdown
from blog import blog_posts # Assuming blog.py contains the blog_posts list
from flask_paginate import Pagination, get_page_parameter

blog_bp = Blueprint('blog', __name__, template_folder='../templates')

@blog_bp.route('/')
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 5  # Number of posts per page
    offset = (page - 1) * per_page

    # Get post IDs and sort them in descending order (newest first)
    sorted_post_ids = sorted(blog_posts.keys(), reverse=True)
    
    all_posts_sorted = []
    for post_id in sorted_post_ids:
        post_data = blog_posts[post_id].copy() # Get a copy of the post dictionary
        post_data['id'] = post_id # Ensure the id is part of the dictionary
        all_posts_sorted.append(post_data)
        
    total_posts = len(all_posts_sorted)
    paginated_posts = all_posts_sorted[offset : offset + per_page]
    
    pagination = Pagination(page=page, total=total_posts, per_page=per_page, css_framework='bootstrap4')
    
    # The template 'index.html' expects 'posts' to be an iterable of post dictionaries.
    # And 'blog_posts' in the template was used for iterating items, which is suitable for dicts.
    # For consistency and to match the template's original expectation for `recent_posts` (which was a dict),
    # we might need to adjust how 'posts' is passed or how the template iterates.
    # However, the current template iterates `blog_posts.items()`.
    # Let's adjust what we pass to the template to be a dictionary for the main display,
    # and use paginated_posts for the paginated section if that was intended.
    # The original index.html template used: `{% for post_id, post in blog_posts.items() %}`
    # and then `recent_posts = dict(sorted(blog_posts.items(), reverse=True)[:3])`
    # The new template uses `posts` for pagination.

    # For index.html, it seems it now expects `posts` (the paginated list)
    # and `pagination` object.
    return render_template('index.html', posts=paginated_posts, pagination=pagination)

@blog_bp.route('/blog/<int:post_id>')
def blog_post(post_id):
    post_data = blog_posts.get(post_id)
    post = None
    if post_data:
        post = post_data.copy() # Make a copy
        post['id'] = post_id    # Ensure 'id' is in the dict for the template
        
    if post:
        # Ensure 'content' key exists before processing
        post_content = post.get('content', '')
        post_content_html = markdown.markdown(post_content)
        return render_template('blog_post.html', post=post, content_html=post_content_html)
    return render_template('404.html'), 404
