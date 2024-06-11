from flask import g, request
from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.email_verification_token:
            return f(*args, **kwargs)
        else:
            flash("You need to verify your email to access this page.", "warning")
            return redirect(url_for('profile'))
    return decorated_function
