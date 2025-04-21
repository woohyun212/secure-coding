# utils.py
from db import get_db

def get_username_by_id(user_id: str) -> str:
    """
    Given a user_id (UUID), return the corresponding username.
    Returns the user_id itself if no matching username is found.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM user WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return row["username"] if row else user_id