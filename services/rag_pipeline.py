from services.vector_store import query_vectors

def ask_question(question: str) -> str:
    docs = query_vectors(question, top_k=2)

    if not docs:
        return "No relevant information found in the uploaded document."

    return "\n\n".join(docs)
