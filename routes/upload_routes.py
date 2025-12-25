from flask import Blueprint, request, jsonify
from services.pdf_loader import extract_text
from services.text_chunker import chunk_text
from services.vector_store import store_chunks, clear_collection
from services.local_embeddings import get_embedding

# ✅ url_prefix FIXED
upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

@upload_bp.route("/pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    # 🔥 Remove old PDF data
    clear_collection()

    # 📄 Extract text
    text = extract_text(file)

    if not text or not text.strip():
        return jsonify({"error": "No readable text found in PDF"}), 400

    # ✂️ Chunk text
    chunks = chunk_text(text)

    # ⚡ Prevent repetition & slowness
    chunks = chunks[:100]

    # 🧠 Local embeddings
    embeddings = [get_embedding(chunk) for chunk in chunks]

    # 📦 Store vectors
    store_chunks(chunks, embeddings)

    return jsonify({"message": "PDF uploaded & processed successfully"})
