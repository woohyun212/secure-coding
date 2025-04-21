from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from db import get_db

# Blueprint for chat-related routes
chat = Blueprint('chat', __name__, url_prefix='/chat')

@chat.route('/')
def chat_list():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    cursor = db.cursor()
    # Fetch all usernames except the current user
    cursor.execute("SELECT username FROM user WHERE id != ?", (session['user_id'],))
    rows = cursor.fetchall()
    users = [row['username'] for row in rows]
    return render_template('chat_list.html', users=users)

@chat.route('/<username>')
def chat_with(username):
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        flash('존재하지 않는 사용자입니다.', 'danger')
        return redirect(url_for('user.dashboard'))
    recipient_id = row['id']
    return render_template('chat.html', recipient_id=recipient_id, recipient_username=username)

@chat.route('/history/<username>')
def chat_history(username):
    # Return JSON history of messages between current user and recipient
    if 'user_id' not in session:
        return jsonify([])
    current = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return jsonify([])
    recipient_id = row['id']
    cursor.execute(
        """
        SELECT id, sender_id, recipient_id, content, timestamp
        FROM message
        WHERE (sender_id = ? AND recipient_id = ?)
           OR (sender_id = ? AND recipient_id = ?)
        ORDER BY timestamp ASC
        """,
        (current, recipient_id, recipient_id, current)
    )
    rows = cursor.fetchall()
    messages = [
        {
            "id": row["id"],
            "sender_id": row["sender_id"],
            "recipient_id": row["recipient_id"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]
    return jsonify(messages)