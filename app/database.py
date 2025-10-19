
import os
from functools import lru_cache

import dotenv
import psycopg2
from google.oauth2.utils import ClientAuthType
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client, ClientOptions

from dotenv import load_dotenv
import os

from functools import lru_cache
import httpx

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

API_CONFIG = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_KEY": os.getenv("SUPABASE_KEY")
}


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

@lru_cache
def get_python_client():
    # Create httpx client with longer timeout
    http_client = httpx.Client(timeout=120.0)  # 2 minutes

    # Create supabase client (no options parameter)
    supabase: Client = create_client(
        API_CONFIG['SUPABASE_URL'],
        API_CONFIG['SUPABASE_KEY']
    )

    # Set the httpx client on the postgrest session
    supabase.postgrest.session = http_client

    return supabase

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
