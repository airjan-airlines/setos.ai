import numpy as np
from kneed import KneeLocator
from . import database
from .models import Paper
from . import llm
from . import open_alex

from transformers import AutoTokenizer, AutoModel
import torch

from .open_alex import get_paper_abstract
from supabase import Client

model_name = "allenai/scibert_scivocab_uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_query_embedding(query: str):
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

    mean_pooled = mean_pooled / mean_pooled.norm(p=2, dim=1, keepdim=True)
    # Return the embedding as a NumPy array
    return mean_pooled.squeeze().cpu().numpy()

def find_similar_papers(query_embedding: np.ndarray, client: Client, candidate_pool_size: int = 200):
    client.rpc("set_config", {"parameter": "statement_timeout", "value": "60000"})
    response = client.rpc("match_papers",
               {
                   'query_embedding': query_embedding.tolist(),
                   'match_count': candidate_pool_size,
                   'match_threshold': 0
    }).execute()

    all_papers_with_scores = []
    papers_needing_abstracts = []
    for paper_dict in response.data:
        paper = Paper(
            paper_id=paper_dict['paper_id'], title=paper_dict['title'], abstract=None,
            authors=paper_dict['authors'], year=paper_dict['year'],
            url=paper_dict['url'], fields_of_study=paper_dict['fields_of_study'],
            citation_count=paper_dict['citation_count']
        )
        score = paper_dict['similarity']
        all_papers_with_scores.append((paper, score))
    '''
    # Step 2: Batch fetch abstracts for papers with PMIDs
    pmid_papers = [(p, s) for p, s in papers_needing_abstracts if p.paper_id and p.paper_id.startswith('PMID:')]
    if pmid_papers:
        pmids = [p.paper_id for p, s in pmid_papers]
        works_data = open_alex.get_works_batch(pmids, search_type='pmid')

        abstracts_by_pmid = {
            work['ids']['pmid'].split('/')[-1]: open_alex.reconstruct_abstract(work.get('abstract_inverted_index'))
            for work in works_data if work.get('abstract_inverted_index') and work.get('ids', {}).get('pmid')
        }

        remaining_after_pmid = []
        for paper, score in pmid_papers:
            pmid_val = paper.paper_id.replace("PMID:", "")
            abstract = abstracts_by_pmid.get(pmid_val)
            if abstract:
                paper.abstract = abstract
                all_papers_with_scores.append((paper, score))
            else:
                remaining_after_pmid.append((paper, score))

        papers_needing_abstracts = remaining_after_pmid + [(p, s) for p, s in papers_needing_abstracts if
                                                           not (p.paper_id and p.paper_id.startswith('PMID:'))]

    # Step 3: Batch fetch for the rest by title
    if papers_needing_abstracts:
        titles = [p.title for p, s in papers_needing_abstracts if p.title]
        works_data = open_alex.get_works_batch(titles, search_type='title.search')

        abstracts_by_title = {
            work['title']: open_alex.reconstruct_abstract(work.get('abstract_inverted_index'))
            for work in works_data if work.get('abstract_inverted_index') and work.get('title')
        }

        remaining_after_title = []
        for paper, score in papers_needing_abstracts:
            abstract = abstracts_by_title.get(paper.title)
            if abstract:
                paper.abstract = abstract
                all_papers_with_scores.append((paper, score))
            else:
                remaining_after_title.append((paper, score))

        papers_needing_abstracts = remaining_after_title

    # Step 4: Fallback to individual search for any remaining papers
    if papers_needing_abstracts:
        for paper, score in papers_needing_abstracts:
            paper.abstract = get_paper_abstract(paper_id=paper.paper_id, title=paper.title)
            all_papers_with_scores.append((paper, score))
    '''

    # Final sort and return
    all_papers_with_scores.sort(key=lambda x: x[1], reverse=True)
    return all_papers_with_scores
    #rewrite ends here
    '''
    #og method
    conn = database.get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            (1 - (embedding <=> %s :: vector)) as similarity,
            paper_id, title, abstract, authors, year, url, fields_of_study,
            citation_count, reference_count, influential_citation_count
        FROM papers
        WHERE (embedding IS NOT NULL AND citation_count IS NOT NULL)
        ORDER BY similarity DESC
        LIMIT %s
    """, (query_embedding.tolist(), candidate_pool_size))

    papers_data = cur.fetchall()
    cur.close()
    conn.close()

    if not papers_data:
        return []

    # Step 1: Initial processing and separation
    all_papers_with_scores = []
    papers_needing_abstracts = []
    for row in papers_data:
        paper = Paper(
            paper_id=row[1], title=row[2], abstract=row[3], authors=row[4],
            year=row[5], url=row[6], fields_of_study=row[7], citation_count=row[8]
        )
        score = row[0]
        if paper.abstract:
            all_papers_with_scores.append((paper, score))
        else:
            papers_needing_abstracts.append((paper, score))

    if not papers_needing_abstracts:
        all_papers_with_scores.sort(key=lambda x: x[1], reverse=True)
        return all_papers_with_scores

    # Step 2: Batch fetch abstracts for papers with PMIDs
    pmid_papers = [(p, s) for p, s in papers_needing_abstracts if p.paper_id and p.paper_id.startswith('PMID:')]
    if pmid_papers:
        pmids = [p.paper_id for p, s in pmid_papers]
        works_data = open_alex.get_works_batch(pmids, search_type='pmid')
        
        abstracts_by_pmid = {
            work['ids']['pmid'].split('/')[-1]: open_alex.reconstruct_abstract(work.get('abstract_inverted_index'))
            for work in works_data if work.get('abstract_inverted_index') and work.get('ids', {}).get('pmid')
        }

        remaining_after_pmid = []
        for paper, score in pmid_papers:
            pmid_val = paper.paper_id.replace("PMID:", "")
            abstract = abstracts_by_pmid.get(pmid_val)
            if abstract:
                paper.abstract = abstract
                all_papers_with_scores.append((paper, score))
            else:
                remaining_after_pmid.append((paper, score))
        
        papers_needing_abstracts = remaining_after_pmid + [(p, s) for p, s in papers_needing_abstracts if not (p.paper_id and p.paper_id.startswith('PMID:'))]

    # Step 3: Batch fetch for the rest by title
    if papers_needing_abstracts:
        titles = [p.title for p, s in papers_needing_abstracts if p.title]
        works_data = open_alex.get_works_batch(titles, search_type='title.search')

        abstracts_by_title = {
            work['title']: open_alex.reconstruct_abstract(work.get('abstract_inverted_index'))
            for work in works_data if work.get('abstract_inverted_index') and work.get('title')
        }

        remaining_after_title = []
        for paper, score in papers_needing_abstracts:
            abstract = abstracts_by_title.get(paper.title)
            if abstract:
                paper.abstract = abstract
                all_papers_with_scores.append((paper, score))
            else:
                remaining_after_title.append((paper, score))
        
        papers_needing_abstracts = remaining_after_title

    # Step 4: Fallback to individual search for any remaining papers
    if papers_needing_abstracts:
        for paper, score in papers_needing_abstracts:
            paper.abstract = get_paper_abstract(paper_id=paper.paper_id, title=paper.title)
            all_papers_with_scores.append((paper, score))

    # Final sort and return
    all_papers_with_scores.sort(key=lambda x: x[1], reverse=True)
    return all_papers_with_scores
    '''

def sequence_papers(papers: list[Paper]):
    # Sequence by year (ascending), then by citation count (descending)
    return sorted(papers, key=lambda p: (p.year or 0, -(p.citation_count or 0)))

def generate_learning_aids(paper: Paper):
    # Placeholder for LLM-based generation of learning aids
    summary = f"This is a summary of the paper '{paper.title}'."
    vocabulary = ["term1", "term2", "term3"]
    quiz = ["question1?", "question2?", "question3?"]
    return summary, vocabulary, quiz

def generate_roadmap(query: str, client: Client):
    improved_query = llm.generate_response("expand_query", query)
    print(f"Original query: '{query}' | Improved query: '{improved_query}'")
    query_embedding = get_query_embedding(improved_query)

    # 1. Get a large candidate pool from the database
    candidate_papers_with_scores = find_similar_papers(query_embedding, client)
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
    #is this necessary? Going to cook our api requests.
    for paper in sequenced_papers:
        summary, vocabulary, quiz = generate_learning_aids(paper)
        roadmap.append({
            "paper": paper,
            "summary": summary,
            "vocabulary": vocabulary,
            "quiz": quiz
        })

    return roadmap

def get_paper_by_id(paper_id: str, client: Client) -> Paper:
    response = (client.table("papers")
        .select("paper_id", "title", "authors", "year", "url", "fields_of_study", "citation_count")
        .eq("paper_id", paper_id)
        .execute()
    )

    if not response.data:
        return None

    paper_data = response.data[0]

    abstract = get_paper_abstract(paper_id = paper_data["paper_id"], title = paper_data["title"])

    return Paper(
        paper_id=paper_data["paper_id"],
        title=paper_data["title"],
        abstract=abstract,
        authors=paper_data["authors"],
        year=paper_data["year"],
        url=paper_data["url"],
        fields_of_study=paper_data["fields_of_study"],
        citation_count=paper_data["citation_count"]
    )

    '''
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT paper_id, title, authors, year, url, fields_of_study, citation_count FROM papers WHERE paper_id = %s",
        (paper_id,))
    paper_data = cur.fetchone()

    # query the openalex api
    abstract = get_paper_abstract(paper_id=paper_data[0], title=paper_data[1])

    cur.close()
    conn.close()
    '''