# socketio_handlers.py
import uuid
from flask_socketio import send, emit, join_room
from flask import session
from db import get_db
import re

import time

# In-memory per-user timestamp log for rate limiting (20 msgs per 60s)
message_timestamps = {}  # dict mapping user_id to list of send timestamps


def is_valid_message(message):
    # 메시지 길이 검사
    if len(message) > 500:
        return False, "메시지가 너무 깁니다. 500자 이하로 작성해주세요."

    # 빈 메시지 검사
    if re.match(r'^\s*$', message):
        return False, "빈 메시지를 보낼 수 없습니다."

    # 반복 문자 검사
    if re.search(r'(.)\1{10,}', message):
        return False, "과도한 반복 문자 사용을 자제해주세요."

    # 특수문자 연속 사용 검사
    if re.search(r'[!@#$%^&*()\-_=+\[\]{}|\\:;"\'<>,.?/]{5,}', message):
        return False, "과도한 특수문자 사용을 자제해주세요."

    # 보안 관련 패턴 검사
    if re.search(r'<\s*script|<\s*img|<\s*iframe|javascript:|on\w+\s*=|data\s*:', message, re.IGNORECASE):
        return False, "잠재적인 보안 위험이 감지되었습니다."

    # SQL 인젝션 패턴 검사
    sql_pattern = r'(\b(select|insert|update|delete|drop|alter|create|where)\b.*\b(from|into|table)\b)|(-{2})|(/\*)|(\*/)|(;)'
    if re.search(sql_pattern, message, re.IGNORECASE):
        return False, "잠재적인 보안 위험이 감지되었습니다."

    # 과도한 줄바꿈 검사
    if re.search(r'(\r?\n){5,}', message):
        return False, "과도한 줄바꿈을 자제해주세요."

    return True, "유효한 메시지입니다."

def handle_send_message_event(data):
    """
    Handler for 'send_message' events: assigns
    a unique message_id and broadcasts to all clients.
    """
    # ── manual rate-limit: max 20 messages per 60 seconds per user
    user_id = session.get('user_id')
    now = time.time()
    timestamps = message_timestamps.setdefault(user_id, [])
    # purge timestamps older than 60 seconds
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= 20:
        # rate limit exceeded: notify client then drop
        emit('rate_limit_exceeded', {'message': '메시지 전송 한도를 초과했습니다.'})
        return
    timestamps.append(now)
    message_timestamps[user_id] = timestamps
    content = data.get('message', '')
    # Validate content length and allowed chars
    if not is_valid_message(content)[0]:
        # Invalid message: ignore
        return

    data['message_id'] = str(uuid.uuid4())

    # Determine sender_id
    sender_id = data.get('sender_id') or session.get('user_id')

    # Log broadcast message to database
    db = get_db()
    cursor = db.cursor()
    msg_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO message (id, sender_id, recipient_id, content) VALUES (?, ?, ?, ?)",
        (msg_id, sender_id, None, data.get('message'))
    )
    db.commit()

    send(data, broadcast=True)

def handle_join(data):
    """
    Client joins their personal room for private messages.
    Expects data['user_id'].
    """
    join_room(data['user_id'])

def handle_private_message_event(data):
    """
    Handler for private messages: logs the message to the DB and emits to recipient's room.
    Expects data['sender_id'], data['recipient_id'], and data['message'].
    """
    # ── manual rate-limit: max 20 messages per 60 seconds per user
    user_id = session.get('user_id')
    now = time.time()
    timestamps = message_timestamps.setdefault(user_id, [])
    timestamps = [t for t in timestamps if now - t < 60]
    if len(timestamps) >= 20:
        emit('rate_limit_exceeded', {'message': '메시지 전송 한도를 초과했습니다.'})
        return
    timestamps.append(now)
    message_timestamps[user_id] = timestamps
    content = data.get('message', '')
    if not is_valid_message(content)[0]:
        # ignore
        return

    # Generate unique message ID
    msg_id = str(uuid.uuid4())
    data['message_id'] = msg_id

    # Log private message to database
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO message (id, sender_id, recipient_id, content) VALUES (?, ?, ?, ?)",
        (msg_id, data.get('sender_id'), data.get('recipient_id'), data.get('message'))
    )
    db.commit()

    # Send to recipient only
    emit('private_message', data, room=data.get('recipient_id'))