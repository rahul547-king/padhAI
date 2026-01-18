# services/flashcard_generator.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import json

from services.vector_store import query_vectors
from services.local_embeddings import get_embedding
from services.gemini_client import generate_answer

from services.firestore_flashcards import create_deck


def _extract_json_object(text: str) -> Optional[str]:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("{") and t.endswith("}"):
        return t
    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1 and last > first:
        return t[first:last + 1]
    return None


def _parse_json(model_text: str) -> Optional[Dict[str, Any]]:
    blob = _extract_json_object(model_text)
    if not blob:
        return None
    try:
        return json.loads(blob)
    except Exception:
        return None


def _normalize_query_results(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        return [r.get("text", "") for r in raw if r.get("text")]
    return [str(x) for x in raw if str(x).strip()]


def _build_context(uid: str, doc_id: str, hint: str, top_k: int = 16) -> str:
    emb = get_embedding(hint)
    raw = query_vectors(uid, emb, top_k=top_k, where={"doc_id": doc_id})
    docs = [d.strip() for d in _normalize_query_results(raw) if d and d.strip()]
    return "\n\n".join(docs[:top_k])


def generate_and_store_flashcards(
    uid: str,
    doc_id: str,
    count: int = 20,
    mode: str = "mixed",        # definitions|qa|cloze|mixed
    difficulty: str = "Medium", # Easy|Medium|Hard
) -> Dict[str, Any]:
    count = max(5, min(int(count or 20), 60))
    mode = (mode or "mixed").strip().lower()
    if mode not in ["definitions", "qa", "cloze", "mixed"]:
        mode = "mixed"

    difficulty = (difficulty or "Medium").strip()
    if difficulty not in ["Easy", "Medium", "Hard"]:
        difficulty = "Medium"

    context = _build_context(uid, doc_id, hint="Create exam-focused flashcards from notes", top_k=18)
    if not context.strip():
        return {"deck_id": None, "deck": None, "error": "Not enough content found in this PDF to generate flashcards."}

    prompt = f"""
You are a university flashcard generator.

STRICT RULES:
- Output MUST be valid JSON only (no markdown, no extra text).
- Create exactly {count} flashcards.
- Use ONLY the given context.
- Difficulty: {difficulty}
- Mode: {mode}

Mode rules:
- definitions: front = term/concept, back = definition + key points
- qa: front = question, back = answer (short, correct)
- cloze: front = fill-in-the-blank statement, back = missing phrase + explanation
- mixed: mixture of the above

JSON schema:
{{
  "title": "string",
  "mode": "definitions|qa|cloze|mixed",
  "difficulty": "Easy|Medium|Hard",
  "cards": [
    {{
      "id": number,
      "front": "string",
      "back": "string",
      "tag": "string"
    }}
  ]
}}

Context:
{context}
""".strip()

    model_out = generate_answer(prompt)
    parsed = _parse_json(model_out)

    if not parsed or "cards" not in parsed:
        return {"deck_id": None, "deck": None, "error": "Flashcard generation failed. Try again."}

    cards_in = parsed.get("cards", [])
    cards: List[Dict[str, Any]] = []
    cid = 1
    for c in cards_in:
        if not isinstance(c, dict):
            continue
        front = (c.get("front") or "").strip()
        back = (c.get("back") or "").strip()
        tag = (c.get("tag") or "").strip() or "General"
        if not front or not back:
            continue
        cards.append({"id": cid, "front": front, "back": back, "tag": tag})
        cid += 1
        if len(cards) >= count:
            break

    if len(cards) < 5:
        return {"deck_id": None, "deck": None, "error": "Not enough valid flashcards were generated. Try again."}

    deck = {
        "title": parsed.get("title") or "Flashcards",
        "mode": parsed.get("mode") or mode,
        "difficulty": parsed.get("difficulty") or difficulty,
        "count": len(cards),
        "cards": cards,
    }

    # ✅ Store in Firestore
    deck_id = create_deck(uid, doc_id, deck)

    return {"deck_id": deck_id, "deck": deck}
