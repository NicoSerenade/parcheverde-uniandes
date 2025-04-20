import pytest
from logic_message import send_message, get_conversation
import sqlite3
from db_conn import create_connection

# Fixture modificado para manejar conexión inyectada
# test_messages.py (fixture actualizado)
@pytest.fixture
def setup_db():
    conn = create_connection(':memory:')
    # Activar claves foráneas y crear tablas necesarias
    with conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            )
        ''')
    yield conn
    conn.close()

# Tests actualizados para usar la conexión inyectada
def test_send_valid_message(setup_db):
    """Test envio de mensaje válido entre usuarios"""
    setup_db.execute("DELETE FROM messages;")
    result = send_message(1, 2, "Hola, ¿cómo estás?", conn=setup_db)
    assert result['status'] == 'success'
    assert isinstance(result['message_id'], int)

def test_send_message_invalid_ids(setup_db):
    """Test IDs no enteros"""
    setup_db.execute("DELETE FROM messages;")
    result = send_message("1", 2, "Mensaje inválido", conn=setup_db)
    assert result['status'] == 'error'
    assert "must be integers" in result['message']

def test_send_empty_content(setup_db):
    """Test contenido vacío"""
    setup_db.execute("DELETE FROM messages;")
    result = send_message(1, 2, "", conn=setup_db)
    assert result['status'] == 'error'
    assert "non-empty string" in result['message']

def test_get_conversation_between_users(setup_db):
    """Test obtener conversación con mensajes bidireccionales"""
    setup_db.execute("DELETE FROM messages;")
    send_message(1, 2, "Hola usuario 2", conn=setup_db)
    send_message(2, 1, "Hola usuario 1", conn=setup_db)
    
    result = get_conversation(1, 2, conn=setup_db)
    
    assert result['status'] == 'success'
    assert len(result['data']) == 2
    assert result['data'][0]['content'] == "Hola usuario 2"
    assert result['data'][1]['content'] == "Hola usuario 1"

def test_conversation_ordering(setup_db):
    """Test orden cronológico de mensajes"""
    setup_db.execute("DELETE FROM messages;")
    send_message(1, 2, "Primer mensaje", conn=setup_db)
    send_message(2, 1, "Segundo mensaje", conn=setup_db)
    
    result = get_conversation(1, 2, conn=setup_db)
    messages = result['data']
    
    assert messages[0]['content'] == "Primer mensaje"
    assert messages[1]['content'] == "Segundo mensaje"

def test_empty_conversation(setup_db):
    """Test conversación sin mensajes"""
    setup_db.execute("DELETE FROM messages;")
    result = get_conversation(99, 100, conn=setup_db)
    assert result['status'] == 'success'
    assert len(result['data']) == 0

def test_foreign_key_constraint(setup_db):
    """Test integridad referencial con usuarios inexistentes"""
    setup_db.execute("DELETE FROM messages;")
    with pytest.raises(sqlite3.IntegrityError) as e:
        send_message(999, 1000, "Mensaje a usuarios fantasmas", conn=setup_db)
    assert "FOREIGN KEY constraint failed" in str(e.value)