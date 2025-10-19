'''
This is a helper script to add semantic embeddings with sent. transformer to the db
'''
import psycopg2
from dotenv import load_dotenv
import os
import multiprocessing
from tqdm import tqdm
import time
import requests
from sentence_transformers import SentenceTransformer

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def init_worker(model_name):
    """Initializer for each worker process."""
    global model
    print(f"Initializing worker {os.getpid()}...")
    model = SentenceTransformer(model_name)


def process_batch(batch):
    """
    Worker function to process a single batch of papers.
    Uses the globally initialized model.
    """
    global model

    if not model:
        print(f"Process {os.getpid()}: Model not initialized. Skipping batch.")
        return []

    paper_ids = [p[0] for p in batch]
    abstracts = [p[1] for p in batch]

    embeddings = model.encode(abstracts)

    return [(pid, emb.tolist()) for pid, emb in zip(paper_ids, embeddings)]


if __name__ == '__main__':
    # Set start method for multiprocessing
    # Use "fork" for macOS and Linux for better performance with large models
    if multiprocessing.get_start_method(allow_none=True) != 'spawn':
        multiprocessing.set_start_method("spawn", force=True)

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Fetching papers without embeddings...")
        cur.execute("SELECT paper_id, abstract FROM papers WHERE mpnet_embedding IS NULL")
        paper_list = cur.fetchall()
        print(f"Found {len(paper_list)} papers to process.")

        conn.close()

        if not paper_list:
            print("No papers to process. Exiting.")
            exit()

        # --- Parallel Processing ---
        model_name = "all-mpnet-base-v2"
        num_processes = 6
        batch_size = 32  # Adjust based on memory per process

        # Create chunks for multiprocessing
        chunks = [paper_list[i:i + batch_size] for i in range(0, len(paper_list), batch_size)]

        print(f"Starting parallel processing with {num_processes} cores...")
        with multiprocessing.Pool(processes=num_processes, initializer=init_worker, initargs=(model_name,)) as pool:
            # Use tqdm for a progress bar
            results = list(tqdm(pool.imap(process_batch, chunks), total=len(chunks), desc="Generating Embeddings"))

        # Flatten the list of lists
        all_embeddings = [item for sublist in results for item in sublist]

        print("\nEmbedding generation complete. Starting database update...")

        # --- Batch Update to DB ---
        update_batch_size = 100  # How many rows to update in one DB transaction
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for i in tqdm(range(0, len(all_embeddings), update_batch_size), desc="Updating Database"):
            batch_to_update = all_embeddings[i:i + update_batch_size]
            # The data needs to be in (embedding, paper_id) format for the query
            update_data = [(emb, pid) for pid, emb in batch_to_update]

            try:
                cur.executemany(
                    "UPDATE papers SET mpnet_embedding = %s WHERE paper_id = %s",
                    update_data
                )
                conn.commit()
            except psycopg2.Error as e:
                print(f"\nDatabase error during batch update: {e}")
                print("Rolling back transaction...")
                conn.rollback()
                # In a production script, you might want more robust reconnect logic here

        print("Database update complete.")

    except psycopg2.Error as e:
        print(f"A database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
