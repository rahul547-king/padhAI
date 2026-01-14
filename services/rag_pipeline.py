from services.local_embeddings import get_embedding
from services.vector_store import query_vectors
from services.gemini_client import generate_answer
import re
import math


def _detect_question_type(q: str) -> str:
    ql = q.strip().lower()

    if re.search(r"\b(summarize|summary|short note|brief)\b", ql):
        return "summary"

    if re.search(r"^(what is|define|meaning of|explain what is)\b", ql):
        return "definition"

    if re.search(r"\b(components|parts|modules|elements|types|modes|classification|functions|features)\b", ql):
        return "list"

    if re.search(r"\b(advantages|benefits|disadvantages|limitations|compare|difference|vs)\b", ql):
        return "compare"

    if re.search(r"\b(explain|working|how does|procedure|steps|process)\b", ql):
        return "explain"

    return "general"


# -------------------- MMR helpers (diverse retrieval) --------------------

def _cosine(a, b):
    if a is None or b is None:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(min(len(a), len(b))):
        dot += a[i] * b[i]
        na += a[i] * a[i]
        nb += b[i] * b[i]
    if na == 0 or nb == 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def _mmr_select(query_emb, candidates, k=8, lambda_mult=0.7):
    """
    candidates: list of dicts
      {"text": str, "metadata": dict, "distance": float, "embedding": list[float]}
    """
    if not candidates:
        return []

    selected = []
    remaining = candidates[:]

    # First pick: best relevance (smallest distance)
    remaining.sort(key=lambda x: x.get("distance", 999999))
    selected.append(remaining.pop(0))

    while remaining and len(selected) < k:
        best = None
        best_score = -1e18

        for c in remaining:
            rel = -float(c.get("distance", 999999))  # higher is better
            max_sim = 0.0
            for s in selected:
                max_sim = max(max_sim, _cosine(c.get("embedding"), s.get("embedding")))

            score = lambda_mult * rel - (1 - lambda_mult) * max_sim
            if score > best_score:
                best_score = score
                best = c

        selected.append(best)
        remaining.remove(best)

    return selected


def _normalize_query_results(raw):
    """
    Old query_vectors returned: list[str]
    New query_vectors may return: list[{"text","metadata","distance","embedding"}]
    """
    if not raw:
        return []

    if isinstance(raw[0], dict) and "text" in raw[0]:
        return raw

    return [{"text": t, "metadata": {}, "distance": 0.0, "embedding": None} for t in raw]


# -------------------- Main function --------------------

def ask_question(uid: str, question: str, doc_id=None) -> str:
    query_embedding = get_embedding(question)

    # ✅ Prevent mixing: require selected PDF
    if not doc_id:
        return "Please upload and select a PDF first."

    where = {"doc_id": doc_id}

    # ✅ retrieve more candidates
    raw = query_vectors(uid, query_embedding, top_k=15, where=where)
    candidates = _normalize_query_results(raw)

    if not candidates:
        return "I couldn't find relevant information in the selected PDF. Try asking in a different way."

    # ✅ select diverse chunks
    chosen = _mmr_select(query_embedding, candidates, k=8, lambda_mult=0.7)

    # ✅ build context (NO citations / NO tags)
    context = "\n\n".join([item["text"] for item in chosen])

    qtype = _detect_question_type(question)

    # ✅ ChatGPT-like formatting (no citations)
    if qtype == "definition":
        format_rules = """
Write in clean study-notes style (no markdown headings like ###).

Format:
Definition:
<2–3 lines>

Key points:
- 5–7 bullets (each 1 line)

Example:
- 1 short example only if relevant (1 line)
"""
    elif qtype == "list":
        format_rules = """
Write in clean study-notes style.

Format:
Intro:
<1–2 lines>

Points:
- 6–10 bullets (each 1 line)
"""
    elif qtype == "compare":
        format_rules = """
Write in clean study-notes style.

Format:
Intro:
<1–2 lines>

Differences:
- Point 1: A | B
- Point 2: A | B
- Point 3: A | B
- Point 4: A | B
(4–8 points)

Conclusion:
<1–2 lines>
"""
    elif qtype == "summary":
        format_rules = """
Write a syllabus-style summary for exam revision.

STRICT formatting rules:
- Use proper line breaks.
- No markdown headings like ###.
- Do NOT write everything in one paragraph.

Output format:

Title:
<short title>

Key concepts:
- (5 bullets only, <= 12 words each)
- ...
- ...
- ...
- ...
- ...

Types / Classification (only if present):
- (max 3 bullets)
- ...
- ...

Important keywords:
keyword1, keyword2, keyword3, keyword4, keyword5, keyword6, keyword7, keyword8

Other rules:
- Each bullet <= 12 words.
- Max total bullets = 12.
- No extra sections.
"""
    elif qtype == "explain":
        format_rules = """
Write in clean study-notes style.

Format:
Intro:
<2 lines>

Explanation:
<6–10 lines, step-wise if possible>

Key points:
- 4–6 bullets
"""
    else:
        format_rules = """
Write in clean study-notes style.

Format:
Direct answer:
<2–3 lines>

Explanation:
<5–8 lines>

Key points:
- 4–6 bullets
"""

    prompt = f"""
You are a university study assistant.

Rules:
- Answer in a natural ChatGPT-like study style: clean, simple, and structured.
- Do NOT use markdown headings like ### or ####.
- Do NOT mention “document”, “context”, or “AI”.
- Use proper line breaks and spacing. Do not compress into one paragraph.
- Prefer short bullets and exam-friendly language.
- Use the provided context primarily, but if it is incomplete, answer using standard textbook knowledge.

Context:
{context}

Question:
{question}

{format_rules}
""".strip()

    answer = generate_answer(prompt).strip()
    return answer
