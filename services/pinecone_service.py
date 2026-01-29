import os
from pinecone import Pinecone

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

def query_pinecone(vector, top_k=10):
    return index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True
    )