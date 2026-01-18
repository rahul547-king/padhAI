# services/firestore_flashcards.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from firebase_init import get_db


def _now():
    return datetime.now(timezone.utc)


def create_deck(uid: str, doc_id: str, deck: Dict[str, Any]) -> str:
    """
    Stores a flashcard deck under:
      users/{uid}/flashcard_decks/{deck_id}

    Deck doc includes:
      - docId, title, mode, difficulty, count
      - cards: [{id, front, back, tag}]
      - progress: { "1": "Good", "2": "Again", ... }
      - currentIndex
    """
    db = get_db()
    ref = db.collection("users").document(uid).collection("flashcard_decks").document()

    ref.set({
        "docId": doc_id,
        "title": deck.get("title", "Flashcards"),
        "mode": deck.get("mode", "mixed"),
        "difficulty": deck.get("difficulty", "Medium"),
        "count": int(deck.get("count") or len(deck.get("cards", [])) or 0),
        "cards": deck.get("cards", []),
        "progress": {},          # map: cardId -> label
        "currentIndex": 0,
        "createdAt": _now(),
        "updatedAt": _now(),
    })
    return ref.id


def list_decks(uid: str, limit: int = 30) -> List[Dict[str, Any]]:
    db = get_db()
    decks = (
        db.collection("users").document(uid)
        .collection("flashcard_decks")
        .order_by("updatedAt", direction="DESCENDING")
        .limit(limit)
        .stream()
    )

    out: List[Dict[str, Any]] = []
    for d in decks:
        item = d.to_dict()
        item["id"] = d.id
        # DO NOT send full cards list for listing (optional, but better)
        item.pop("cards", None)
        out.append(item)
    return out


def get_deck(uid: str, deck_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    ref = db.collection("users").document(uid).collection("flashcard_decks").document(deck_id)
    snap = ref.get()
    if not snap.exists:
        return None
    data = snap.to_dict()
    data["id"] = deck_id
    return data


def update_progress(
    uid: str,
    deck_id: str,
    progress_updates: Dict[str, str] | None = None,
    current_index: Optional[int] = None,
) -> bool:
    """
    progress_updates example:
      {"1": "Good", "2": "Again"}
    """
    db = get_db()
    ref = db.collection("users").document(uid).collection("flashcard_decks").document(deck_id)

    patch: Dict[str, Any] = {"updatedAt": _now()}

    if current_index is not None:
        patch["currentIndex"] = int(current_index)

    if progress_updates:
        # Firestore merge nested map fields:
        # progress.<cardId> = label
        for k, v in progress_updates.items():
            patch[f"progress.{str(k)}"] = str(v)

    ref.set(patch, merge=True)
    return True
