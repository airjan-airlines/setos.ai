import requests
from transformers import BertTokenizer, BertModel
import torch
import torch.nn.functional as F

tokenizer = BertTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = BertModel.from_pretrained("allenai/scibert_scivocab_uncased")

paper_id = "arXiv:1906.02515"
url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,abstract,year,citations"
resp = requests.get(url)
data = resp.json()
# print(data)
year = data.get("year", "")
citations = data.get("citations", "")
print(year, citations)
text = (data.get("title", "") + ". " + data.get("abstract", ""))

inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)

search = "quantum physics field theory gauge theory Lie group"
searchinput = tokenizer(search, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    searchoutputs = model(**searchinput)

search2 = "biology heart atrium failure tetralogy of fallot"
searchinput2 = tokenizer(search2, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    searchoutput2 = model(**searchinput2)

search3 = "turing machine busy beaver number termination"
searchinput3 = tokenizer(search3, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    searchoutput3 = model(**searchinput3)

embedding = outputs.pooler_output
searchembedding = searchoutputs.pooler_output
searchembedding2 = searchoutput2.pooler_output
searchembedding3 = searchoutput3.pooler_output

print(F.cosine_similarity(embedding, searchembedding))
print(F.cosine_similarity(embedding, searchembedding2))
print(F.cosine_similarity(embedding, searchembedding3))