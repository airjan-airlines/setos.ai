import os
import gzip
import json
import requests
import wget
import psycopg2
from psycopg2.extras import execute_values

# ---------------------------
# CONFIGURATION
# ---------------------------

LOCAL_PATH = "./semantic_scholar_db"

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

# Ensure download folder exists
os.makedirs(LOCAL_PATH, exist_ok=True)

# ---------------------------
# STEP 1: Get dataset files
# ---------------------------

latest_release = requests.get('https://api.semanticscholar.org/datasets/v1/release/latest').json()
release_id = latest_release['release_id']

dataset_info = requests.get(
    f'https://api.semanticscholar.org/datasets/v1/release/{release_id}/dataset/abstracts'
).json()

print(dataset_info)

shard_urls = dataset_info['files']

# ---------------------------
# STEP 2: Download shards
# ---------------------------

for url in shard_urls:
    filename = os.path.join(LOCAL_PATH, os.path.basename(url))
    if not os.path.exists(filename):
        print(f"Downloading {url}...")
        wget.download(url, out=filename)
        print(f"\nDownloaded {filename}")
    else:
        print(f"Already downloaded {filename}")

# ---------------------------
# STEP 3: Connect to Postgres
# ---------------------------

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
            CREATE TABLE IF NOT EXISTS papers
            (paper_id TEXT PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                authors TEXT[],
                year INT,
                url TEXT,
                fields_of_study TEXT[])
            """)
conn.commit()

# ---------------------------
# STEP 4: Process shards & insert into DB
# ---------------------------

for shard_file in sorted(os.listdir(LOCAL_PATH)):
    shard_path = os.path.join(LOCAL_PATH, shard_file)
    print(f"Processing {shard_path}...")

    batch = []
    with gzip.open(shard_path, 'rt', encoding='utf-8') as f:
        for line in f:
            paper = json.loads(line)

            # Skip if abstract is missing
            if not paper.get("abstract"):
                continue

            metadata = (
                paper.get("paperId"),
                paper.get("title"),
                paper.get("abstract"),
                [a.get("name") for a in paper.get("authors", [])],
                paper.get("year"),
                paper.get("url"),
                paper.get("fieldsOfStudy"),
                paper.get("citationCount"),
                paper.get("referenceCount"),
                paper.get("influentialCitationCount")
            )
            batch.append(metadata)

            # Insert in batches of 1000 for efficiency
            if len(batch) >= 1000:
                execute_values(cur,
                               "INSERT INTO papers (paper_id,title,abstract,authors,year,url,fields_of_study,citation_count,reference_count,influential_citation_count) VALUES %s ON CONFLICT (paper_id) DO NOTHING",
                               batch)
                conn.commit()
                batch = []

    # Insert remaining papers in batch
    if batch:
        execute_values(cur,
                       "INSERT INTO papers (paper_id,title,abstract,authors,year,url,fields_of_study,citation_count,reference_count,influential_citation_count) VALUES %s ON CONFLICT (paper_id) DO NOTHING",
                       batch)
        conn.commit()

# ---------------------------
# FINISH
# ---------------------------
cur.close()
conn.close()
print("All shards processed and stored in Postgres.")
