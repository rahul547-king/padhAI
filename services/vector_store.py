import chromadb
import uuid

client = chromadb.Client()

def get_collection():
    return client.get_or_create_collection(name="pdf_docs")

def clear_collection():
    try:
        client.delete_collection("pdf_docs")
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

# 🔥 IMPORTANT FIX HERE
def query_vectors(question, top_k=3):
    collection = get_collection()

    results = collection.query(
        query_texts=[question],   # ✅ TEXT BASED QUERY
        n_results=top_k
    )

    return results["documents"][0]
