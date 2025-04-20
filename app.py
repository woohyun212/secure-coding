# app.py
from flask import Flask, session
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from db import init_db, close_connection
from socketio_handlers import handle_send_message_event

# 변경 후
from routes.auth import auth
from routes.user import user
from routes.product import product
from routes.report import report

from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

app.teardown_appcontext(close_connection)
# socket
socketio.on_event('send_message', handle_send_message_event)

# routes
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(product)
app.register_blueprint(report)






@app.before_request
def make_session_permanent():
    session.permanent = True

if __name__ == '__main__':
    with app.app_context():
        init_db()
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0')
