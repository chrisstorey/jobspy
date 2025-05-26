import os
from flask_mail import Mail, Message
from flask import current_app, url_for

# Initialize Mail object without app
mail = Mail()

def configure_mail(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@example.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-email-password')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'your-email@example.com')
    mail.init_app(app) # Initialize mail with app settings here

def send_validation_email(email, token):
    subject = "Validate Your Email Address"
    validation_url = url_for('auth.validate_email', token=token, _external=True)
    body = f"Please click the following link to validate your email address: {validation_url}"
    msg = Message(subject, recipients=[email], body=body, sender=current_app.config.get('MAIL_DEFAULT_SENDER'))
    try:
        mail.send(msg)
        current_app.logger.info(f"Validation email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send validation email to {email}: {e}")

def send_welcome_email(email):
    subject = "Welcome to Our Job Search App!"
    body = "Welcome to our platform! We are excited to have you."
    msg = Message(subject, recipients=[email], body=body, sender=current_app.config.get('MAIL_DEFAULT_SENDER'))
    try:
        mail.send(msg)
        current_app.logger.info(f"Welcome email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email to {email}: {e}")
