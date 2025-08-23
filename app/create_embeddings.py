'''
This is a helper script to run when new papers are added to the database. It updates all
papers with sci-bert embeddings at once. Can also be run when embedding model is updated etc
'''
from transformers import AutoTokenizer, AutoModel

import psycopg2
import json
import torch

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

if __name__ == '__main__':
    # SciBERT uncased model from AllenAI (uncased better for user input
    model_name = "allenai/scibert_scivocab_uncased"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    #get papers without embeddings
    cur.execute("""
    SELECT paper_id, abstract FROM papers WHERE embedding IS NULL
    """)

    paper_list = cur.fetchall()

    embedding_dict = {}
    batch_size = 16  # adjust to fit memory
    max_length = 512  # SciBERT max sequence length

    # --- Process abstracts in batches ---
    for i in range(0, len(paper_list), batch_size):
        batch = paper_list[i:i + batch_size]
        paper_ids = [p[0] for p in batch]
        abstracts = [p[1] for p in batch]

        # Tokenize batch with truncation
        inputs = tokenizer(
            abstracts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )

        # Forward pass
        with torch.no_grad():
            outputs = model(**inputs)

        last_hidden_state = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]

        # Mean pooling
        mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size())
        sum_embeddings = torch.sum(last_hidden_state * mask_expanded, dim=1)
        sum_mask = mask_expanded.sum(dim=1).clamp(min=1e-9)
        mean_pooled = sum_embeddings / sum_mask

        # Convert to Python lists and store in dict
        for pid, emb in zip(paper_ids, mean_pooled):
            embedding_dict[pid] = emb.cpu().numpy()

    # --- Batch update in one go ---
    update_data = [(embedding, pid) for pid, embedding in embedding_dict.items()]
    cur.executemany("""
    UPDATE papers SET embedding = %s WHERE paper_id = %s 
                    """, update_data)

    conn.commit()
    conn.close()