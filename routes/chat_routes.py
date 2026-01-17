# routes/chat_routes.py
from __future__ import annotations

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone

# -------- OLD (local JSON chat history) ----------
from services.chat_history import (
    create_new_chat as json_create_new_chat,
    add_message as json_add_message,
    load_history as json_load_history,
    get_chat as json_get_chat,
)

# -------- Core logic ----------
from services.rag_pipeline import ask_question
from services.quiz_generator import generate_quiz, grade_quiz

chat_bp = Blueprint("chat", __name__)

DEMO_UID = "demo_user"


# -------- Optional: Firebase token verify (only if token exists) ----------
try:
    from firebase_admin import auth as fb_auth
except Exception:
    fb_auth = None

# -------- Optional: Firestore chat (only if available/configured) ----------
try:
    from services.firestore_chat import (
        create_chat as fs_create_chat,
        add_message as fs_add_message,
        list_chats as fs_list_chats,
        get_chat as fs_get_chat,
    )
except Exception:
    fs_create_chat = None
    fs_add_message = None
    fs_list_chats = None
    fs_get_chat = None

# -------- Optional: Firestore client for saving quiz attempts ----------
try:
    from firebase_init import get_db
except Exception:
    get_db = None


def _get_uid_from_bearer() -> str:
    """
    Backward-compatible UID getter:
    - If Authorization: Bearer <token> is present and valid -> returns real uid
    - Otherwise -> returns DEMO_UID
    """
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return DEMO_UID

    token = header.replace("Bearer ", "").strip()
    if not token or fb_auth is None:
        return DEMO_UID

    try:
        decoded = fb_auth.verify_id_token(token)
        return decoded.get("uid") or DEMO_UID
    except Exception:
        return DEMO_UID


def _use_firestore(uid: str) -> bool:
    """
    Decide whether to store chats in Firestore:
    - Must be a real user (not demo)
    - Firestore chat functions must exist
    """
    return (
        uid != DEMO_UID
        and fs_create_chat is not None
        and fs_add_message is not None
        and fs_list_chats is not None
        and fs_get_chat is not None
    )


def _title_from_question(q: str) -> str:
    q = (q or "").strip().rstrip("?")
    words = q.split()
    return (" ".join(words[:6]) or "Conversation").capitalize()


# ✅ OPTIONAL (Quick): serve the quiz dashboard page from this blueprint
# Open it at: /chat/dashboard
@chat_bp.route("/dashboard", methods=["GET"])
def quiz_dashboard():
    return render_template("quiz_dashboard.html")


@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    chat_id = data.get("chat_id")
    doc_id = data.get("doc_id")  # required to prevent mixing PDFs

    if not question:
        return jsonify({"error": "question is required"}), 400

    uid = _get_uid_from_bearer()
    firestore_mode = _use_firestore(uid)

    # Require doc_id for correct PDF-scoped RAG (same as your current logic)
    if not doc_id:
        return jsonify({"error": "doc_id is required"}), 400

    # -------------------------
    # Create / update chat (Firestore if logged in, else JSON)
    # -------------------------
    if firestore_mode:
        if not chat_id:
            chat_id = fs_create_chat(uid, _title_from_question(question), active_doc_id=doc_id)
        fs_add_message(uid, chat_id, "user", question)
    else:
        if not chat_id:
            chat = json_create_new_chat(question)
            chat_id = chat["id"]
        else:
            json_add_message(chat_id, "user", question)

    # -------------------------
    # RAG answer (per-user if logged in else demo_user)
    # -------------------------
    answer = ask_question(uid, question, doc_id)

    # Store assistant message
    if firestore_mode:
        fs_add_message(uid, chat_id, "assistant", answer)
    else:
        json_add_message(chat_id, "assistant", answer)

    # Keep response same as before
    return jsonify({"answer": answer, "chat_id": chat_id})


@chat_bp.route("/quiz", methods=["POST"])
def quiz():
    """
    Returns:
      {
        "quiz_id": "...",
        "quiz": {
           "title": ...,
           "difficulty": ...,
           "estimated_time_minutes": ...,
           "questions": [
              { id, type, question, options? }  // NO answers
           ]
        }
      }
    """
    data = request.get_json(force=True)
    doc_id = data.get("doc_id")
    num_questions = int(data.get("num_questions") or 20)
    difficulty = (data.get("difficulty") or "Medium").strip()

    if not doc_id:
        return jsonify({"error": "doc_id is required"}), 400

    uid = _get_uid_from_bearer()

    # Generate quiz scoped to user/doc (works in demo mode too)
    result = generate_quiz(uid, doc_id, num_questions=num_questions, difficulty=difficulty)

    if result.get("error"):
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)


@chat_bp.route("/quiz/submit", methods=["POST"])
def quiz_submit():
    """
    Request:
      { "quiz_id": "...", "answers": { "1":"B", "2":"True", "3":"..." } }

    Response:
      score summary + review including correct answers + explanations
    """
    data = request.get_json(force=True)
    quiz_id = data.get("quiz_id")
    answers = data.get("answers") or {}

    if not quiz_id:
        return jsonify({"error": "quiz_id is required"}), 400

    if not isinstance(answers, dict):
        return jsonify({"error": "answers must be an object/dict"}), 400

    uid = _get_uid_from_bearer()

    result = grade_quiz(uid, quiz_id, answers)

    if result.get("error"):
        return jsonify({"error": result["error"]}), 400

    # Optional: Save quiz attempt if Firestore is available and user is logged in
    if uid != DEMO_UID and get_db is not None:
        try:
            db = get_db()
            db.collection("users").document(uid).collection("quizAttempts").document().set({
                "quizId": quiz_id,
                "title": result.get("title"),
                "difficulty": result.get("difficulty"),
                "scorePercent": result.get("score_percent"),
                "correct": result.get("correct"),
                "incorrect": result.get("incorrect"),
                "total": result.get("total_questions"),
                "createdAt": datetime.now(timezone.utc),
            })
        except Exception:
            pass

    return jsonify(result)


@chat_bp.route("/history", methods=["GET"])
def history():
    """
    Backward compatible:
    - If token valid + firestore available: returns Firestore chat list
    - Else: returns JSON history list (old)
    """
    uid = _get_uid_from_bearer()
    if _use_firestore(uid):
        chats = fs_list_chats(uid, limit=50)
        out = []
        for c in chats:
            d = dict(c)
            # Convert timestamps for JSON response
            for k in ["createdAt", "updatedAt"]:
                if k in d and hasattr(d[k], "isoformat"):
                    d[k] = d[k].isoformat()
            out.append(d)
        return jsonify(out)

    # Old mode
    return jsonify(json_load_history())


@chat_bp.route("/<chat_id>", methods=["GET"])
def load_chat(chat_id):
    """
    Backward compatible:
    - If token valid + firestore available: loads Firestore chat
    - Else: loads JSON chat
    """
    uid = _get_uid_from_bearer()
    if _use_firestore(uid):
        chat = fs_get_chat(uid, chat_id, message_limit=200)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        # Convert timestamps for frontend compatibility
        for k in ["createdAt", "updatedAt"]:
            if k in chat and hasattr(chat[k], "isoformat"):
                chat[k] = chat[k].isoformat()

        msgs = []
        for m in chat.get("messages", []):
            msgs.append({
                "role": m.get("role"),
                "content": m.get("content"),
                "citations": m.get("citations", []),
                "createdAt": m.get("createdAt").isoformat() if hasattr(m.get("createdAt"), "isoformat") else None,
            })
        chat["messages"] = msgs

        return jsonify(chat)

    # Old mode
    chat = json_get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chat)
