
import os
import time
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
import random

# --------------------------- 
# CONFIGURATION
# --------------------------- 

# --- Search Parameters ---
# A list of queries to build a diverse database
SEARCH_QUERIES = [
    "CRISPR gene editing",
    "large language model pre-training",
    "carbon capture and storage",
    "behavioral economics and public policy",
    "quantum entanglement applications",
    "graphene synthesis and applications",
    "cognitive behavioral therapy for depression",
    "supply chain resilience post-pandemic",
    "Roman Empire trade routes",
    "dark matter detection experiments"
]

queries = [
    # STEM - Computer Science & AI
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "natural language processing",
    "computer vision",
    "reinforcement learning",
    "robotics",
    "human-computer interaction",
    "computer graphics",
    "quantum computing",

    # STEM - Mathematics & Statistics
    "algebra",
    "calculus",
    "probability theory",
    "statistics",
    "number theory",
    "geometry",
    "topology",
    "mathematical modeling",
    "applied mathematics",
    "game theory",

    # STEM - Physics
    "quantum mechanics",
    "relativity",
    "astrophysics",
    "nuclear physics",
    "particle physics",
    "thermodynamics",
    "statistical mechanics",
    "optics",
    "plasma physics",
    "condensed matter physics",

    # STEM - Chemistry
    "organic chemistry",
    "inorganic chemistry",
    "physical chemistry",
    "analytical chemistry",
    "biochemistry",
    "polymer chemistry",
    "theoretical chemistry",
    "green chemistry",
    "materials chemistry",
    "nanochemistry",

    # STEM - Biology
    "genetics",
    "molecular biology",
    "evolutionary biology",
    "ecology",
    "cell biology",
    "microbiology",
    "immunology",
    "neuroscience",
    "developmental biology",
    "synthetic biology",

    # STEM - Engineering
    "electrical engineering",
    "mechanical engineering",
    "civil engineering",
    "aerospace engineering",
    "chemical engineering",
    "biomedical engineering",
    "materials engineering",
    "industrial engineering",
    "nuclear engineering",
    "systems engineering",

    # Social Sciences
    "psychology",
    "cognitive science",
    "sociology",
    "anthropology",
    "political science",
    "economics",
    "international relations",
    "education",
    "law",
    "criminology",

    # Humanities
    "history",
    "philosophy",
    "literature",
    "linguistics",
    "religious studies",
    "art history",
    "musicology",
    "classics",
    "cultural studies",
    "ethics",

    # Interdisciplinary / Applied
    "environmental science",
    "climate change",
    "public health",
    "epidemiology",
    "bioinformatics",
    "genomics",
    "health policy",
    "urban studies",
    "media studies",
    "communication studies",

    # Emerging & Broad Impact Fields
    "artificial general intelligence",
    "cybersecurity",
    "blockchain",
    "internet of things",
    "data science",
    "precision medicine",
    "space exploration",
    "renewable energy",
    "nanotechnology",
    "social media studies"
]

extra_queries = [
    # Methods & Tools
    "Bayesian inference",
    "Monte Carlo simulation",
    "finite element analysis",
    "agent-based modeling",
    "network analysis",
    "computational complexity",
    "data visualization",
    "survey methodology",
    "ethnography",
    "randomized controlled trials",

    # Computer Science / AI Subfields
    "federated learning",
    "multimodal machine learning",
    "knowledge graphs",
    "explainable AI",
    "adversarial machine learning",
    "AI in healthcare",
    "AI for drug discovery",
    "neuromorphic computing",
    "edge computing",
    "quantum machine learning",

    # Mathematics & Statistics Subfields
    "linear algebra",
    "differential equations",
    "dynamical systems",
    "fractal geometry",
    "stochastic processes",
    "operations research",
    "optimization theory",
    "statistical learning",
    "information theory",
    "category theory",

    # Physics Subfields
    "string theory",
    "gravitational waves",
    "cosmology",
    "quantum field theory",
    "superconductivity",
    "fluid dynamics",
    "biophysics",
    "accelerator physics",
    "chaos theory",
    "nonlinear dynamics",

    # Chemistry Subfields
    "supramolecular chemistry",
    "catalysis",
    "photochemistry",
    "electrochemistry",
    "medicinal chemistry",
    "computational chemistry",
    "chemical engineering materials",
    "spectroscopy",
    "surface chemistry",
    "crystallography",

    # Biology & Medicine Subfields
    "cancer genomics",
    "stem cell biology",
    "epigenetics",
    "proteomics",
    "metabolomics",
    "microbiome research",
    "structural biology",
    "aging biology",
    "neurodegenerative diseases",
    "gene therapy",

    # Engineering & Technology Subfields
    "control systems",
    "signal processing",
    "renewable energy engineering",
    "biomedical imaging",
    "tissue engineering",
    "nanomaterials",
    "additive manufacturing",
    "photonics",
    "microelectronics",
    "environmental engineering",

    # Psychology & Cognitive Science Subfields
    "developmental psychology",
    "social psychology",
    "educational psychology",
    "decision-making",
    "behavioral neuroscience",
    "affective science",
    "psycholinguistics",
    "memory research",
    "consciousness studies",
    "computational psychiatry",

    # Social Sciences / Policy
    "migration studies",
    "gender studies",
    "social network analysis",
    "comparative politics",
    "public administration",
    "conflict resolution",
    "global governance",
    "economic history",
    "labor economics",
    "health economics",

    # Humanities Extensions
    "digital humanities",
    "media archaeology",
    "critical theory",
    "comparative literature",
    "semiotics",
    "philosophy of science",
    "metaphysics",
    "epistemology",
    "political philosophy",
    "aesthetics",

    # Interdisciplinary / Global Challenges
    "pandemic preparedness",
    "food security",
    "water resources management",
    "sustainable agriculture",
    "biodiversity conservation",
    "renewable energy storage",
    "disaster risk reduction",
    "artificial ecosystems",
    "urban resilience",
    "planetary health"
]

# The fields to retrieve from the Semantic Scholar API
REQUEST_FIELDS = "paperId,title,abstract,authors,year,url,fieldsOfStudy,citationCount,referenceCount,influentialCitationCount"

# Max number of papers to retrieve PER QUERY
MAX_RESULTS_PER_QUERY = 150

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

# --------------------------- 
# DATABASE SETUP
# --------------------------- 

def setup_database():
    """Connects to Postgres and creates the papers table if it doesn't exist."""
    print("Setting up database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    return conn

# --------------------------- 
# SEMANTIC SCHOLAR API FETCHER
# --------------------------- 

def fetch_papers_from_api(query, fields, max_results):
    """
    Fetches papers from the Semantic Scholar API with pagination and exponential backoff.
    Yields batches of papers.
    """
    print(f"Starting to fetch papers for query: '{query}'")
    url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    params = {"query": query, "fields": fields}
    headers = {"Accept": "application/json"}
    
    results_retrieved = 0
    
    while results_retrieved < max_results:
        retries = 0
        max_retries = 5
        
        while retries < max_retries:
            try:
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

                data = response.json()
                papers = data.get("data", [])
                
                if not papers:
                    print("No more papers found.")
                    return

                yield papers
                
                results_retrieved += len(papers)
                
                # Check for next token for pagination
                next_token = data.get("token")
                if not next_token or results_retrieved >= max_results:
                    print("Reached end of results or max results limit.")
                    return
                
                params["token"] = next_token
                break  # Exit retry loop on success

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    delay = 2 ** retries
                    print(f"Rate limited. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    retries += 1
                else:
                    print(f"HTTP Error: {e}")
                    return # Exit on other HTTP errors
            except requests.exceptions.RequestException as e:
                print(f"A network error occurred: {e}")
                return # Exit on network errors

        if retries == max_retries:
            print("Max retries reached. Exiting.")
            return

# --------------------------- 
# DATABASE INSERTION
# --------------------------- 

def insert_papers_into_db(conn, papers):
    """Inserts a batch of papers into the database."""
    batch_data = []
    for paper in papers:

        # Skip papers without an abstract or embedding
        if not paper.get("abstract"):
            continue

        metadata = (
            paper.get("paperId"),
            paper.get("title"),
            paper.get("abstract"),
            [author.get("name") for author in paper.get("authors", []) if author],
            paper.get("year"),
            paper.get("url"),
            paper.get("fieldsOfStudy"),
            paper.get("citationCount"),
            paper.get("referenceCount"),
            paper.get("influentialCitationCount")
        )
        batch_data.append(metadata)

    if not batch_data:
        return 0

    with conn.cursor() as cur:
        # Using ON CONFLICT to avoid errors if a paper is already in the database
        execute_values(
            cur,
            """
            INSERT INTO papers (
                paper_id, title, abstract, authors, year, url, fields_of_study, 
                citation_count, reference_count, influential_citation_count
            ) VALUES %s
            ON CONFLICT (paper_id) DO NOTHING;
            """,
            batch_data
        )
        conn.commit()
        print(f"Successfully inserted or updated {len(batch_data)} papers.")
        return len(batch_data)

# --------------------------- 
# MAIN EXECUTION
# --------------------------- 

if __name__ == "__main__":
    db_connection = None
    try:
        db_connection = setup_database()
        total_inserted = 0

        random.shuffle(extra_queries)
        for query in extra_queries:
            print(f"\n{'='*50}")
            print(f"Processing query: '{query}'")
            print(f"{ '='*50}\n")
            
            paper_generator = fetch_papers_from_api(
                query=query,
                fields=REQUEST_FIELDS,
                max_results=MAX_RESULTS_PER_QUERY
            )
            
            for paper_batch in paper_generator:
                inserted_count = insert_papers_into_db(db_connection, paper_batch)
                total_inserted += inserted_count
        
        print(f"\n--- Import Complete ---")
        print(f"Total new papers inserted across all queries: {total_inserted}")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        if db_connection:
            db_connection.close()
            print("Database connection closed.")
