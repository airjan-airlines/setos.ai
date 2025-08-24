import numpy as np
from kneed import KneeLocator
from . import database
from .models import Paper

from transformers import AutoTokenizer, AutoModel
import torch

model_name = "allenai/scibert_scivocab_uncased"
_tokenizer = None
_model = None

def _load_model():
    """Lazy load the model and tokenizer"""
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
    if _model is None:
        _model = AutoModel.from_pretrained(model_name)
    return _tokenizer, _model

def get_query_embedding(query: str):
    # Load model lazily
    tokenizer, model = _load_model()
    
    # Tokenize query
    inputs = tokenizer(
        [query],
        padding=True,
        truncation=True,
        max_length=512,  # Match the max length from embedding script
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

    # Return the embedding as a NumPy array
    return mean_pooled.squeeze().cpu().numpy()

# This function now returns a list of tuples, where each tuple is (Paper, similarity_score)
def find_similar_papers(query_embedding: np.ndarray, candidate_pool_size: int = 200):
    conn = database.get_db_connection()
    cur = conn.cursor()

    # The <-> operator gives us cosine distance (0=identical, 2=opposite)
    # We calculate 1 - (distance / 2) to get similarity (1=identical, 0=opposite)
    # and select it as the "similarity" column.
    cur.execute("""
        SELECT
            (1 - (embedding <-> %s :: vector) / 2) as similarity,
            paper_id, title, abstract, authors, year, url, fields_of_study,
            citation_count, reference_count, influential_citation_count
        FROM papers
        WHERE embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT %s
    """, (query_embedding.tolist(), candidate_pool_size))

    papers_data = cur.fetchall()
    cur.close()
    conn.close()

    if not papers_data:
        return []

    similar_papers_with_scores = []
    for row in papers_data:
        paper = Paper(
            paper_id=row[1],
            title=row[2],
            abstract=row[3],
            authors=row[4],
            year=row[5],
            url=row[6],
            fields_of_study=row[7],
            citation_count=row[8],
            reference_count=row[9],
            influential_citation_count=row[10]
        )
        similarity_score = row[0]
        similar_papers_with_scores.append((paper, similarity_score))

    return similar_papers_with_scores

def sequence_papers(papers: list[Paper]):
    # Sequence by year (ascending), then by citation count (descending)
    return sorted(papers, key=lambda p: (p.year or 0, p.citation_count or 0), reverse=False)

def generate_learning_aids(paper: Paper):
    # Placeholder for LLM-based generation of learning aids
    summary = f"This is a summary of the paper '{paper.title}'."
    vocabulary = ["term1", "term2", "term3"]
    quiz = ["question1?", "question2?", "question3?"]
    return summary, vocabulary, quiz

def generate_roadmap(query: str):
    query_embedding = get_query_embedding(query)

    # 1. Get a large candidate pool from the database
    candidate_papers_with_scores = find_similar_papers(query_embedding)
    if not candidate_papers_with_scores:
        return []

    # Unzip the papers and their scores into separate lists
    candidate_papers, similarities = zip(*candidate_papers_with_scores)

    # 2. Find the "knee" to determine the optimal number of papers
    if len(candidate_papers) < 2:
        knee_point = len(candidate_papers)
    else:
        # Note: kneed expects x and y values for the curve
        x_values = range(len(candidate_papers))
        y_values = sorted(similarities, reverse=True) # Ensure similarities are decreasing
        kneedle = KneeLocator(x_values, y_values, curve='convex', direction='decreasing')
        knee_point = kneedle.knee or len(candidate_papers)

    # 3. Select the papers up to the knee point
    final_papers = candidate_papers[:knee_point]

    # 4. Sequence the final, smaller list of papers by year and citation count
    sequenced_papers = sequence_papers(list(final_papers))

    # 5. Generate the final roadmap with learning aids
    roadmap = []
    for paper in sequenced_papers:
        summary, vocabulary, quiz = generate_learning_aids(paper)
        roadmap.append({
            "paper": paper,
            "summary": summary,
            "vocabulary": vocabulary,
            "quiz": quiz
        })

    return roadmap

def get_paper_by_id(paper_id: str) -> Paper:
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT paper_id, title, abstract, authors, year, url, fields_of_study, citation_count, reference_count, influential_citation_count FROM papers WHERE paper_id = %s", (paper_id,))
    paper_data = cur.fetchone()
    cur.close()
    conn.close()

    if not paper_data:
        return None

    return Paper(
        paper_id=paper_data[0],
        title=paper_data[1],
        abstract=paper_data[2],
        authors=paper_data[3],
        year=paper_data[4],
        url=paper_data[5],
        fields_of_study=paper_data[6],
        citation_count=paper_data[7],
        reference_count=paper_data[8],
        influential_citation_count=paper_data[9]
    )

def generate_summary_for_paper(paper: Paper):
    # Placeholder for LLM-based generation of a summary
    return f"This is a summary of the paper '{paper.title}'."

def extract_jargon_for_paper(paper: Paper):
    # Placeholder for an LLM call to extract jargon and definitions from paper.abstract
    # In a real implementation, you would send paper.abstract to an LLM
    # with a prompt like:
    # "You are an expert in [field of study]. Please read the following abstract and identify the 5 most important technical terms or pieces of jargon a student would need to understand. For each term, provide a concise, one-sentence definition."
    
    print(f"--- Pretending to call LLM for paper: {paper.title} ---")
    print(f"Abstract: {paper.abstract[:200]}...")
    print("--- End of pretended LLM call ---")

    return [
        {"term": "Placeholder Jargon 1", "definition": "This is a definition for the first piece of jargon."},
        {"term": "Placeholder Jargon 2", "definition": "This is a definition for the second piece of jargon."}
    ]
