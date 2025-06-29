import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    series TEXT DEFAULT NULL,
    content TEXT DEFAULT ''
);
""")
conn.commit()
conn.close()
