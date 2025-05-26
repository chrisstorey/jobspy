from flask import Blueprint, render_template, redirect, url_for, request
import markdown
from blog import blog_posts # Assuming blog.py contains the blog_posts list
from flask_paginate import Pagination, get_page_parameter

blog_bp = Blueprint('blog', __name__, template_folder='../templates')

@blog_bp.route('/')
def index():
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 5
    offset = (page - 1) * per_page
    paginated_posts = blog_posts[offset: offset + per_page]
    pagination = Pagination(page=page, total=len(blog_posts), per_page=per_page, css_framework='bootstrap4')
    return render_template('index.html', posts=paginated_posts, pagination=pagination)

@blog_bp.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = next((p for p in blog_posts if p['id'] == post_id), None)
    if post:
        post_content_html = markdown.markdown(post['content'])
        return render_template('blog_post.html', post=post, content_html=post_content_html)
    return render_template('404.html'), 404
