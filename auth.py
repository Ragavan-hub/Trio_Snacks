"""
Authentication and authorization utilities for the Trio Snacks application
"""
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from models import db, User


def get_current_user():
    """Return the currently authenticated User instance, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    """Decorator requiring an authenticated user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not get_current_user():
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator requiring an authenticated admin user."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin():
            if request.path.startswith("/api/"):
                return jsonify({"error": "Administrator privileges required"}), 403
            return redirect(url_for("billing"))
        return f(*args, **kwargs)

    return decorated_function
