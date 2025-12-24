from flask import Blueprint, request, jsonify
from services.rag_pipeline import ask_question

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    answer = ask_question(question)
    return jsonify({"answer": answer})
