import os
import gzip
import requests
import xml.etree.ElementTree as ET
import psycopg2
import torch
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv
import numpy as np
from tqdm import tqdm

# -------------------------
# CONFIG
# -------------------------
PUBMED_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"  # baseline dumps
BATCH_SIZE = 32
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # start cheap

# -------------------------
# DB CONNECTION
# -------------------------
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Ensure table exists
cur.execute("""CREATE TABLE IF NOT EXISTS pubmed_papers(
                pmid BIGINT PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                year INT,
                allmini_embedding VECTOR(768),
                citation_count INT,
                url TEXT,
                authors TEXT[]
                );""")
conn.commit()

# -------------------------
# EMBEDDING MODEL
# -------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)


def embed_texts(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
    return embeddings


# -------------------------
# PROCESSING FUNCTION
# -------------------------
def process_pubmed_file(file_url):
    print(f"Downloading {file_url} ...")
    r = requests.get(file_url, stream=True)
    r.raise_for_status()

    with gzip.open(r.raw, "rt", encoding="utf-8") as f:
        tree = ET.parse(f)
        root = tree.getroot()

        batch_texts, batch_meta = [], []

        for article in tqdm(root.findall(".//PubmedArticle")):
            try:
                pmid = int(article.findtext(".//PMID"))
                title = article.findtext(".//ArticleTitle") or ""
                abstract = " ".join([a.text or "" for a in article.findall(".//Abstract/AbstractText")])
                year = article.findtext(".//PubDate/Year")
                year = int(year) if year and year.isdigit() else None

                if not abstract.strip():
                    continue

                text = f"{title}. {abstract}"
                batch_texts.append(text)
                batch_meta.append((pmid, title, abstract, year))

                if len(batch_texts) >= BATCH_SIZE:
                    embeddings = embed_texts(batch_texts)
                    for (pmid, title, abstract, year), emb in zip(batch_meta, embeddings):
                        cur.execute(
                            "INSERT INTO pubmed_papers (pmid, title, abstract, year, embedding) "
                            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (pmid) DO NOTHING",
                            (pmid, title, abstract, year, emb.tolist())
                        )
                    conn.commit()
                    batch_texts, batch_meta = [], []
            except Exception as e:
                print(f"Error processing article: {e}")

        # flush remainder
        if batch_texts:
            embeddings = embed_texts(batch_texts)
            for (pmid, title, abstract, year), emb in zip(batch_meta, embeddings):
                cur.execute(
                    "INSERT INTO pubmed_papers (pmid, title, abstract, year, embedding) "
                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (pmid) DO NOTHING",
                    (pmid, title, abstract, year, emb.tolist())
                )
            conn.commit()


# -------------------------
# RUN EXAMPLE
# -------------------------
if __name__ == "__main__":
    # Example: process the first baseline file (you can loop through all)
    file_url = PUBMED_BASE_URL + "pubmed23n0001.xml.gz"
    process_pubmed_file(file_url)

    cur.close()
    conn.close()