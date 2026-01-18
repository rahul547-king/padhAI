# routes/flashcard_routes.py
from __future__ import annotations

from flask import Blueprint, request, jsonify

from services.flashcard_generator import generate_and_store_flashcards
from services.firestore_flashcards import list_decks, get_deck, update_progress

DEMO_UID = "demo_user"

try:
    from firebase_admin import auth as fb_auth
except Exception:
    fb_auth = None

flash_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


def _get_uid_from_bearer() -> str:
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


@flash_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    doc_id = (data.get("doc_id") or "").strip()
    if not doc_id:
        return jsonify({"error": "doc_id is required"}), 400

    count = int(data.get("count") or 20)
    mode = (data.get("mode") or "mixed").strip()
    difficulty = (data.get("difficulty") or "Medium").strip()

    uid = _get_uid_from_bearer()

    result = generate_and_store_flashcards(uid, doc_id, count=count, mode=mode, difficulty=difficulty)
    if result.get("error"):
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)


@flash_bp.route("/decks", methods=["GET"])
def decks():
    uid = _get_uid_from_bearer()
    out = list_decks(uid, limit=40)
    return jsonify({"decks": out})


@flash_bp.route("/decks/<deck_id>", methods=["GET"])
def deck(deck_id: str):
    uid = _get_uid_from_bearer()
    d = get_deck(uid, deck_id)
    if not d:
        return jsonify({"error": "Deck not found"}), 404
    return jsonify({"deck": d})


@flash_bp.route("/decks/<deck_id>/progress", methods=["POST"])
def progress(deck_id: str):
    uid = _get_uid_from_bearer()
    data = request.get_json(force=True) or {}

    progress_updates = data.get("progress_updates") or {}
    current_index = data.get("current_index", None)

    # sanitize
    if not isinstance(progress_updates, dict):
        progress_updates = {}

    if current_index is not None:
        try:
            current_index = int(current_index)
        except Exception:
            current_index = None

    update_progress(uid, deck_id, progress_updates=progress_updates, current_index=current_index)
    return jsonify({"ok": True})
