import sqlite3

conn = sqlite3.connect("papers.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    year_of_publication INTEGER,
    embedding BLOB,
    citations INTEGER
)
""")

conn.commit()
conn.close()