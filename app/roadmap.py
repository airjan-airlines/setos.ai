import numpy as np
from kneed import KneeLocator
from . import database
from .models import Paper
from . import llm

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
    try:
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
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        print("Using fallback embedding method...")
        # Return a simple hash-based embedding as fallback
        # Create a 768-dimensional embedding (matching the model output)
        import hashlib
        hash_obj = hashlib.md5(query.encode())
        hash_bytes = hash_obj.digest()
        
        # Create a 768-dimensional array by repeating and scaling the hash
        embedding = []
        for i in range(768):
            byte_index = i % len(hash_bytes)
            embedding.append(float(hash_bytes[byte_index]) / 255.0)
        
        return np.array(embedding)

# This function now returns a list of tuples, where each tuple is (Paper, similarity_score)
def find_similar_papers(query_embedding: np.ndarray, candidate_pool_size: int = 200):
    try:
        print(f"Attempting to connect to database...")
        conn = database.get_db_connection()
        cur = conn.cursor()
        print(f"Database connection successful")

        # First, let's check if we have any papers at all
        cur.execute("SELECT COUNT(*) FROM papers")
        total_papers = cur.fetchone()[0]
        print(f"Total papers in database: {total_papers}")

        # Check if we have any papers with embeddings
        cur.execute("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL")
        papers_with_embeddings = cur.fetchone()[0]
        print(f"Papers with embeddings: {papers_with_embeddings}")

        if papers_with_embeddings == 0:
            print("No papers with embeddings found in database")
            cur.close()
            conn.close()
            return []

        # The <-> operator gives us cosine distance (0=identical, 2=opposite)
        # We calculate 1 - (distance / 2) to get similarity (1=identical, 0=opposite)
        # and select it as the "similarity" column.
        print(f"Searching for papers with query embedding...")
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
        print(f"Found {len(papers_data)} papers matching query")
        cur.close()
        conn.close()

        if not papers_data:
            print("No papers found matching the query")
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

        print(f"Returning {len(similar_papers_with_scores)} papers with scores")
        return similar_papers_with_scores
    except Exception as e:
        print(f"Database error: {e}")
        return []

def sequence_papers(papers: list[Paper]):
    # Sequence by year (ascending), then by citation count (descending)
    return sorted(papers, key=lambda p: (p.year or 0, p.citation_count or 0), reverse=False)



def generate_learning_aids(paper: Paper):
    try:
        # Generate summary using LLM
        summary = llm.generate_response("summary", paper.abstract)
        
        # Generate jargon/vocabulary using LLM
        jargon_response = llm.generate_response("jargon", paper.abstract)
        
        # Parse jargon response to extract terms (simple parsing)
        vocabulary = []
        if jargon_response:
            # Split by lines and look for terms
            lines = jargon_response.split('\n')
            for line in lines:
                if ':' in line and len(line.strip()) > 0:
                    term = line.split(':')[0].strip()
                    if term and len(term) > 2:  # Basic validation
                        vocabulary.append(term)
        
        # If no vocabulary found, create some basic terms
        if not vocabulary:
            vocabulary = ["Key Concept 1", "Key Concept 2", "Key Concept 3"]
        
        # Generate quiz questions (placeholder for now)
        quiz = [
            f"What is the main contribution of this paper?",
            f"How does this research advance the field?",
            f"What are the key findings presented?"
        ]
        
        return summary, vocabulary, quiz
    except Exception as e:
        print(f"Error generating learning aids for paper {paper.paper_id}: {e}")
        # Fallback to basic content
        summary = f"This paper titled '{paper.title}' presents research in the field."
        vocabulary = ["Research", "Study", "Analysis"]
        quiz = ["What is the main topic?", "What are the key findings?", "How is this research significant?"]
        return summary, vocabulary, quiz

def generate_roadmap(query: str):
    print(f"Generating roadmap for query: '{query}'")
    try:
        print("Getting query embedding...")
        query_embedding = get_query_embedding(query)
        print(f"Query embedding generated, length: {len(query_embedding)}")
        
        # 1. Get a large candidate pool from the database
        print("Searching for similar papers...")
        candidate_papers_with_scores = find_similar_papers(query_embedding)
        
        if not candidate_papers_with_scores:
            print("No papers found in database")
            return []
            
        print(f"Found {len(candidate_papers_with_scores)} candidate papers")
        
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

        print(f"Generated roadmap with {len(roadmap)} papers")
        return roadmap
        
    except Exception as e:
        print(f"Error with embedding/database: {e}")
        return []
        


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
    try:
        return llm.generate_response("summary", paper.abstract)
    except Exception as e:
        print(f"Error generating summary for paper {paper.paper_id}: {e}")
        return f"This is a summary of the paper '{paper.title}'."

def extract_jargon_for_paper(paper: Paper):
    try:
        jargon_response = llm.generate_response("jargon", paper.abstract)
        # Parse the response to extract terms and definitions
        jargon_list = []
        if jargon_response:
            lines = jargon_response.split('\n')
            for line in lines:
                if ':' in line and len(line.strip()) > 0:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        term = parts[0].strip()
                        definition = parts[1].strip()
                        if term and definition:
                            jargon_list.append({"term": term, "definition": definition})
        
        # If no jargon found, return basic terms
        if not jargon_list:
            jargon_list = [
                {"term": "Research", "definition": "Systematic investigation to establish facts or principles."},
                {"term": "Analysis", "definition": "Detailed examination of the elements or structure of something."}
            ]
        
        return jargon_list
    except Exception as e:
        print(f"Error extracting jargon for paper {paper.paper_id}: {e}")
        return [
            {"term": "Technical Term 1", "definition": "This is a definition for the first technical term."},
            {"term": "Technical Term 2", "definition": "This is a definition for the second technical term."}
        ]
