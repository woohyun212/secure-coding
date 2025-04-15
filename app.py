# app.py
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_socketio import SocketIO, send
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from forms import RegisterForm, LoginForm, BioForm, ProductForm, ReportForm
from datetime import timedelta, datetime  # 추가된 import
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os

load_dotenv()
login_failures = {}  # key = IP, value = {"count": int, "last_attempt": datetime}

# app 설정 이후에 추가
app = Flask(__name__)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 기본적으로 True 지만 명시적 설정
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'
# app.config['WTF_CSRF_TIME_LIMIT'] = 300 # CSRF 토큰 5분 후 만료
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.permanent_session_lifetime = timedelta(minutes=30)




@app.before_request
def make_session_permanent():
    session.permanent = True


DATABASE = 'market.db'


# 데이터베이스 연결 관리: 요청마다 연결 생성 후 사용, 종료 시 close
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # 결과를 dict처럼 사용하기 위함
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# 테이블 생성 (최초 실행 시에만)
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # 사용자 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bio TEXT
            )
        """)
        # 상품 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                seller_id TEXT NOT NULL
            )
        """)
        # 신고 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report (
                id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                reason TEXT NOT NULL
            )
        """)
        db.commit()


# 기본 라우트
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# 회원가입
@limiter.limit("3 per minute", methods=["POST"])
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('register'))

        user_id = str(uuid.uuid4())
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')  # 해시 적용 포함
        cursor.execute("INSERT INTO user (id, username, password) VALUES (?, ?, ?)",
                       (user_id, username, hashed_pw))
        db.commit()
        flash('회원가입이 완료되었습니다. 로그인 해주세요.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    client_ip = request.remote_addr
    now = datetime.now()

    # get or initialize failure info
    failure = login_failures.get(client_ip, {"count": 0, "last_attempt": now})
    elapsed = (now - failure["last_attempt"]).total_seconds()

    # reset failure count after 5 minutes
    if elapsed > 300:
        failure = {"count": 0, "last_attempt": now}

    # block login if 5 or more failed attempts within 5 minutes
    if request.method == "POST" and failure["count"] >= 5:
        flash('5회 이상 로그인 실패로 잠시 차단되었습니다. 잠시 후 다시 시도해주세요.')
        return redirect(url_for('login'))

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('로그인 성공!')
            login_failures.pop(client_ip, None)  # Reset failure count on successful login
            return redirect(url_for('dashboard'))
        else:
            failure["count"] += 1
            failure["last_attempt"] = now
            login_failures[client_ip] = failure
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('로그아웃되었습니다.')
    return redirect(url_for('index'))


# 대시보드: 사용자 정보와 전체 상품 리스트 표시
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    cursor = db.cursor()
    # 현재 사용자 조회
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    # 모든 상품 조회
    cursor.execute("SELECT * FROM product")
    all_products = cursor.fetchall()
    return render_template('dashboard.html', products=all_products, user=current_user)


# 프로필 페이지: bio 업데이트 가능
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = BioForm()
    db = get_db()
    cursor = db.cursor()
    if form.validate_on_submit():
        bio = form.bio.data
        cursor.execute("UPDATE user SET bio = ? WHERE id = ?", (bio, session['user_id']))
        db.commit()
        flash('프로필이 업데이트되었습니다.')
        return redirect(url_for('profile'))
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    current_user = cursor.fetchone()
    return render_template('profile.html', user=current_user, form=form)


# 상품 등록
@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = ProductForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        price = form.price.data
        db = get_db()
        cursor = db.cursor()
        product_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO product (id, title, description, price, seller_id) VALUES (?, ?, ?, ?, ?)",
            (product_id, title, description, price, session['user_id'])
        )
        db.commit()
        flash('상품이 등록되었습니다.')
        return redirect(url_for('dashboard'))
    return render_template('new_product.html', form=form)


# 상품 상세보기
@app.route('/product/<product_id>')
def view_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM product WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        flash('상품을 찾을 수 없습니다.')
        return redirect(url_for('dashboard'))
    # 판매자 정보 조회
    cursor.execute("SELECT * FROM user WHERE id = ?", (product['seller_id'],))
    seller = cursor.fetchone()
    return render_template('view_product.html', product=product, seller=seller)


# 신고하기
@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = ReportForm()
    if form.validate_on_submit():
        target_id = form.target_id.data
        reason = form.reason.data
        db = get_db()
        cursor = db.cursor()
        report_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO report (id, reporter_id, target_id, reason) VALUES (?, ?, ?, ?)",
            (report_id, session['user_id'], target_id, reason)
        )
        db.commit()
        flash('신고가 접수되었습니다.')
        return redirect(url_for('dashboard'))
    return render_template('report.html', form=form)


# 실시간 채팅: 클라이언트가 메시지를 보내면 전체 브로드캐스트
@socketio.on('send_message')
def handle_send_message_event(data):
    data['message_id'] = str(uuid.uuid4())
    send(data, broadcast=True)


if __name__ == '__main__':
    init_db()  # 앱 컨텍스트 내에서 테이블 생성
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0')
