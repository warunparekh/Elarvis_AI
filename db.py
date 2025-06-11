# db.py
import sqlite3, datetime

DB_PATH = "jarvis_convos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
      CREATE TABLE IF NOT EXISTS convos (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        persona TEXT NOT NULL,
        created TEXT NOT NULL
      )""")
    conn.execute("""
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        convo_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL
      )""")
    conn.commit(); conn.close()

def get_convos():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id,name FROM convos ORDER BY id").fetchall()
    conn.close(); return rows

def create_convo(name, persona):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
      "INSERT INTO convos (name,persona,created) VALUES (?,?,?)",
      (name, persona, datetime.datetime.utcnow().isoformat())
    )
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit(); conn.close(); return cid

def rename_convo(convo_id,new_name):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE convos SET name=? WHERE id=?", (new_name,convo_id))
    conn.commit(); conn.close()

def delete_convo(convo_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE convo_id=?", (convo_id,))
    conn.execute("DELETE FROM convos WHERE id=?",       (convo_id,))
    conn.commit(); conn.close()

def save_message(convo_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
      "INSERT INTO messages (convo_id,role,content,timestamp) VALUES (?,?,?,?)",
      (convo_id, role, content, datetime.datetime.utcnow().isoformat())
    )
    conn.commit(); conn.close()

def load_messages(convo_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
      "SELECT role,content FROM messages WHERE convo_id=? ORDER BY id DESC LIMIT ?",
      (convo_id, limit)
    )
    rows = cur.fetchall(); conn.close()
    return rows[::-1]

def export_chatlog(convo_id):
    msgs = load_messages(convo_id,9999)
    return "\n".join(f"{r}: {c}" for r,c in msgs)

def get_persona(convo_id, default):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT persona FROM convos WHERE id=?", (convo_id,)).fetchone()
    conn.close()
    return row[0] if row else default

def set_persona(convo_id, persona):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE convos SET persona=? WHERE id=?", (persona,convo_id))
    conn.commit(); conn.close()
