import chromadb
import uuid

# 🔹 Single persistent client
client = chromadb.Client()

COLLECTION_NAME = "pdf_docs"


def get_collection():
    return client.get_or_create_collection(name=COLLECTION_NAME)


def clear_collection():
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass


def store_chunks(chunks, embeddings):
    collection = get_collection()

    ids = [str(uuid.uuid4()) for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )


# ✅ REAL FIX: embedding-based query + safe n_results
def query_vectors(query_embedding, top_k=3):
    collection = get_collection()

    total_docs = collection.count()
    if total_docs == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],   # 🔥 CORRECT
        n_results=min(top_k, total_docs)       # 🔥 VERY IMPORTANT
    )

    return results["documents"][0]
