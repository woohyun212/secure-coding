# decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash, abort
from db import get_db

def login_and_active_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Check login
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        # Fetch user record
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_active FROM user WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or row['is_active'] == 0:
            flash('휴면 계정입니다. 서비스 이용이 제한되었습니다.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Ensure user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        # Fetch admin flag
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_admin FROM user WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or row['is_admin'] == 0:
            abort(403)
        return f(*args, **kwargs)
    return wrapper