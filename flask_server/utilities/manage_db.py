import sqlite3
from flask import g

DATABASE_NAME = "users.db"

def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_NAME)
        g.db.execute("PRAGMA foreign_keys = ON")  
        g.db.row_factory = sqlite3.Row 
    return g.db

def close_connection(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            user_id INTEGER PRIMARY KEY,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES credentials (id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()
