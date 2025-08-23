
import os

import dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def create_papers_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            authors TEXT[],
            year INT,
            url TEXT,
            fields_of_study TEXT[],
            embedding TEXT,
            citation_count INT,
            reference_count INT,
            influential_citation_count INT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_papers_table()
