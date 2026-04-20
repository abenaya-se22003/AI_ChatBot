import psycopg2
import os
import time
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


def get_connection():
    for attempt in range(5):
        try:
            conn = psycopg2.connect(
                DB_URL,
                connect_timeout=10,
                sslmode="require"
            )
            return conn
        except Exception as e:
            print(f"DB connection failed (attempt {attempt+1}):", e)
            time.sleep(2)

    raise Exception("❌ Database connection failed after retries")


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Create chat_sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                title VARCHAR(255) DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add session_id column to chats if it doesn't exist
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='chats' AND column_name='session_id'
                ) THEN
                    ALTER TABLE chats ADD COLUMN session_id INTEGER;
                END IF;
            END $$;
        """)

        conn.commit()
        print("✅ Database tables initialized.")
    except Exception as e:
        print("DB Init Error:", e)
    finally:
        cur.close()
        conn.close()


def create_session(user_id, title="New Chat"):
    """Create a new chat session and return its ID."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s) RETURNING id",
            (user_id, title)
        )
        session_id = cur.fetchone()[0]
        conn.commit()
        return session_id
    except Exception as e:
        print("DB Error (create_session):", e)
        return None
    finally:
        cur.close()
        conn.close()


def get_sessions(user_id):
    """Get all chat sessions for a user, newest first."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id, title, created_at FROM chat_sessions WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cur.fetchall()
        return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]
    except Exception as e:
        print("DB Error (get_sessions):", e)
        return []
    finally:
        cur.close()
        conn.close()


def update_session_title(session_id, title):
    """Update the title of a chat session."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE chat_sessions SET title=%s WHERE id=%s",
            (title, session_id)
        )
        conn.commit()
    except Exception as e:
        print("DB Error (update_title):", e)
    finally:
        cur.close()
        conn.close()


def delete_session(session_id):
    """Delete a chat session and all its messages."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM chats WHERE session_id=%s", (session_id,))
        cur.execute("DELETE FROM chat_sessions WHERE id=%s", (session_id,))
        conn.commit()
    except Exception as e:
        print("DB Error (delete_session):", e)
    finally:
        cur.close()
        conn.close()


def save_message(user_id, role, message, session_id=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO chats (user_id, role, message, session_id) VALUES (%s, %s, %s, %s)",
            (user_id, role, message, session_id)
        )
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        cur.close()
        conn.close()


def load_messages(user_id, session_id=None):
    conn = get_connection()
    cur = conn.cursor()

    try:
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

        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception as e:
        print("DB Error (load_messages):", e)
        return []
    finally:
        cur.close()
        conn.close()