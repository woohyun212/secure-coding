import uuid
from flask import Blueprint, render_template, redirect, url_for, session, flash
from forms import RegisterForm, LoginForm
from db import get_db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import generate_password_hash, check_password_hash

# Blueprint for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')
limiter = Limiter(key_func=get_remote_address)

@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute", methods=["POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = ?", (form.username.data,))
        if cursor.fetchone():
            flash('이미 존재하는 사용자명입니다.', 'danger')
            return redirect(url_for('auth.register'))
        user_id = str(uuid.uuid4())
        hashed = generate_password_hash(form.password.data).decode('utf-8')
        cursor.execute(
            "INSERT INTO user (id, username, password) VALUES (?, ?, ?)",
            (user_id, form.username.data, hashed)
        )
        db.commit()
        flash('회원가입 완료.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (form.username.data,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], form.password.data):
            session['user_id'] = user['id']
            flash('로그인 성공!', 'success')
            return redirect(url_for('user.dashboard'))
        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))