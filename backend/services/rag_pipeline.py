from services.gemini_client import get_embedding, generate_answer
from services.vector_store import query_vectors

def ask_question(question):
    query_embedding = get_embedding(question)
    results = query_vectors(query_embedding)

    context_docs = results["documents"][0]
    context = "\n".join(context_docs)

    prompt = f"""
Use the following context to answer the question.
If the answer is not in the context, say you don't know.

Context:
{context}

Question:
{question}
"""

    return generate_answer(prompt)
