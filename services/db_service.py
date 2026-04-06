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


def save_message(user_id, role, message):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO chats (user_id, role, message) VALUES (%s, %s, %s)",
            (user_id, role, message)
        )
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        cur.close()
        conn.close()


def load_messages(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT role, message FROM chats WHERE user_id=%s ORDER BY created_at",
        (user_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [{"role": r[0], "content": r[1]} for r in rows]