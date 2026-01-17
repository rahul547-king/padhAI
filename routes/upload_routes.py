# routes/upload_routes.py

from __future__ import annotations

from flask import Blueprint, request, jsonify
import uuid
from io import BytesIO
from datetime import datetime, timezone

# Your existing services (keep same behavior)
from services.pdf_loader import extract_pages
from services.text_chunker import chunk_pages
from services.local_embeddings import get_embedding
from services.vector_store import store_chunks

# Optional Firebase Admin verification (only used if token is provided)
try:
    from firebase_admin import auth as fb_auth
except Exception:
    fb_auth = None

# Optional Firebase Storage + Firestore (only used if configured)
try:
    from firebase_init import get_bucket, get_db
except Exception:
    get_bucket = None
    get_db = None

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

DEMO_UID = "demo_user"


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


@upload_bp.route("/pdf", methods=["POST"])
def upload_pdf():
    """
    Backward compatible:
    - Old behavior: works without auth and stores vectors for DEMO_UID
    - New behavior: if token exists, stores per-user + uploads PDF to Firebase Storage + doc metadata in Firestore
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Invalid file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    uid = _get_uid_from_bearer()
    doc_id = str(uuid.uuid4())

    # Read once so we can both upload + extract
    raw = file.read()
    if not raw:
        return jsonify({"error": "Empty PDF file"}), 400

    # -------------------------
    # NEW (optional): Firebase Storage + Firestore
    # If Firebase is not configured, we skip this and keep old behavior.
    # -------------------------
    storage_path = None
    try:
        if get_bucket is not None and get_db is not None:
            # Upload PDF to Firebase Storage
            bucket = get_bucket()
            blob_path = f"users/{uid}/docs/{doc_id}/{file.filename}"
            blob = bucket.blob(blob_path)
            blob.upload_from_string(raw, content_type="application/pdf")
            storage_path = blob_path

            # Save metadata in Firestore
            db = get_db()
            db.collection("users").document(uid).collection("docs").document(doc_id).set({
                "filename": file.filename,
                "storagePath": storage_path,
                "contentType": "application/pdf",
                "createdAt": datetime.now(timezone.utc),
            })
    except Exception:
        # Don’t fail the request—keep old behavior working.
        storage_path = None

    # -------------------------
    # OLD behavior (still): Extract -> chunk -> embed -> store vectors
    # -------------------------
    pages = extract_pages(BytesIO(raw))
    chunks, metas = chunk_pages(pages, chunk_size=500, overlap=60)

    if not chunks:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    # safe cap
    chunks = chunks[:200]
    metas = metas[:200]

    embeddings = [get_embedding(c) for c in chunks]

    # Keep same metadata keys + add doc_id/source/page/chunk_index
    metadatas = []
    for m in metas:
        metadatas.append({
            "doc_id": doc_id,
            "source": file.filename,
            "page": int(m.get("page", 0)),
            "chunk_index": int(m.get("chunk_index", 0)),
        })

    # IMPORTANT: now stores per-user if token exists, else demo_user (old behavior)
    store_chunks(uid, chunks, embeddings, metadatas)

    # Response keeps old fields so frontend stays compatible
    out = {
        "message": "PDF uploaded & processed successfully!",
        "doc_id": doc_id,
        "filename": file.filename,
        "uid_used": uid,  # helpful for debugging
    }

    # Optional extra info for new system
    if storage_path:
        out["storage_path"] = storage_path

    return jsonify(out)
