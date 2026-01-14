import os
import uuid
import chromadb
from config import Config

os.makedirs(Config.CHROMA_PATH, exist_ok=True)
client = chromadb.PersistentClient(path=Config.CHROMA_PATH)

def _collection_name(uid: str) -> str:
    return f"user_{uid}"

def get_collection(uid: str):
    return client.get_or_create_collection(name=_collection_name(uid))

def store_chunks(uid: str, chunks, embeddings, metadatas):
    """
    metadatas must be non-empty dicts for Chroma.
    """
    col = get_collection(uid)
    ids = [str(uuid.uuid4()) for _ in chunks]
    col.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metadatas)

def query_vectors(uid: str, query_embedding, top_k=10, where=None, include_embeddings=True):
    col = get_collection(uid)
    if col.count() == 0:
        return []

    includes = ["documents", "metadatas", "distances"]
    if include_embeddings:
        includes.append("embeddings")

    res = col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, col.count()),
        where=where,
        include=includes
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    embs = res.get("embeddings", [[]])[0] if include_embeddings else [None] * len(docs)

    results = []
    for i in range(len(docs)):
        results.append({
            "text": docs[i],
            "metadata": metas[i] or {},
            "distance": dists[i] if i < len(dists) else None,
            "embedding": embs[i] if i < len(embs) else None
        })
    return results

def clear_user(uid: str):
    name = _collection_name(uid)
    try:
        client.delete_collection(name)
    except Exception:
        pass
