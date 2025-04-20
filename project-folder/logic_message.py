import sqlite3
from db_conn import create_connection


def init_message_table(conn=None):
    if conn is None:
        conn = create_connection()
    """
    Create the `messages` table if it doesn't exist.

    Schema:
        - message_id:   INTEGER PRIMARY KEY AUTOINCREMENT
        - sender_id:    INTEGER NOT NULL (FK users.user_id)
        - receiver_id:  INTEGER NOT NULL (FK users.user_id)
        - content:      TEXT    NOT NULL
        - timestamp:    TEXT    DEFAULT CURRENT_TIMESTAMP
    """
    conn = create_connection()

    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating messages table: {e}")
    finally:
        conn.close()

# Ensure the messages table exists when this module is imported
init_message_table()


def send_message(sender_id, receiver_id, content, conn=None):
    if conn is None:
        conn = create_connection()
    """
    Send a message from one user to another by inserting it into the messages table.

    Args:
        sender_id (int):    ID of the user sending the message.
        receiver_id (int):  ID of the user receiving the message.
        content (str):      Text content of the message.

    Returns:
        dict: A dictionary with keys:
            - status (str): "success" or "error".
            - message (str): Human-readable result or error description.
            - message_id (int, optional): ID of the stored message on success.
    """
    # Ensure table exists
    init_message_table()

    # Validate input types
    if not isinstance(sender_id, int) or not isinstance(receiver_id, int):
        return {"status": "error", "message": "Sender and receiver IDs must be integers."}
    if not content or not isinstance(content, str):
        return {"status": "error", "message": "Content must be a non-empty string."}

    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
            (sender_id, receiver_id, content)
        )
        conn.commit()
        msg_id = cursor.lastrowid
        return {"status": "success", "message": "Message sent successfully.", "message_id": msg_id}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error sending message: {e}"}
    finally:
        conn.close()


def get_conversation(user1_id, user2_id, conn=None):
    if conn is None:
        conn = create_connection()
    """
    Retrieve all messages exchanged between two users, ordered chronologically.

    Args:
        user1_id (int): ID of the first user.
        user2_id (int): ID of the second user.

    Returns:
        dict: A dictionary with keys:
            - status (str): "success" or "error".
            - data (list of dict): On success, a list of messages with fields:
                * message_id, sender_id, receiver_id, content, timestamp.
            - message (str, optional): Error description on failure.
    """
    # Ensure table exists
    init_message_table()

    # Validate input types
    if not isinstance(user1_id, int) or not isinstance(user2_id, int):
        return {"status": "error", "message": "User IDs must be integers."}

    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT message_id, sender_id, receiver_id, content, timestamp
            FROM messages
            WHERE (sender_id = ? AND receiver_id = ?)
               OR (sender_id = ? AND receiver_id = ?)
            ORDER BY timestamp ASC
            ''',
            (user1_id, user2_id, user2_id, user1_id)
        )
        rows = cursor.fetchall()
        conversation = []
        for row in rows:
            conversation.append({
                "message_id": row[0],
                "sender_id": row[1],
                "receiver_id": row[2],
                "content": row[3],
                "timestamp": row[4]
            })
        return {"status": "success", "data": conversation}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error retrieving conversation: {e}"}
    finally:
        conn.close()
