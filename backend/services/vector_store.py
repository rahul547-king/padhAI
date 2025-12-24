import chromadb
from config import Config

client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory=Config.CHROMA_PATH
    )
)

collection = client.get_or_create_collection("padhai")

def store_chunks(chunks, embeddings):
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            embeddings=[embeddings[i]],
            ids=[f"chunk_{i}"]
        )

def query_vectors(query_embedding, top_k=3):
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
