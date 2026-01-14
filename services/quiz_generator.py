# services/quiz_generator.py
from services.local_embeddings import get_embedding
from services.vector_store import query_vectors
from services.gemini_client import generate_answer


def _docs_to_text(docs):
    """
    Supports both formats:
    - list[str]
    - list[dict] with key 'text'
    """
    if not docs:
        return ""
    if isinstance(docs[0], dict):
        return "\n\n".join(d.get("text", "") for d in docs if d.get("text"))
    return "\n\n".join(docs)


def generate_quiz(uid: str, doc_id: str) -> str:
    if not doc_id:
        return "Please upload and select a PDF first."

    # Better quiz query to retrieve wider coverage
    quiz_query = (
        "Create a quiz from this chapter covering: flags, instruction format, "
        "addressing/memory, interrupts, buses/signals, stack, and timing."
    )
    quiz_embedding = get_embedding(quiz_query)

    # Pull more chunks for better coverage
    docs = query_vectors(uid, quiz_embedding, top_k=18, where={"doc_id": doc_id})
    context = _docs_to_text(docs)

    if not context.strip():
        return "I couldn’t find enough content in the selected PDF to generate a quiz."

    prompt = f"""
You are a strict university exam quiz setter.

IMPORTANT OUTPUT RULES (must follow):
- Output ONLY the questions. Do NOT write any intro line.
- Total = 20 questions exactly.
- Use this structure and numbering:

SECTION A: MCQ (Q1–Q12)
For each MCQ:
Q1) <question>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <A/B/C/D>

SECTION B: True/False (Q13–Q16)
Format:
Q13) <statement>
Answer: True/False

SECTION C: Short Answer (Q17–Q20)
Format:
Q17) <question>
Answer: <2–4 lines>

QUALITY RULES:
- Every MCQ must have 4 complete options (no blanks).
- Avoid repeated questions.
- Questions must be directly based on the content below.
- Use clear, exam-style language.
- If exact info is not present, do NOT invent numbers/specs.

CONTENT:
{context}
""".strip()

    return generate_answer(prompt).strip()
