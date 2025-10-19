import pyalex
from pyalex import Works
import requests
import time

pyalex.config.email = "seratosa.ai@gmail.com"


def reconstruct_abstract(inverted_index):
    """
    Reconstructs the abstract from OpenAlex's inverted index format.
    """
    if not inverted_index:
        return None

    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    word_positions.sort()

    return ' '.join([word for pos, word in word_positions])


def get_paper_abstract(paper_id: str = None, title: str = None) -> str:
    """
    Fetches a paper's abstract. It prioritizes title search using OpenAlex.
    If a paper_id is given, it uses the appropriate API (OpenAlex for PMID, Semantic Scholar for S2ID).
    """
    time.sleep(0.5) # Add a delay to avoid rate limiting
    # Prioritize title search via OpenAlex
    if title:
        try:
            base_url = "https://api.openalex.org/works"
            params = {
                "filter": f"title.search:{title}",
                "mailto": pyalex.config.email,
                "per-page": "1"
            }
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            results = response.json().get('results')
            if results:
                work_data = results[0]
                abstract_inverted_index = work_data.get('abstract_inverted_index')
                if abstract_inverted_index:
                    abstract = reconstruct_abstract(abstract_inverted_index)
                    if abstract:
                        return abstract
        except Exception as e:
            print(f"Error fetching from OpenAlex by title: {e}")

    # If title search fails or no title is provided, use paper_id
    if paper_id:
        if paper_id.startswith("PMID:"):
            try:
                pmid = paper_id.replace("PMID:", "")
                work_data = Works().filter(pmid=pmid).get()
                if work_data:
                    abstract_inverted_index = work_data[0].get('abstract_inverted_index')
                    if abstract_inverted_index:
                        abstract = reconstruct_abstract(abstract_inverted_index)
                        if abstract:
                            return abstract
            except Exception as e:
                print(f"Error fetching from OpenAlex by PMID: {e}")
        else:  # Assume Semantic Scholar ID
            try:
                response = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=abstract")
                response.raise_for_status()  # Raise an exception for bad status codes
                data = response.json()
                abstract = data.get('abstract')
                if abstract:
                    return abstract
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from Semantic Scholar: {e}")

    return "Abstract not currently available, please visit publisher site to view"

def get_works_batch(items: list[str], search_type: str) -> list[dict]:
    """
    Fetches a batch of works from OpenAlex.
    `search_type` can be 'pmid', 'doi', 'title.search', or 'openalex_id'.
    """
    if not items:
        return []

    base_url = "https://api.openalex.org/works"
    all_results = []
    batch_size = 20  # Process 20 items at a time to keep the URL length manageable

    # Process items in batches
    for i in range(0, len(items), batch_size):
        batch_items = items[i:i + batch_size]

        # Process IDs/items based on type
        if search_type == 'doi':
            processed_items = [item.replace("https://doi.org/", "") for item in batch_items]
        elif search_type == 'pmid':
            processed_items = [item.replace("PMID:", "") for item in batch_items]
        else:  # For title.search or openalex_id
            processed_items = batch_items

        filter_value = "|".join(processed_items)
        params = {
            "filter": f"{search_type}:{filter_value}",
            "mailto": pyalex.config.email
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            all_results.extend(data.get('results', []))
            time.sleep(3)  # Respect rate limits
        except requests.exceptions.RequestException as e:
            print(f"Error fetching batch from OpenAlex with type {search_type}: {e}")
            # Decide if you want to continue with other batches or stop
            continue  # Continue with the next batch

    return all_results