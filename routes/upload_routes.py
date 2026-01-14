from flask import Blueprint, request, jsonify
import uuid

from services.pdf_loader import extract_pages
from services.text_chunker import chunk_pages
from services.local_embeddings import get_embedding
from services.vector_store import store_chunks

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

DEMO_UID = "demo_user"

@upload_bp.route("/pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    doc_id = str(uuid.uuid4())

    pages = extract_pages(file)
    chunks, metas = chunk_pages(pages, chunk_size=500, overlap=60)

    if not chunks:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    chunks = chunks[:200]  # safe cap
    metas = metas[:200]

    embeddings = [get_embedding(c) for c in chunks]

    # ✅ make metadatas non-empty + include doc_id/source
    metadatas = []
    for m in metas:
        metadatas.append({
            "doc_id": doc_id,
            "source": file.filename,
            "page": int(m.get("page", 0)),
            "chunk_index": int(m.get("chunk_index", 0))
        })

    store_chunks(DEMO_UID, chunks, embeddings, metadatas)

    return jsonify({
        "message": "PDF uploaded & processed successfully!",
        "doc_id": doc_id,
        "filename": file.filename
    })
