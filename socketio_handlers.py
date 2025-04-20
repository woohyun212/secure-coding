import uuid
from flask_socketio import send

def handle_send_message_event(data):
    """
    Handler for 'send_message' events: assigns
    a unique message_id and broadcasts to all clients.
    """
    data['message_id'] = str(uuid.uuid4())
    send(data, broadcast=True)