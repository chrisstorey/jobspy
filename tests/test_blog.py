import pytest
from flask import url_for
from blog import blog_posts # To get actual post data for assertions

# Fixtures 'client', 'app' are expected from conftest.py

def test_blog_index_get(client):
    """Test GET request to the blog index page."""
    response = client.get(url_for('blog.index'))
    assert response.status_code == 200
    # Check for a common string from base.html or index.html.
    # "Hudd-Jobs.com" is the navbar brand in base.html.
    # "Welcome to Hudd-Jobs.com" is the main heading in index.html.
    assert b"Hudd-Jobs.com" in response.data 
    assert b"Welcome to Hudd-Jobs.com" in response.data

    # Check if titles of the first few posts (sorted by ID desc) are present
    sorted_post_ids = sorted(blog_posts.keys(), reverse=True)
    # In blog_routes.py, per_page = 5
    expected_on_first_page_ids = sorted_post_ids[:5] 

    for post_id in expected_on_first_page_ids:
        # Ensure the post_id from sorted_post_ids is actually in blog_posts before accessing
        if post_id in blog_posts:
            assert bytes(blog_posts[post_id]['title'], 'utf-8') in response.data

def test_blog_index_pagination(client):
    """Test pagination on the blog index page."""
    # In blog_routes.py, per_page = 5
    if len(blog_posts) <= 5: 
        pytest.skip("Not enough blog posts to test pagination meaningfully.")

    sorted_post_ids = sorted(blog_posts.keys(), reverse=True)
    
    # --- Page 1 ---
    response_page1 = client.get(url_for('blog.index', page=1))
    assert response_page1.status_code == 200
    
    # Check content of page 1 (e.g., first post title)
    first_post_id_page1 = sorted_post_ids[0]
    first_post_title_page1 = blog_posts[first_post_id_page1]['title']
    assert bytes(first_post_title_page1, 'utf-8') in response_page1.data

    # --- Page 2 ---
    response_page2 = client.get(url_for('blog.index', page=2))
    assert response_page2.status_code == 200
    
    # Ensure there's a 6th post for page 2 (index 5 in 0-indexed list)
    if len(sorted_post_ids) > 5:
        first_post_id_page2 = sorted_post_ids[5] 
        first_post_title_page2 = blog_posts[first_post_id_page2]['title']
        assert bytes(first_post_title_page2, 'utf-8') in response_page2.data
        
        # Crucially, the first post of page 1 should NOT be on page 2
        assert bytes(first_post_title_page1, 'utf-8') not in response_page2.data

def test_view_blog_post_success(client):
    """Test viewing a single existing blog post."""
    if not blog_posts:
        pytest.skip("No blog posts available to test viewing.")
        
    # Get an existing post ID from the blog_posts dictionary
    existing_post_id = list(blog_posts.keys())[0] 
    post_data = blog_posts[existing_post_id]
    
    response = client.get(url_for('blog.blog_post', post_id=existing_post_id))
    assert response.status_code == 200
    assert bytes(post_data['title'], 'utf-8') in response.data
    # Check for a part of the excerpt as content can be long and include complex HTML
    assert bytes(post_data['excerpt'], 'utf-8') in response.data

def test_view_blog_post_not_found(client):
    """Test viewing a non-existent blog post."""
    non_existent_id = 0
    # Find an ID that is guaranteed not to exist in blog_posts
    if blog_posts: # If there are any posts, find an ID larger than any existing one
        non_existent_id = max(list(blog_posts.keys())) + 1
    # If blog_posts is empty, non_existent_id = 0 is fine.

    response = client.get(url_for('blog.blog_post', post_id=non_existent_id))
    assert response.status_code == 404
    # Check for a generic 404 message from default Flask 404 page or a simple custom 404.html
    assert b"Not Found" in response.data
