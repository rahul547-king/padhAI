from flask import Blueprint, request, jsonify
from services.pdf_processor import extract_text_from_pdf, chunk_text
from services.vector_store import store_chunks

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_bp.route("/pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    text = extract_text_from_pdf(file)
    chunks = chunk_text(text)

    store_chunks(chunks)

    return jsonify({"message": "PDF processed and stored successfully"})
