
'''
This is a helper script to run when new papers are added to the database. It updates all
papers with sci-bert embeddings at once. Can also be run when embedding model is updated etc
'''
import psycopg2
import torch
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv
import os
import multiprocessing
from tqdm import tqdm
import time
import requests

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# SciBERT model name
MODEL_NAME = "allenai/scibert_scivocab_uncased"
MAX_LENGTH = 512  # SciBERT max sequence length

# Global variables for the model and tokenizer in each worker process
model = None
tokenizer = None

def init_worker(model_name):
    """Initializer for each worker process."""
    global model, tokenizer
    print(f"Initializing worker {os.getpid()}...")
    retries = 3
    backoff_factor = 2
    for i in range(retries):
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            print(f"Worker {os.getpid()} initialized.")
            return
        except (requests.exceptions.RequestException, ConnectionError) as e:
            if i < retries - 1:
                sleep_time = backoff_factor ** i
                print(f"Worker {os.getpid()}: Connection error: {e}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Worker {os.getpid()}: Failed to download model after {retries} retries.")
                raise

def process_batch(batch):
    """
    Worker function to process a single batch of papers.
    Uses the globally initialized model and tokenizer.
    """
    global model, tokenizer

    if not tokenizer or not model:
        print(f"Process {os.getpid()}: Model or tokenizer not initialized. Skipping batch.")
        return []

    paper_ids = [p[0] for p in batch]
    abstracts = [p[1] for p in batch]

    inputs = tokenizer(
        abstracts,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)

    last_hidden_state = outputs.last_hidden_state
    attention_mask = inputs["attention_mask"]

    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size())
    sum_embeddings = torch.sum(last_hidden_state * mask_expanded, dim=1)
    sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-9)
    mean_pooled = sum_embeddings / sum_mask

    return [(pid, emb.cpu().numpy().tolist()) for pid, emb in zip(paper_ids, mean_pooled)]

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
        cur.execute("SELECT paper_id, abstract FROM papers WHERE embedding IS NULL")
        paper_list = cur.fetchall()
        print(f"Found {len(paper_list)} papers to process.")

        conn.close()

        if not paper_list:
            print("No papers to process. Exiting.")
            exit()

        # --- Parallel Processing ---
        num_processes = 6
        batch_size = 32  # Adjust based on memory per process
        
        # Create chunks for multiprocessing
        chunks = [paper_list[i:i + batch_size] for i in range(0, len(paper_list), batch_size)]
        
        print(f"Starting parallel processing with {num_processes} cores...")
        with multiprocessing.Pool(processes=num_processes, initializer=init_worker, initargs=(MODEL_NAME,)) as pool:
            # Use tqdm for a progress bar
            results = list(tqdm(pool.imap(process_batch, chunks), total=len(chunks), desc="Generating Embeddings"))

        # Flatten the list of lists
        all_embeddings = [item for sublist in results for item in sublist]
        
        print("\nEmbedding generation complete. Starting database update...")

        # --- Batch Update to DB ---
        update_batch_size = 1000 # How many rows to update in one DB transaction
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        for i in tqdm(range(0, len(all_embeddings), update_batch_size), desc="Updating Database"):
            batch_to_update = all_embeddings[i:i + update_batch_size]
            # The data needs to be in (embedding, paper_id) format for the query
            update_data = [(emb, pid) for pid, emb in batch_to_update]

            try:
                cur.executemany(
                    "UPDATE papers SET embedding = %s WHERE paper_id = %s",
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
