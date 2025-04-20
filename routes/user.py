from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db
from forms import BioForm
from flask import flash

# Blueprint for user-related routes
user = Blueprint('user', __name__)

@user.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))
    return render_template('index.html')

@user.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    cursor.execute("SELECT * FROM product")
    all_products = cursor.fetchall()
    return render_template('dashboard.html', user=current_user, products=all_products)

@user.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    form = BioForm()
    if form.validate_on_submit():
        cursor.execute("UPDATE user SET bio = ? WHERE id = ?", (form.bio.data, current_user['id']))
        db.commit()
        flash('프로필이 업데이트되었습니다.', 'success')
    return render_template('profile.html', user=current_user, form=form)