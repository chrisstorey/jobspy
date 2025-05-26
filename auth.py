import secrets
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models.models import User
from db import get_db_connection # Updated import
from email_utils import send_validation_email, send_welcome_email # Updated import

login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Adjusted to auth.login

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2], user[3], user[4], user[5], user[6], user[7])
    return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index')) # Corrected to blog.index
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username or email already exists. Please choose different ones.', 'danger')
            conn.close()
            return redirect(url_for('auth.register'))
        hashed_password = generate_password_hash(password)
        api_key = secrets.token_hex(16)
        validation_token = secrets.token_hex(16)
        cursor.execute("INSERT INTO users (username, email, password_hash, api_key, email_validated, validation_token) VALUES (?, ?, ?, ?, ?, ?)",
                       (username, email, hashed_password, api_key, False, validation_token))
        conn.commit()
        conn.close()
        send_validation_email(email, validation_token)
        flash('Registration successful! Please check your email to validate your account.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index')) # Corrected to blog.index
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6], user_data[7])
            if user.email_validated:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Please validate your email before logging in.', 'warning')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/validate_email/<token>')
def validate_email(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE validation_token = ?", (token,))
    user_data = cursor.fetchone()
    if user_data:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6], user_data[7])
        if not user.email_validated:
            cursor.execute("UPDATE users SET email_validated = TRUE, validation_token = NULL WHERE id = ?", (user.id,))
            conn.commit()
            flash('Email validated successfully! You can now log in.', 'success')
            send_welcome_email(user.email)
        else:
            flash('Email already validated.', 'info')
    else:
        flash('Invalid or expired validation token.', 'danger')
    conn.close()
    return redirect(url_for('auth.login'))
