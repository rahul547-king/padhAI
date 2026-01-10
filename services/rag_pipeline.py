from services.local_embeddings import get_embedding
from services.vector_store import query_vectors
from services.gemini_client import generate_answer
import re

def ask_question(question: str) -> str:
    # 1️⃣ Embed question
    query_embedding = get_embedding(question)

    # 2️⃣ Retrieve MORE relevant chunks
    docs = query_vectors(query_embedding, top_k=4)

    if not docs:
        return "Answer not found in the document."

    # 3️⃣ Combine context properly
    context = "\n\n".join(docs)

    # 4️⃣ STRONG PROMPT (🔥 THIS IS THE KEY)
    prompt = f"""
You are an AI study assistant.

Answer the question ONLY using the given document context.
Give a clear, medium-length explanation (5–8 lines).
If it is a definition, explain it properly.
If it is a purpose/objective question, give points.

Document Context:
{context}

Question:
{question}

Rules:
- Do NOT say "Answer not found" unless context is totally missing
- Do NOT give one-line answers
- Explain like a university exam answer
"""

    # 5️⃣ Gemini generates final answer
    answer = generate_answer(prompt)

    return answer.strip()
