import secrets
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models.models import User # User model from PonyORM
from pony.orm import db_session, select # PonyORM imports
from email_utils import send_validation_email, send_welcome_email # Updated import

login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Adjusted to auth.login

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@login_manager.user_loader
@db_session
def load_user(user_id):
    return User.get(id=user_id)

@auth_bp.route('/register', methods=['GET', 'POST'])
@db_session
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index')) # Corrected to blog.index
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.get(lambda u: u.username == username or u.email == email)
        if existing_user:
            flash('Username or email already exists. Please choose different ones.', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = generate_password_hash(password)
        api_key = secrets.token_hex(16) # Ensure api_key is generated
        validation_token = secrets.token_hex(16)
        
        User(
            username=username,
            email=email,
            password_hash=hashed_password,
            api_key=api_key,
            validation_token=validation_token
            # email_validated defaults to False, created_at defaults to now in model
        )
        # No explicit commit needed due to @db_session
        
        send_validation_email(email, validation_token)
        flash('Registration successful! Please check your email to validate your account.', 'success')
        return redirect(url_for('auth.login')) # Explicitly ensuring it's auth.login
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@db_session
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index')) # Corrected to blog.index
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get(username=username) # Fetch PonyORM User entity
        
        if user and check_password_hash(user.password_hash, password):
            if user.email_validated:
                login_user(user) # Pass the PonyORM User entity directly
                flash('Login successful!', 'success')
                # Corrected from url_for('index') to url_for('blog.index') as per previous context.
                # If 'index' is a different general dashboard, it should be 'some_other_blueprint.index' or just '/' if globally defined
                return redirect(url_for('blog.index')) 
            else:
                flash('Please validate your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid username or password.', 'danger')
            # For POST requests that fail login, we still want to re-render login.html
            return render_template('login.html') 
    # This is for GET requests
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/validate_email/<token>')
@db_session
def validate_email(token):
    user_to_validate = User.get(validation_token=token)
    if user_to_validate:
        if not user_to_validate.email_validated:
            user_to_validate.email_validated = True
            user_to_validate.validation_token = None # Clear the token
            send_welcome_email(user_to_validate.email)
            flash('Email validated successfully! You can now log in.', 'success')
        else:
            flash('Email already validated.', 'info')
    else:
        flash('Invalid or expired validation token.', 'danger')
    return redirect(url_for('auth.login'))
