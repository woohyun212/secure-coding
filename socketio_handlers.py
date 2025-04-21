# socketio_handlers.py
import uuid
from flask_socketio import send, emit, join_room
from flask import session
from db import get_db

def handle_send_message_event(data):
    """
    Handler for 'send_message' events: assigns
    a unique message_id and broadcasts to all clients.
    """
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