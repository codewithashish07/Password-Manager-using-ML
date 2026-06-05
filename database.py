import sqlite3

def init_db():
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            strength_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_password(site, username, encrypted_pw, strength_score):
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO passwords (site, username, encrypted_password, strength_score) VALUES (?,?,?,?)",
        (site, username, encrypted_pw, strength_score)
    )
    conn.commit()
    conn.close()

def get_all_passwords():
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, site, username, encrypted_password, strength_score FROM passwords")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_password(record_id):
    conn = sqlite3.connect("passwords.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passwords WHERE id=?", (record_id,))
    conn.commit()
    conn.close()