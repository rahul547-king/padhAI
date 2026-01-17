# services/quiz_generator.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
import time
import json

from services.local_embeddings import get_embedding
from services.vector_store import query_vectors
from services.gemini_client import generate_answer


# -----------------------------------------------------------------------------
# In-memory quiz store (answers hidden from frontend)
# NOTE: This resets when server restarts. For production, store in Firestore/DB.
# -----------------------------------------------------------------------------
_QUIZ_STORE: Dict[str, Dict[str, Any]] = {}


def _now_ts() -> float:
    return time.time()


def _cleanup_old_quizzes(ttl_seconds: int = 60 * 60 * 6) -> None:
    """Remove quizzes older than ttl_seconds (default 6 hours)."""
    cutoff = _now_ts() - ttl_seconds
    to_delete = []
    for qid, payload in list(_QUIZ_STORE.items()):
        created = payload.get("created_at", 0)
        if created < cutoff:
            to_delete.append(qid)
    for qid in to_delete:
        _QUIZ_STORE.pop(qid, None)


def _normalize_query_results(raw) -> List[str]:
    """
    Backward compatible:
    - Old query_vectors returned: list[str]
    - New query_vectors returns: list[{"text","metadata","distance","embedding"}]
    Returns: list[str] (documents only)
    """
    if not raw:
        return []

    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "text" in raw[0]:
        return [r.get("text", "") for r in raw if r.get("text")]

    # assume list[str] or list[any]
    return [str(x) for x in raw if str(x).strip()]


def _build_context(uid: str, doc_id: str, prompt_hint: str, top_k: int = 12) -> str:
    """
    Retrieve chunks ONLY from the selected doc_id, for the provided uid collection.
    """
    emb = get_embedding(prompt_hint)
    where = {"doc_id": doc_id}

    raw = query_vectors(uid, emb, top_k=top_k, where=where)
    docs = _normalize_query_results(raw)

    # Limit context size a bit (helps Gemini and cost)
    docs = [d.strip() for d in docs if d and d.strip()]
    return "\n\n".join(docs[:top_k])


def _extract_json_object(text: str) -> Optional[str]:
    """
    Gemini can return JSON with extra surrounding text.
    This extracts the first {...} JSON object if present.
    """
    t = (text or "").strip()
    if not t:
        return None

    # direct JSON
    if t.startswith("{") and t.endswith("}"):
        return t

    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1 and last > first:
        return t[first:last + 1]
    return None


def _parse_quiz_json(model_text: str) -> Optional[Dict[str, Any]]:
    blob = _extract_json_object(model_text)
    if not blob:
        return None
    try:
        return json.loads(blob)
    except Exception:
        return None


def generate_quiz(uid: str, doc_id: str, num_questions: int = 20, difficulty: str = "Medium") -> Dict[str, Any]:
    """
    Backward compatible return:
      {
        "quiz_id": "...",
        "quiz": {
          "title": ...,
          "difficulty": ...,
          "estimated_time_minutes": ...,
          "questions": [{id,type,question,options?}]  # NO answers
        }
      }
    """
    _cleanup_old_quizzes()

    # Context from the selected PDF only
    context = _build_context(uid, doc_id, prompt_hint="Generate an exam practice quiz", top_k=16)

    if not context.strip():
        return {
            "quiz_id": None,
            "quiz": None,
            "error": "Not enough content found in this PDF to generate a quiz."
        }

    # Keep schema exactly same as before (so frontend stays compatible)
    prompt = f"""
You are an exam-focused quiz generator for university students.

STRICT RULES:
- Output MUST be valid JSON only (no markdown, no extra text).
- Generate exactly {num_questions} questions.
- Mix types:
  - 70% MCQ (4 options)
  - 20% True/False
  - 10% Short answer
- Keep questions based ONLY on the given context.
- Difficulty: {difficulty}
- Provide short explanations (1–2 lines) for each answer.

JSON schema:
{{
  "title": "string",
  "difficulty": "Easy|Medium|Hard",
  "estimated_time_minutes": number,
  "questions": [
    {{
      "id": number,
      "type": "mcq|tf|short",
      "question": "string",
      "options": ["A", "B", "C", "D"],   // only for mcq
      "answer": "A|B|C|D|True|False|string",  // correct answer
      "explanation": "string"
    }}
  ]
}}

Context:
{context}
""".strip()

    model_out = generate_answer(prompt)
    parsed = _parse_quiz_json(model_out)

    if not parsed or "questions" not in parsed:
        return {
            "quiz_id": None,
            "quiz": None,
            "error": "Quiz generation failed. Try again."
        }

    questions = parsed.get("questions", [])
    normalized: List[Dict[str, Any]] = []
    answers_private: List[Dict[str, Any]] = []

    qid_counter = 1

    for q in questions:
        if not isinstance(q, dict):
            continue

        qtype = (q.get("type") or "").strip().lower()
        question_text = (q.get("question") or "").strip()
        explanation = (q.get("explanation") or "").strip()
        answer = q.get("answer")

        if not question_text or not qtype:
            continue

        if qtype == "mcq":
            opts = q.get("options") or []
            if not isinstance(opts, list) or len(opts) != 4:
                continue

            if isinstance(answer, str):
                ans = answer.strip().upper()
            else:
                continue

            if ans not in ["A", "B", "C", "D"]:
                continue

            normalized.append({
                "id": qid_counter,
                "type": "mcq",
                "question": question_text,
                "options": [str(o) for o in opts],
            })

            answers_private.append({
                "id": qid_counter,
                "type": "mcq",
                "correct": ans,
                "explanation": explanation,
            })

        elif qtype in ["tf", "truefalse", "true/false"]:
            if isinstance(answer, str):
                ans = answer.strip().lower()
            else:
                continue

            if ans in ["true", "t"]:
                correct = "True"
            elif ans in ["false", "f"]:
                correct = "False"
            else:
                continue

            normalized.append({
                "id": qid_counter,
                "type": "tf",
                "question": question_text,
                "options": ["True", "False"],
            })

            answers_private.append({
                "id": qid_counter,
                "type": "tf",
                "correct": correct,
                "explanation": explanation,
            })

        elif qtype == "short":
            if not isinstance(answer, str) or not answer.strip():
                continue

            normalized.append({
                "id": qid_counter,
                "type": "short",
                "question": question_text,
            })

            answers_private.append({
                "id": qid_counter,
                "type": "short",
                "correct": answer.strip(),
                "explanation": explanation,
            })

        else:
            continue

        qid_counter += 1
        if len(normalized) >= num_questions:
            break

    # Same safety check as before
    if len(normalized) < 5:
        return {
            "quiz_id": None,
            "quiz": None,
            "error": "Not enough valid questions were generated. Try again."
        }

    quiz_id = str(uuid.uuid4())

    quiz_public = {
        "title": parsed.get("title") or "Practice Quiz",
        "difficulty": parsed.get("difficulty") or difficulty,
        "estimated_time_minutes": parsed.get("estimated_time_minutes") or max(10, int(num_questions * 1.5)),
        "questions": normalized,
    }

    _QUIZ_STORE[quiz_id] = {
        "created_at": _now_ts(),
        "uid": uid,
        "doc_id": doc_id,
        "public": quiz_public,
        "answers": answers_private,
    }

    return {"quiz_id": quiz_id, "quiz": quiz_public}


def grade_quiz(uid: str, quiz_id: str, user_answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward compatible:
    user_answers format:
      { "1":"B", "2":"True", "3":"some text" }

    Returns score + per-question review (same shape as before).
    """
    _cleanup_old_quizzes()

    stored = _QUIZ_STORE.get(quiz_id)
    if not stored:
        return {"error": "Quiz not found or expired."}

    if stored.get("uid") != uid:
        return {"error": "Unauthorized quiz access."}

    answers_private = stored.get("answers", [])
    public = stored.get("public", {})
    questions_public = public.get("questions", [])

    total = len(answers_private)
    correct_count = 0
    review: List[Dict[str, Any]] = []

    pub_map = {q["id"]: q for q in questions_public if isinstance(q, dict) and "id" in q}

    for a in answers_private:
        qid = a["id"]
        qtype = a["type"]
        correct = a["correct"]
        explanation = a.get("explanation") or ""

        given = user_answers.get(str(qid))
        is_correct = False

        if qtype in ["mcq", "tf"]:
            if isinstance(given, str):
                is_correct = (given.strip().upper() == str(correct).strip().upper())

        elif qtype == "short":
            if isinstance(given, str):
                gv = given.strip().lower()
                cv = str(correct).strip().lower()
                is_correct = (gv == cv) or (cv in gv) or (gv in cv)

        if is_correct:
            correct_count += 1

        pub_q = pub_map.get(qid, {"id": qid, "question": ""})
        review.append({
            "id": qid,
            "type": qtype,
            "question": pub_q.get("question", ""),
            "options": pub_q.get("options"),
            "your_answer": given,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": explanation,
        })

    score_percent = round((correct_count / max(1, total)) * 100, 2)

    return {
        "quiz_id": quiz_id,
        "title": public.get("title"),
        "difficulty": public.get("difficulty"),
        "total_questions": total,
        "correct": correct_count,
        "incorrect": total - correct_count,
        "score_percent": score_percent,
        "review": review,
    }
