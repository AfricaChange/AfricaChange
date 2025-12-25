from flask import session
from functools import wraps

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return "Accès refusé", 403
        return f(*args, **kwargs)
    return wrapper
