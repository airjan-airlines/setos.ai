import os
import requests
from supabase import create_client, Client
import time
from dotenv import load_dotenv

load_dotenv()

# ---- CONFIG ----
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper"
SEMANTIC_SCHOLAR_FIELDS = "citationCount,externalIds"

# ---- INIT SUPABASE ----
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- FETCH PAPERS ----
def fetch_papers():
    response = (
        supabase.table("papers")
        .select("paper_id, pubmed_id")
        .not_.is_("pubmed_id", None)
        .limit(10000)
        .execute()
    )
    return response.data

# ---- GET SINGLE CITATION ----
def get_citation_count(pubmed_id):
    url = f"{SEMANTIC_SCHOLAR_URL}/PMID:{pubmed_id}"
    params = {"fields": SEMANTIC_SCHOLAR_FIELDS}
    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        print(f"⚠️ PMID {pubmed_id} failed: {r.text}")
        return None

    data = r.json()
    return data.get("citationCount", None)

# ---- UPDATE DATABASE ----
def update_citation(pubmed_id, count):
    print(f"Updating PMID {pubmed_id} → {count} citations")
    supabase.table("papers").update({"citation_count": count}).eq("pubmed_id", pubmed_id).execute()

# ---- MAIN ----
def main():
    for i in range (10):
        papers = fetch_papers()
        print(f"Fetched {len(papers)} papers.")
        for i, p in enumerate(papers, start=1):
            pid = p["pubmed_id"]
            count = get_citation_count(pid)
            if count is not None:
                update_citation(pid, count)
            if i % 10 == 0:
                time.sleep(1)
                print(f"Processed {i} papers...")
            time.sleep(0.5)  # avoid rate limit
        print("finished one round cuh")

if __name__ == "__main__":
    main()
