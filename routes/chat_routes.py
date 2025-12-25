from flask import Blueprint, request, jsonify
from services.rag_pipeline import ask_question
from services.chat_history import save_message, load_history

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

# 🔹 Ask Question API
@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400

    question = data["question"]

    # Generate answer using RAG
    answer = ask_question(question)

    # ✅ Save chat to history
    save_message(question, answer)

    return jsonify({"answer": answer})


# 🔹 Get Chat History (for sidebar)
@chat_bp.route("/history", methods=["GET"])
def history():
    chats = load_history()
    return jsonify(chats)
