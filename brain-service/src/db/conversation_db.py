"""
Conversation history storage using SQLite for Loomis Brain Service.
"""
import sqlite3
from typing import List, Tuple
import threading

_DB_PATH = "conversations.db"
_LOCK = threading.Lock()

# Initialize DB
with _LOCK:
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_message(session_id: str, sender: str, message: str):
    with _LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO conversation (session_id, sender, message) VALUES (?, ?, ?)",
            (session_id, sender, message)
        )
        conn.commit()
        conn.close()

def get_history(session_id: str) -> List[Tuple[str, str, str, str]]:
    with _LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT sender, message, timestamp FROM conversation WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = c.fetchall()
        conn.close()
        return rows

def clear_history(session_id: str):
    with _LOCK:
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM conversation WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
