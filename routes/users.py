# users.py
from flask import Blueprint, render_template, redirect, url_for, session, flash
from db import get_db
from forms import BioForm, ChangePasswordForm
from flask_bcrypt import check_password_hash, generate_password_hash
from decorators import login_and_active_required

# Blueprint for user-related routes
user = Blueprint('user', __name__)

@user.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user.dashboard'))
    return render_template('index.html')

@user.route('/dashboard')
@login_and_active_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    cursor.execute("SELECT * FROM product WHERE is_active = 1")
    all_products = cursor.fetchall()
    return render_template('dashboard.html', user=current_user, products=all_products)

@user.route('/profile', methods=['GET', 'POST'])
@login_and_active_required
def profile():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    # existing bio form
    form = BioForm()
    pwd_form = ChangePasswordForm()

    if form.validate_on_submit():
        cursor.execute("UPDATE user SET bio = ? WHERE id = ?", (form.bio.data, current_user['id']))
        db.commit()
        flash('프로필이 업데이트되었습니다.', 'success')
        return redirect(url_for('user.profile'))

    return render_template(
        'profile.html',
        user=current_user,
        form=form,
        pwd_form=pwd_form
    )

@user.route('/change_password', methods=['POST'])
@login_and_active_required
def change_password():
    form = ChangePasswordForm()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    if form.validate_on_submit():
        if not check_password_hash(current_user['password'], form.current_password.data):
            flash('현재 비밀번호가 올바르지 않습니다.', 'danger')
        else:
            new_hashed = generate_password_hash(form.new_password.data).decode('utf-8')
            cursor.execute("UPDATE user SET password = ? WHERE id = ?", (new_hashed, current_user['id']))
            db.commit()
            flash('비밀번호가 변경되었습니다.', 'success')
    return redirect(url_for('user.profile'))

@user.route('/profile/name/<username>')
@login_and_active_required
def profile_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        flash('사용자를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('user.profile'))
    return redirect(url_for('user.view_profile', user_id=row['id']))

@user.route('/profile/<user_id>')
@login_and_active_required
def view_profile(user_id):
    # Fetch the requested user's data
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, bio, is_active FROM user WHERE id = ?",
        (user_id,)
    )
    u = cursor.fetchone()
    if not u:
        flash('사용자를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('user.profile'))
    # Fetch products posted by this user
    cursor.execute(
        "SELECT id, title, description, price, is_active FROM product WHERE seller_id = ?",
        (user_id,)
    )
    products = cursor.fetchall()
    return render_template('view_profile.html', user=u, products=products)