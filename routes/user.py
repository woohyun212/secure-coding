from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db
from forms import BioForm, ChangePasswordForm
from flask import flash
from flask_bcrypt import check_password_hash, generate_password_hash

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
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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