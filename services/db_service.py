import psycopg2
import os
import time
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Return a raw psycopg2 connection. Caller is responsible for commit/close. Retries up to 5 times."""
    for attempt in range(5):
        try:
            return psycopg2.connect(DB_URL, connect_timeout=10, sslmode="require")
        except Exception as e:
            if attempt == 4:
                raise Exception("Database connection failed after retries")
            time.sleep(2)


@contextmanager
def _get_cursor():
    """Get a DB cursor with auto-close. Retries connection up to 5 times."""
    conn = None
    for attempt in range(5):
        try:
            conn = psycopg2.connect(DB_URL, connect_timeout=10, sslmode="require")
            break
        except Exception as e:
            if attempt == 4:
                raise Exception("Database connection failed after retries")
            time.sleep(2)

    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with _get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                title VARCHAR(255) DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='chats' AND column_name='session_id'
                ) THEN
                    ALTER TABLE chats ADD COLUMN session_id INTEGER;
                END IF;
            END $$;
        """)


def create_session(user_id, title="New Chat"):
    """Create a new chat session and return its ID."""
    with _get_cursor() as cur:
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
            (user_id, title)
        )
        return cur.fetchone()[0]


def get_sessions(user_id):
    """Get all chat sessions for a user, newest first."""
    with _get_cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at FROM chat_sessions WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,)
        )
        return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in cur.fetchall()]


def update_session_title(session_id, title):
    """Update the title of a chat session."""
    with _get_cursor() as cur:
        cur.execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))


def delete_session(session_id):
    """Delete a chat session and all its messages."""
    with _get_cursor() as cur:
        cur.execute("DELETE FROM chats WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM chat_sessions WHERE id=%s", (session_id,))


def save_message(user_id, role, message, session_id=None):
    """Save a chat message to the database."""
    with _get_cursor() as cur:
        cur.execute(
            "INSERT INTO chats (user_id, role, message, session_id) VALUES (%s, %s, %s, %s)",
            (user_id, role, message, session_id)
        )


def load_messages(user_id, session_id=None):
    """Load all messages for a session."""
    with _get_cursor() as cur:
        if session_id:
            cur.execute(
                "SELECT role, message FROM chats WHERE user_id=%s AND session_id=%s ORDER BY created_at",
                (user_id, session_id)
            )
        else:
            cur.execute(
                "SELECT role, message FROM chats WHERE user_id=%s AND session_id IS NULL ORDER BY created_at",
                (user_id,)
            )
        return [{"role": r[0], "content": r[1]} for r in cur.fetchall()]