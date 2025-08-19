import requests
from transformers import BertTokenizer, BertModel
import torch
import torch.nn.functional as F
from collections import deque
import time

tokenizer = BertTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = BertModel.from_pretrained("allenai/scibert_scivocab_uncased")

# paper_id = "arXiv:1906.02515"
# url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,abstract,year,citations.paperId"
# resp = requests.get(url)
# data = resp.json()
# print(data)
# year = data.get("year", "")
# citations = data.get("citations", "")
# print(year, citations)
# text = (data.get("title", "") + ". " + data.get("abstract", ""))

# inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
# with torch.no_grad():
#     outputs = model(**inputs)

# search = "quantum physics field theory gauge theory Lie group"
# searchinput = tokenizer(search, return_tensors="pt", truncation=True, max_length=512)
# with torch.no_grad():
#     searchoutputs = model(**searchinput)

# search2 = "biology heart atrium failure tetralogy of fallot"
# searchinput2 = tokenizer(search2, return_tensors="pt", truncation=True, max_length=512)
# with torch.no_grad():
#     searchoutput2 = model(**searchinput2)

# search3 = "turing machine busy beaver number termination"
# searchinput3 = tokenizer(search3, return_tensors="pt", truncation=True, max_length=512)
# with torch.no_grad():
#     searchoutput3 = model(**searchinput3)

# embedding = outputs.pooler_output
# searchembedding = searchoutputs.pooler_output
# searchembedding2 = searchoutput2.pooler_output
# searchembedding3 = searchoutput3.pooler_output

# print(F.cosine_similarity(embedding, searchembedding))
# print(F.cosine_similarity(embedding, searchembedding2))
# print(F.cosine_similarity(embedding, searchembedding3))


def getCitations(id):
    paper_id = id
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=citations.paperId"
    resp = requests.get(url)
    data = resp.json()
    data = data.get("citations", "")
    returned_id = [d["paperId"] for d in data]

    return returned_id

def getBatchCitations(ids):
    resp = requests.post(
    'https://api.semanticscholar.org/graph/v1/paper/batch',
    params={'fields': 'citations'},
    json={"ids": ids}
    )
    data = resp.json()
    returned_id = []
    for paper in data:
        citations = paper.get("citations", [])
        returned_id.extend([c["paperId"] for c in citations])

    return returned_id

FirstID = ['a46da2537c91ff907380599a1c653f0d684b4948']

citations = ['6b0d8f53df50e0872006d20d2d62d5baa9067391', '39f34860dc6cc9d2bfea5d1ef0f0688900ed0363', '56e10b8ab293ee0037b6248f3d8a325b7898385a', '6748f51447c56ba08d277516048f60a6bf7cde73', 'e0f6718e48d0879751134dc7f19a32652821a639']

def getBatchCitations(ids):
    resp = requests.post(
    'https://api.semanticscholar.org/graph/v1/paper/batch',
    params={'fields': 'citations'},
    json={"ids": ids}
    )
    data = resp.json()
    returned_id = []
    for paper in data:
        citations = paper.get("citations", [])
        returned_id.extend([c["paperId"] for c in citations])

    return returned_id

def citationsBFS(start_ids):
    papersQueue = deque()
    papersSet = set()
    for paper in start_ids:
        if paper not in papersSet:
            papersQueue.append(paper)
            papersSet.add(paper)

    for _ in range(0, 3): # limiting to 3 levels for now
        counter = 0
        inputArray = []
        for _ in range(min(100, len(papersQueue))):
            inputArray.append(papersQueue.popleft())
            counter += 1
        return_ids = getBatchCitations(inputArray)

        for paper in return_ids:
            if paper not in papersSet:
                papersQueue.append(paper)
                papersSet.add(paper)
        time.sleep(600) # dpmowts rate limiting

    return list(papersSet)

results = citationsBFS(FirstID)
print(results)