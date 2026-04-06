from functools import wraps
from flask_login import current_user
from flask import redirect, flash, url_for

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            flash("Accès refusé", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated