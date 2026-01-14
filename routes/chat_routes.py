from flask import Blueprint, request, jsonify
from services.chat_history import create_new_chat, add_message, load_history, get_chat
from services.rag_pipeline import ask_question
from services.quiz_generator import generate_quiz   # ✅ NEW

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

DEMO_UID = "demo_user"

@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    chat_id = data.get("chat_id")
    doc_id = data.get("doc_id")  # ✅ REQUIRED

    if not question:
        return jsonify({"error": "question is required"}), 400

    # ✅ create chat if needed
    if not chat_id:
        chat = create_new_chat(question)
        chat_id = chat["id"]
    else:
        add_message(chat_id, "user", question)

    # ✅ PASS doc_id (prevents mixing PDFs)
    answer = ask_question(DEMO_UID, question, doc_id)

    # ✅ store assistant message
    add_message(chat_id, "assistant", answer)

    return jsonify({"answer": answer, "chat_id": chat_id})


# ✅ NEW: Quiz endpoint
@chat_bp.route("/quiz", methods=["POST"])
def quiz():
    data = request.get_json(force=True)
    doc_id = data.get("doc_id")

    if not doc_id:
        return jsonify({"error": "doc_id is required"}), 400

    quiz_text = generate_quiz(DEMO_UID, doc_id)
    return jsonify({"quiz": quiz_text})


@chat_bp.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())


@chat_bp.route("/<chat_id>", methods=["GET"])
def load_chat(chat_id):
    chat = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chat)
